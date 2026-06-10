from __future__ import annotations

import asyncio
import tempfile
import json
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from tools.mcp_config import (
    MCP_SERVERS,
    MCP_TOOL_NAMES,
    PROJECT_DIR,
    TOOL_ALIASES,
    WORKSPACE_DIR,
    MCPServerConfig,
)
from tools.tool_policy import check_tool_policy
from tools.tool_schemas import (
    build_tool_protocol_prompt,
    get_tool_metadata,
    validate_tool_args,
)


class MCPToolError(RuntimeError):
    pass


def _resolve_workspace_path(raw_path: str) -> str:
    path = Path(raw_path)
    if not path.is_absolute():
        path = WORKSPACE_DIR / path

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise MCPToolError(f"Path is outside workspace: {raw_path}")

    return str(resolved)


def _normalize_filesystem_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(args)

    for key in ("path", "source", "destination"):
        if key in normalized:
            normalized[key] = _resolve_workspace_path(str(normalized[key]))

    if "paths" in normalized:
        normalized["paths"] = [
            _resolve_workspace_path(str(path))
            for path in normalized["paths"]
        ]

    if tool_name == "list_directory" and "path" not in normalized:
        normalized["path"] = str(WORKSPACE_DIR.resolve())

    return normalized


def _normalize_git_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(args)
    normalized.setdefault("repo_path", str(PROJECT_DIR))

    if tool_name == "git_branch":
        normalized.setdefault("branch_type", "local")

    return normalized


def _server_params(config: MCPServerConfig) -> StdioServerParameters:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    if config.env:
        env.update(config.env)

    return StdioServerParameters(
        command=config.command,
        args=config.args,
        cwd=str(config.cwd),
        env=env,
    )


def _dump_content_block(block: Any) -> dict[str, Any]:
    if hasattr(block, "model_dump"):
        return block.model_dump(mode="json")
    if hasattr(block, "dict"):
        return block.dict()
    return {"type": type(block).__name__, "value": str(block)}


def _try_parse_json_text(text: str) -> dict[str, Any] | None:
    text = text.strip()

    if not text:
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        return parsed

    return None


def _dump_result(result: Any, server_name: str, tool_name: str) -> dict[str, Any]:
    content = [
        _dump_content_block(block)
        for block in getattr(result, "content", [])
    ]

    text = "\n".join(
        block.get("text", "")
        for block in content
        if block.get("type") == "text"
    )

    is_error = bool(getattr(result, "isError", False))

    structured_content = getattr(result, "structuredContent", None)

    if hasattr(structured_content, "model_dump"):
        structured_content = structured_content.model_dump(mode="json")

    payload = None

    if isinstance(structured_content, dict):
        payload = structured_content
    else:
        payload = _try_parse_json_text(text)

    if isinstance(payload, dict):
        merged = dict(payload)

        inner_ok = merged.get("ok")

        if inner_ok is None:
            inner_ok = not is_error

        merged["ok"] = bool(inner_ok) and not is_error
        merged["server"] = server_name
        merged["tool"] = tool_name

        return merged

    return {
        "ok": not is_error,
        "server": server_name,
        "tool": tool_name,
        "text": text,
        "content": content,
    }


