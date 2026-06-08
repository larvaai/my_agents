from __future__ import annotations

import asyncio
import tempfile
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


def _normalize_git_args(args: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(args)
    normalized.setdefault("repo_path", str(PROJECT_DIR))
    return normalized


def _server_params(config: MCPServerConfig) -> StdioServerParameters:
    return StdioServerParameters(
        command=config.command,
        args=config.args,
        cwd=str(config.cwd),
        env=config.env,
    )


def _dump_content_block(block: Any) -> dict[str, Any]:
    if hasattr(block, "model_dump"):
        return block.model_dump(mode="json")
    if hasattr(block, "dict"):
        return block.dict()
    return {"type": type(block).__name__, "value": str(block)}


def _dump_result(result: Any, server_name: str, tool_name: str) -> dict[str, Any]:
    content = [_dump_content_block(block) for block in getattr(result, "content", [])]
    text = "\n".join(
        block.get("text", "")
        for block in content
        if block.get("type") == "text"
    )

    structured_content = getattr(result, "structuredContent", None)
    if hasattr(structured_content, "model_dump"):
        structured_content = structured_content.model_dump(mode="json")

    return {
        "ok": not bool(getattr(result, "isError", False)),
        "server": server_name,
        "tool": tool_name,
        "text": text,
        "content": content,
        "structured_content": structured_content,
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


async def _call_mcp_tool(server_name: str, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    if server_name == "filesystem":
        args = _normalize_filesystem_args(tool_name, args)
    elif server_name == "git":
        args = _normalize_git_args(args)

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
        return asyncio.run(_call_mcp_tool(server_name, resolved_tool_name, resolved_args))
    except Exception as exc:
        return {
            "ok": False,
            "tool": tool_name,
            "error": str(exc),
        }


def build_tool_prompt() -> str:
    return f"""
Available MCP tools:

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
- git.git_add: {{"files": ["path/from/repo/root.py"]}}
- git.git_commit: {{"message": "commit message"}}
- git.git_log, git.git_branch, git.git_show, git.git_create_branch, git.git_checkout, git.git_reset

Context7 MCP:
- context7.resolve-library-id: {{"libraryName": "react", "query": "hooks docs"}}
- context7.query-docs: {{"libraryId": "/facebook/react", "query": "useEffect cleanup"}}

Compatibility aliases routed through MCP:
- list_files -> filesystem.list_directory
- read_file -> filesystem.read_file
- write_file -> filesystem.write_file
""".strip()