def _resolve_tool(tool_name: str, args: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    if tool_name in TOOL_ALIASES:
        server_name, mcp_tool_name, rename_map = TOOL_ALIASES[tool_name]
        mapped_args = {
            rename_map.get(key, key): value
            for key, value in args.items()
        }
        return server_name, mcp_tool_name, mapped_args

    if "." in tool_name:
        server_name, mcp_tool_name = tool_name.split(".", 1)
        if server_name not in MCP_SERVERS:
            raise MCPToolError(f"Unknown MCP server: {server_name}")
        return server_name, mcp_tool_name, args

    matches = [
        server_name
        for server_name, tool_names in MCP_TOOL_NAMES.items()
        if tool_name in tool_names
    ]
    if not matches:
        raise MCPToolError(f"Unknown MCP tool: {tool_name}")
    if len(matches) > 1:
        raise MCPToolError(
            f"Ambiguous MCP tool {tool_name!r}; use server.tool form."
        )

    return matches[0], tool_name, args


def canonicalize_tool_name(tool_name: str) -> str:
    """
    Return the server-qualified tool name after resolving aliases.
    """
    server_name, resolved_tool_name, _ = _resolve_tool(tool_name, {})
    return f"{server_name}.{resolved_tool_name}"


def _all_canonical_tool_names() -> set[str]:
    return {
        f"{server_name}.{tool_name}"
        for server_name, tool_names in MCP_TOOL_NAMES.items()
        for tool_name in tool_names
    }


def expand_tool_patterns(tool_patterns: list[str] | tuple[str, ...] | set[str] | None) -> set[str] | None:
    """
    Expand exact tool names, aliases, and server.* patterns into canonical names.
    """
    if tool_patterns is None:
        return None

    all_tools = _all_canonical_tool_names()
    expanded: set[str] = set()

    for pattern in tool_patterns:
        if pattern == "*":
            expanded.update(all_tools)
            continue

        if pattern.endswith(".*"):
            server_name = pattern[:-2]
            expanded.update(
                tool_name
                for tool_name in all_tools
                if tool_name.startswith(f"{server_name}.")
            )
            continue

        expanded.add(canonicalize_tool_name(pattern))

    return expanded


async def _call_mcp_tool(server_name: str, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    if server_name == "filesystem":
        args = _normalize_filesystem_args(tool_name, args)
    elif server_name == "git":
        args = _normalize_git_args(tool_name, args)

    config = MCP_SERVERS[server_name]
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as stderr_file:
        try:
            async with stdio_client(_server_params(config), errlog=stderr_file) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, args)
                    return _dump_result(result, server_name, tool_name)
        except Exception as exc:
            stderr_file.seek(0)
            stderr = stderr_file.read().strip()
            if stderr:
                raise MCPToolError(f"{exc}\nMCP stderr:\n{stderr}") from exc
            raise


def call_mcp_tool(tool_name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    args = args or {}

    try:
        server_name, resolved_tool_name, resolved_args = _resolve_tool(tool_name, args)
        schema_error = validate_tool_args(server_name, resolved_tool_name, resolved_args)
        metadata = get_tool_metadata(server_name, resolved_tool_name)
        if schema_error:
            return {
                "ok": False,
                "server": server_name,
                "tool": resolved_tool_name,
                "requested_tool": tool_name,
                "schema_error": True,
                "error": schema_error,
                "tool_metadata": metadata,
            }
        policy = check_tool_policy(server_name, resolved_tool_name, resolved_args)
        if not policy.allowed:
            return {
                "ok": False,
                "server": server_name,
                "tool": resolved_tool_name,
                "requested_tool": tool_name,
                "policy_blocked": True,
                "policy_code": policy.code,
                "error": policy.reason,
                "tool_metadata": metadata,
            }
        result = asyncio.run(_call_mcp_tool(server_name, resolved_tool_name, resolved_args))
        result.setdefault("tool_metadata", metadata)
        return result
    except Exception as exc:
        return {
            "ok": False,
            "tool": tool_name,
            "error": str(exc),
        }


TOOL_EXAMPLES: dict[str, str] = {
    "filesystem.list_directory": '- filesystem.list_directory: {"path": "."}',
    "filesystem.read_file": '- filesystem.read_file: {"path": "notes/example.md"}',
    "filesystem.read_text_file": '- filesystem.read_text_file: {"path": "notes/example.md"}',
    "filesystem.read_multiple_files": '- filesystem.read_multiple_files: {"paths": ["notes/a.md", "notes/b.md"]}',
    "filesystem.directory_tree": '- filesystem.directory_tree: {"path": "."}',
    "filesystem.search_files": '- filesystem.search_files: {"path": ".", "pattern": "*.py"}',
    "filesystem.get_file_info": '- filesystem.get_file_info: {"path": "notes/example.md"}',
    "filesystem.list_allowed_directories": '- filesystem.list_allowed_directories: {}',
    "filesystem.create_directory": '- filesystem.create_directory: {"path": "society_sim"}',
    "filesystem.write_file": '- filesystem.write_file: {"path": "society_sim/example.py", "content": "..."}',
    "file_editor.file_editor_view": '- file_editor.file_editor_view: {"path": "code/example.py", "start_line": 1, "max_lines": 200}',
    "file_editor.file_editor_create": '- file_editor.file_editor_create: {"path": "code/example.py", "content": "...", "overwrite": false}',
    "file_editor.file_editor_write_lines": '- file_editor.file_editor_write_lines: {"path": "code/example.py", "lines": ["def main():", "    print(\'OK\')", "", "main()"], "overwrite": true}',
    "file_editor.file_editor_str_replace": '- file_editor.file_editor_str_replace: {"path": "code/example.py", "old_text": "...", "new_text": "...", "expected_replacements": 1}',
    "file_editor.file_editor_insert": '- file_editor.file_editor_insert: {"path": "code/example.py", "line": 10, "content": "..."}',
    "lint_test.test_python_file": '- lint_test.test_python_file: {"path": "workspace/code/project_smoke_test.py", "timeout": 30}',
    "lint_test.lint_compile": '- lint_test.lint_compile: {"path": ".", "timeout": 30}',
    "lint_test.lint_ruff_check": '- lint_test.lint_ruff_check: {"path": ".", "timeout": 30}',
    "lint_test.lint_ruff_format_check": '- lint_test.lint_ruff_format_check: {"path": ".", "timeout": 30}',
    "lint_test.test_smoke_suite": '- lint_test.test_smoke_suite: {"timeout": 60}',
    "python.run_python": '- python.run_python: {"path": "code/test.py", "timeout": 10}',
    "python.python_probe": '- python.python_probe: {"timeout": 10}',
    "terminal.terminal_run": '- terminal.terminal_run: {"argv": ["python", "-m", "py_compile", "main.py"], "timeout": 10, "cwd": ".", "purpose": "validate syntax"}',
    "code_index.code_index": '- code_index.code_index: {"path": ".", "max_files": 300}',
    "code_index.code_find_symbol": '- code_index.code_find_symbol: {"name": "run_orchestrator", "path": ".", "max_results": 20}',
    "code_index.code_find_references": '- code_index.code_find_references: {"name": "run_python", "path": ".", "max_results": 50}',
    "code_index.code_dependency_graph": '- code_index.code_dependency_graph: {"path": "tools", "max_files": 100}',
    "git.git_status": "- git.git_status: {}",
    "git.git_diff_unstaged": "- git.git_diff_unstaged: {}",
    "git.git_diff_staged": "- git.git_diff_staged: {}",
    "git.git_diff": '- git.git_diff: {"target": "HEAD"}',
    "git.git_branch": '- git.git_branch: {"branch_type": "local"}',
    "ledger.ledger_append": '- ledger.ledger_append: {"entry_type": "decision", "title": "...", "data": {}, "tags": []}',
    "ledger.ledger_tail": '- ledger.ledger_tail: {"limit": 20}',
    "ledger.ledger_search": '- ledger.ledger_search: {"text": "threshold", "limit": 20}',
    "issue.issue_create": '- issue.issue_create: {"title": "Bug title", "description": "...", "kind": "bug", "priority": 2}',
    "issue.issue_list": '- issue.issue_list: {"status": "open", "limit": 50}',
    "issue.issue_get": '- issue.issue_get: {"issue_id": 1}',
    "rag.rag_health": "- rag.rag_health: {}",
    "rag.rag_search": '- rag.rag_search: {"query": "question text", "top_k": 5, "score_threshold": 0.80}',
    "fetch.fetch_url": '- fetch.fetch_url: {"url": "https://example.com", "max_chars": 12000, "timeout": 20}',
    "search.web_search": '- search.web_search: {"query": "latest library docs", "limit": 5}',
    "search.search_health": "- search.search_health: {}",
    "document.document_extract_text": '- document.document_extract_text: {"path": "notes/example.md", "max_chars": 20000}',
    "document.document_write_markdown": '- document.document_write_markdown: {"path": "reports/report.md", "title": "Report", "content": "...", "overwrite": false}',
    "document.document_append_section": '- document.document_append_section: {"path": "reports/report.md", "heading": "Findings", "content": "..."}',
    "document.document_outline": '- document.document_outline: {"path": "reports/report.md", "max_items": 100}',
    "playwright.playwright_health": "- playwright.playwright_health: {}",
    "playwright.playwright_get_text": '- playwright.playwright_get_text: {"url": "http://localhost:3000", "selector": "body", "timeout_ms": 30000}',
    "playwright.playwright_screenshot": '- playwright.playwright_screenshot: {"url": "http://localhost:3000", "path": "screenshots/home.png", "full_page": true}',
}


def _build_role_tool_examples(allowed_set: set[str]) -> str:
    examples = [
        TOOL_EXAMPLES[tool_name]
        for tool_name in sorted(allowed_set)
        if tool_name in TOOL_EXAMPLES
    ]
    if not examples:
        return "No extra examples; use the validated schemas above."
    return "\n".join(examples)


def build_tool_prompt(allowed_tools: list[str] | tuple[str, ...] | set[str] | None = None) -> str:
    allowed_set = expand_tool_patterns(allowed_tools)
    role_tool_prompt = ""
    if allowed_set is not None:
        role_tool_prompt = "\n".join(
            [
                "Role tool allowlist:",
                "- This agent may call only the tools listed below.",
                "- If a needed tool is not listed, return final with finish_reason=\"blocker\" and explain the missing permission.",
                *[f"- {tool_name}" for tool_name in sorted(allowed_set)],
                "",
            ]
        )

    if allowed_set is not None:
        return f"""
Available MCP tools:

{role_tool_prompt}
{build_tool_protocol_prompt(allowed_set)}

Role-specific examples for allowed tools only:
{_build_role_tool_examples(allowed_set)}

Important:
- Tools not listed above are not callable by this role, even if the user prompt mentions them.
- For file edits, prefer file_editor tools unless filesystem.create_directory/write_file is explicitly allowed for this role.
""".strip()

    return f"""
Available MCP tools:

{role_tool_prompt}
{build_tool_protocol_prompt(allowed_set)}

Filesystem MCP (sandboxed to {WORKSPACE_DIR}):
- filesystem.list_directory: {{"path": "."}} or {{"path": "notes"}}
- filesystem.read_file: {{"path": "notes/example.md"}}
- filesystem.write_file: {{"path": "code/example.py", "content": "..."}}
- filesystem.edit_file: {{"path": "code/example.py", "edits": [{{"oldText": "...", "newText": "..."}}], "dryRun": false}}
- filesystem.create_directory, filesystem.move_file, filesystem.search_files, filesystem.directory_tree, filesystem.get_file_info

Git MCP (local repo at {PROJECT_DIR}; repo_path is optional because the registry fills it in):
- git.git_status: {{}}
- git.git_diff_unstaged: {{}}
- git.git_diff_staged: {{}}
- git.git_diff: {{"target": "HEAD"}}
- git.git_branch: {{"branch_type": "local"}} or {{"branch_type": "all"}}
- git.git_log, git.git_show
  Mutating Git tools git.git_add, git.git_commit, git.git_reset, git.git_checkout,
  and git.git_create_branch are hard-blocked unless AGENT_ALLOW_GIT_MUTATIONS=1
  is set by the operator for that run.

Context7 MCP:
- context7.resolve-library-id: {{"libraryName": "react", "query": "hooks docs"}}
- context7.query-docs: {{"libraryId": "/facebook/react", "query": "useEffect cleanup"}}

Python MCP (sandboxed to {WORKSPACE_DIR}, executes .py files with timeout):
- python.run_python: {{"path": "code/test.py", "timeout": 10}}
- python.python_probe: {{"timeout": 10}}
  Check whether child Python subprocess can start and exit.

File Editor MCP (sandboxed to {WORKSPACE_DIR}; preferred for file edits):
- file_editor.file_editor_view: {{"path": "code/example.py", "start_line": 1, "max_lines": 200}}
- file_editor.file_editor_create: {{"path": "code/example.py", "content": "...", "overwrite": false}}
- file_editor.file_editor_write_lines: {{"path": "code/example.py", "lines": ["def main():", "    print('OK')", "", "main()"], "overwrite": true}}
- file_editor.file_editor_str_replace: {{"path": "code/example.py", "old_text": "...", "new_text": "...", "expected_replacements": 1}}
- file_editor.file_editor_insert: {{"path": "code/example.py", "line": 10, "content": "..."}}
  Use file_editor for auditable view/create/replace/insert. For write_lines, each item is one physical
  file line and must be delimited by JSON double quotes; use single quotes only inside the code text.
  Never put a whole file in one string with \n escapes. Do not edit files via terminal.

Terminal MCP (project cwd, non-interactive argv only, no shell):
- terminal.terminal_run: {{"argv": ["python", "-m", "py_compile", "main.py"], "timeout": 10, "cwd": ".", "purpose": "validate syntax"}}
  Returns command_metadata.summary and command_metadata.security_risk. Shell strings, cmd/powershell/bash,
  destructive commands, shell control tokens, and git mutations are blocked by default.

Code Index MCP (read-only, project-scoped, excludes heavy dirs):
- code_index.code_index: {{"path": ".", "max_files": 300}}
- code_index.code_find_symbol: {{"name": "run_orchestrator", "path": ".", "max_results": 20}}
- code_index.code_find_references: {{"name": "run_python", "path": ".", "max_results": 50}}
- code_index.code_dependency_graph: {{"path": "tools", "max_files": 100}}
  Prefer Code Index before reading many files manually.

Lint/Test MCP (structured validation, no arbitrary shell):
- lint_test.lint_compile: {{"path": ".", "timeout": 30}}
- lint_test.lint_ruff_check: {{"path": ".", "timeout": 30}}
- lint_test.lint_ruff_format_check: {{"path": ".", "timeout": 30}}
- lint_test.test_python_file: {{"path": "workspace/code/project_smoke_test.py", "timeout": 30}}
- lint_test.test_smoke_suite: {{"timeout": 60}}
  Use Lint/Test MCP as the preferred validation path after code changes.

Docker MCP (restricted Docker helper):
- docker.docker_health: {{"timeout": 20}}
- docker.docker_ps: {{"all": true, "timeout": 20}}
- docker.docker_compose_ps: {{"timeout": 20}}
- docker.docker_compose_logs: {{"service": "qdrant", "tail": 100, "timeout": 30}}
- docker.docker_compose_up: {{"service": "qdrant", "timeout": 120}}
- docker.docker_compose_stop: {{"service": "qdrant", "timeout": 60}}
  Compose up/stop are blocked unless DOCKER_MCP_ALLOW_MUTATION=1. Delete/prune tools are not exposed.

Obsidian MCP (local markdown vault, sandboxed):
- obsidian.obsidian_list_notes: {{"folder": ".", "limit": 100}}
- obsidian.obsidian_read_note: {{"path": "Projects/Test.md", "max_chars": 20000}}
- obsidian.obsidian_write_note: {{"path": "Projects/Test.md", "content": "...", "overwrite": false}}
- obsidian.obsidian_append_note: {{"path": "Projects/Test.md", "content": "\\nMore text"}}
- obsidian.obsidian_search_notes: {{"query": "MCP", "folder": ".", "limit": 20}}
- obsidian.obsidian_create_daily_note: {{"date": "2026-06-10", "content": "# Daily"}}
  Use only for notes/knowledge logging. Do not store secrets.

Issue Tracker MCP (local SQLite task/bug/review/risk tracker):
- issue.issue_create: {{"title": "Bug title", "description": "...", "kind": "bug", "priority": 2, "assignee": "code_agent", "labels": ["bug"], "related_files": []}}
- issue.issue_update: {{"issue_id": 1, "status": "in_progress", "assignee": "code_agent"}}
- issue.issue_add_comment: {{"issue_id": 1, "message": "...", "author": "review_agent"}}
- issue.issue_list: {{"status": "open", "limit": 50}}
- issue.issue_get: {{"issue_id": 1}}
- issue.issue_search: {{"query": "timeout", "limit": 20}}
- issue.issue_stats: {{}}
  Create issues for bugs, review findings, risks, blockers, and multi-agent handoffs.

RAG MCP (sandboxed to {WORKSPACE_DIR}, stores vectors in Qdrant):
- rag.rag_health: {{}}
  Check Qdrant connectivity before RAG ingest/search. If ok is false, stop and classify it as dependency failure.
- rag.rag_ingest: {{"path": "."}} or {{"path": "notes"}}
  Ingest .md, .txt, and .py files from the workspace into Qdrant.
- rag.rag_search: {{"query": "question text", "top_k": 5, "score_threshold": 0.80}}
  Search relevant chunks from the ingested workspace knowledge. Results below score_threshold are removed.

Fetch MCP:
- fetch.fetch_url: {{"url": "https://example.com", "max_chars": 12000, "timeout": 20}}
  Fetch one HTTP/HTTPS page and return readable text, title, final URL, status, and truncation info.
  Use after search.web_search when you need page content or citation-quality source text.

Search MCP:
- search.search_health: {{}}
  Report configured provider. Brave uses BRAVE_SEARCH_API_KEY, Tavily uses TAVILY_API_KEY,
  and DuckDuckGo HTML is a best-effort fallback without an API key.
- search.web_search: {{"query": "latest library docs", "limit": 5}}
  Search the web and return title, URL, and snippet results.

Document MCP (sandboxed to {WORKSPACE_DIR}):
- document.document_extract_text: {{"path": "notes/example.md", "max_chars": 20000}}
  Extract text from md/txt/code/json/csv/html and, when dependencies are installed, pdf/docx.
- document.document_write_markdown: {{"path": "reports/report.md", "title": "Report", "content": "...", "overwrite": false}}
  Create markdown or text documents inside the workspace.
- document.document_append_section: {{"path": "reports/report.md", "heading": "Findings", "content": "..."}}
- document.document_outline: {{"path": "reports/report.md", "max_items": 100}}
  Return headings or a lightweight outline for a document.

Ledger MCP (append-only run memory under {WORKSPACE_DIR} by default):
- ledger.ledger_append: {{"entry_type": "decision", "title": "Chose RAG threshold", "data": {{"threshold": 0.8}}, "tags": ["rag"]}}
- ledger.ledger_tail: {{"limit": 20}}
- ledger.ledger_search: {{"text": "threshold", "entry_type": "decision", "tag": "rag", "limit": 20}}
- ledger.ledger_get: {{"entry_id": "..."}}
- ledger.ledger_stats: {{}}
  Use ledger for durable decisions, audit notes, and run memory when the user asks to preserve context
  or when a task spans multiple sessions.

Playwright MCP:
- playwright.playwright_health: {{}}
  Check whether Python Playwright and browser binaries are available.
- playwright.playwright_get_text: {{"url": "http://localhost:3000", "selector": "body", "timeout_ms": 30000, "max_chars": 12000}}
  Use for local UI or JavaScript-rendered pages when fetch.fetch_url is not enough.
- playwright.playwright_screenshot: {{"url": "http://localhost:3000", "path": "screenshots/home.png", "full_page": true}}
  Save a screenshot inside the workspace. Requires: python -m playwright install chromium.

Compatibility aliases routed through MCP:
- list_files -> filesystem.list_directory
- read_file -> filesystem.read_file
- write_file -> filesystem.write_file
- run_python -> python.run_python
- file_editor_view -> file_editor.file_editor_view
- file_editor_create -> file_editor.file_editor_create
- file_editor_write_lines -> file_editor.file_editor_write_lines
- file_editor_str_replace -> file_editor.file_editor_str_replace
- file_editor_insert -> file_editor.file_editor_insert
- terminal_run -> terminal.terminal_run
- code_index -> code_index.code_index
- find_symbol -> code_index.code_find_symbol
- find_references -> code_index.code_find_references
- dependency_graph -> code_index.code_dependency_graph
- lint_compile -> lint_test.lint_compile
- lint_ruff_check -> lint_test.lint_ruff_check
- lint_ruff_format_check -> lint_test.lint_ruff_format_check
- test_python_file -> lint_test.test_python_file
- test_smoke_suite -> lint_test.test_smoke_suite
- docker_health -> docker.docker_health
- docker_ps -> docker.docker_ps
- docker_compose_ps -> docker.docker_compose_ps
- docker_logs -> docker.docker_compose_logs
- obsidian_list -> obsidian.obsidian_list_notes
- obsidian_read -> obsidian.obsidian_read_note
- obsidian_write -> obsidian.obsidian_write_note
- obsidian_append -> obsidian.obsidian_append_note
- obsidian_search -> obsidian.obsidian_search_notes
- issue_create -> issue.issue_create
- issue_list -> issue.issue_list
- issue_get -> issue.issue_get
- issue_search -> issue.issue_search
- issue_stats -> issue.issue_stats
- rag_health -> rag.rag_health
- rag_ingest -> rag.rag_ingest
- rag_search -> rag.rag_search
- fetch_url -> fetch.fetch_url
- search_health -> search.search_health
- web_search -> search.web_search
- document_extract_text -> document.document_extract_text
- document_write_markdown -> document.document_write_markdown
- document_append_section -> document.document_append_section
- document_outline -> document.document_outline
- ledger_append -> ledger.ledger_append
- ledger_tail -> ledger.ledger_tail
- ledger_search -> ledger.ledger_search
- ledger_get -> ledger.ledger_get
- ledger_stats -> ledger.ledger_stats
- playwright_health -> playwright.playwright_health
- playwright_get_text -> playwright.playwright_get_text
- playwright_screenshot -> playwright.playwright_screenshot
""".strip()
