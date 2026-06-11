from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from core.runtime_paths import PROJECT_DIR, WORKSPACE_DIR


@dataclass(frozen=True)
class MCPServerConfig:
    command: str
    args: list[str]
    cwd: Path = PROJECT_DIR
    env: dict[str, str] | None = None


def _optional_values(keys: tuple[str, ...]) -> dict[str, str]:
    return {key: value for key in keys if (value := os.getenv(key)) is not None}


def _merged_env(values: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if values:
        env.update(values)
    return env


def _optional_env(keys: tuple[str, ...]) -> dict[str, str] | None:
    values = _optional_values(keys)

    if not values:
        return None

    return _merged_env(values)


def _python_env(keys: tuple[str, ...] = ()) -> dict[str, str]:
    env = _merged_env(_optional_values(keys))
    current_pythonpath = env.get("PYTHONPATH", "")
    pythonpath_parts = [str(PROJECT_DIR)]
    if current_pythonpath:
        pythonpath_parts.append(current_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return env


def _python_module_config(module: str, *extra_args: str, env_keys: tuple[str, ...] = ()) -> MCPServerConfig:
    return MCPServerConfig(
        command=sys.executable,
        args=["-m", module, *extra_args],
        env=_python_env(env_keys),
    )


def _npx_config(package: str, *extra_args: str, env_keys: tuple[str, ...] = ()) -> MCPServerConfig:
    npx_command = os.getenv("NPX_COMMAND", "npx")
    args = ["-y", package, *extra_args]
    env = _optional_env(env_keys)

    if os.name == "nt" and npx_command.lower() in {"npx", "npx.cmd"}:
        return MCPServerConfig(command="cmd", args=["/c", npx_command, *args], env=env)

    return MCPServerConfig(command=npx_command, args=args, env=env)


MCP_SERVERS: dict[str, MCPServerConfig] = {
    "filesystem": _npx_config("@modelcontextprotocol/server-filesystem", str(WORKSPACE_DIR)),
    "git": _python_module_config("mcp_server_git", "--repository", str(PROJECT_DIR)),
    "context7": _npx_config("@upstash/context7-mcp", env_keys=("CONTEXT7_API_KEY",)),
    "python": _python_module_config("mcp_servers.python_sandbox"),
    "file_editor": _python_module_config("mcp_servers.file_editor_server"),
    "terminal": _python_module_config(
        "mcp_servers.terminal_server",
        env_keys=("AGENT_ALLOW_HIGH_RISK_TERMINAL",),
    ),
    "code_index": _python_module_config("mcp_servers.code_index_server"),
    "lint_test": _python_module_config("mcp_servers.lint_test_server"),
    "docker": _python_module_config(
        "mcp_servers.docker_server",
        env_keys=("DOCKER_MCP_ALLOW_MUTATION",),
    ),
    "obsidian": _python_module_config("mcp_servers.obsidian_server", env_keys=("OBSIDIAN_VAULT_DIR",)),
    "issue": _python_module_config("mcp_servers.issue_server", env_keys=("ISSUE_DB_PATH",)),
    "rag": _python_module_config(
        "mcp_servers.rag_server",
        env_keys=(
            "QDRANT_URL",
            "QDRANT_API_KEY",
            "QDRANT_COLLECTION",
            "EMBEDDING_MODEL",
            "RAG_CHUNK_SIZE",
            "RAG_CHUNK_OVERLAP",
        ),
    ),
    "fetch": _python_module_config("mcp_servers.fetch_server"),
    "search": _python_module_config(
        "mcp_servers.search_server",
        env_keys=(
            "SEARCH_PROVIDER",
            "BRAVE_SEARCH_API_KEY",
            "TAVILY_API_KEY",
        ),
    ),
    "document": _python_module_config("mcp_servers.document_server"),
    "pdf_text_extraction": _python_module_config("mcp_servers.pdf_text_extraction_server"),
    "ledger": _python_module_config("mcp_servers.ledger_server", env_keys=("LEDGER_PATH",)),
    "playwright": _python_module_config(
        "mcp_servers.playwright_server",
        env_keys=("PLAYWRIGHT_BROWSERS_PATH",),
    ),
}


MCP_TOOL_NAMES: dict[str, tuple[str, ...]] = {
    "filesystem": (
        "read_file",
        "read_text_file",
        "read_media_file",
        "read_multiple_files",
        "write_file",
        "edit_file",
        "create_directory",
        "list_directory",
        "list_directory_with_sizes",
        "directory_tree",
        "move_file",
        "search_files",
        "get_file_info",
        "list_allowed_directories",
    ),
    "git": (
        "git_status",
        "git_diff_unstaged",
        "git_diff_staged",
        "git_diff",
        "git_commit",
        "git_add",
        "git_reset",
        "git_log",
        "git_create_branch",
        "git_checkout",
        "git_show",
        "git_branch",
    ),
    "context7": (
        "resolve-library-id",
        "query-docs",
    ),
    "python": (
        "run_python",
        "python_probe",
    ),
    "file_editor": (
        "file_editor_view",
        "file_editor_create",
        "file_editor_write_lines",
        "file_editor_str_replace",
        "file_editor_insert",
    ),
    "terminal": (
        "terminal_run",
    ),
    "code_index": (
        "code_index",
        "code_find_symbol",
        "code_find_references",
        "code_dependency_graph",
    ),
    "lint_test": (
        "lint_compile",
        "lint_ruff_check",
        "lint_ruff_format_check",
        "test_python_file",
        "test_smoke_suite",
    ),
    "docker": (
        "docker_health",
        "docker_ps",
        "docker_compose_ps",
        "docker_compose_logs",
        "docker_compose_up",
        "docker_compose_stop",
    ),
    "obsidian": (
        "obsidian_list_notes",
        "obsidian_read_note",
        "obsidian_write_note",
        "obsidian_append_note",
        "obsidian_search_notes",
        "obsidian_create_daily_note",
    ),
    "issue": (
        "issue_create",
        "issue_update",
        "issue_add_comment",
        "issue_list",
        "issue_get",
        "issue_search",
        "issue_stats",
    ),
    "rag": (
        "rag_health",
        "rag_ingest",
        "rag_search",
    ),
    "fetch": (
        "fetch_url",
    ),
    "search": (
        "search_health",
        "web_search",
    ),
    "document": (
        "document_extract_text",
        "document_write_markdown",
        "document_append_section",
        "document_outline",
    ),
    "pdf_text_extraction": (
        "extract_text",
    ),
    "ledger": (
        "ledger_append",
        "ledger_tail",
        "ledger_search",
        "ledger_get",
        "ledger_stats",
    ),
    "playwright": (
        "playwright_health",
        "playwright_get_text",
        "playwright_screenshot",
    ),
}


TOOL_ALIASES: dict[str, tuple[str, str, dict[str, str]]] = {
    "list_files": ("filesystem", "list_directory", {"folder": "path"}),
    "read_file": ("filesystem", "read_file", {}),
    "write_file": ("filesystem", "write_file", {}),
    "run_python": ("python", "run_python", {}),

    "file_editor_view": ("file_editor", "file_editor_view", {}),
    "file_editor_create": ("file_editor", "file_editor_create", {}),
    "file_editor_write_lines": ("file_editor", "file_editor_write_lines", {}),
    "file_editor_str_replace": ("file_editor", "file_editor_str_replace", {}),
    "file_editor_insert": ("file_editor", "file_editor_insert", {}),
    "terminal_run": ("terminal", "terminal_run", {}),

    "code_index": ("code_index", "code_index", {}),
    "find_symbol": ("code_index", "code_find_symbol", {}),
    "find_references": ("code_index", "code_find_references", {}),
    "dependency_graph": ("code_index", "code_dependency_graph", {}),

    "lint_compile": ("lint_test", "lint_compile", {}),
    "lint_ruff_check": ("lint_test", "lint_ruff_check", {}),
    "lint_ruff_format_check": ("lint_test", "lint_ruff_format_check", {}),
    "test_python_file": ("lint_test", "test_python_file", {}),
    "test_smoke_suite": ("lint_test", "test_smoke_suite", {}),

    "docker_health": ("docker", "docker_health", {}),
    "docker_ps": ("docker", "docker_ps", {}),
    "docker_compose_ps": ("docker", "docker_compose_ps", {}),
    "docker_logs": ("docker", "docker_compose_logs", {}),

    "obsidian_list": ("obsidian", "obsidian_list_notes", {}),
    "obsidian_read": ("obsidian", "obsidian_read_note", {}),
    "obsidian_write": ("obsidian", "obsidian_write_note", {}),
    "obsidian_append": ("obsidian", "obsidian_append_note", {}),
    "obsidian_search": ("obsidian", "obsidian_search_notes", {}),

    "issue_create": ("issue", "issue_create", {}),
    "issue_list": ("issue", "issue_list", {}),
    "issue_get": ("issue", "issue_get", {}),
    "issue_search": ("issue", "issue_search", {}),
    "issue_stats": ("issue", "issue_stats", {}),

    "rag_health": ("rag", "rag_health", {}),
    "rag_ingest": ("rag", "rag_ingest", {}),
    "rag_search": ("rag", "rag_search", {}),

    "fetch_url": ("fetch", "fetch_url", {}),
    "search_health": ("search", "search_health", {}),
    "web_search": ("search", "web_search", {}),

    "document_extract_text": ("document", "document_extract_text", {}),
    "document_write_markdown": ("document", "document_write_markdown", {}),
    "document_append_section": ("document", "document_append_section", {}),
    "document_outline": ("document", "document_outline", {}),
    "pdf_extract_text": ("pdf_text_extraction", "extract_text", {}),

    "ledger_append": ("ledger", "ledger_append", {}),
    "ledger_tail": ("ledger", "ledger_tail", {}),
    "ledger_search": ("ledger", "ledger_search", {}),
    "ledger_get": ("ledger", "ledger_get", {}),
    "ledger_stats": ("ledger", "ledger_stats", {}),

    "playwright_health": ("playwright", "playwright_health", {}),
    "playwright_get_text": ("playwright", "playwright_get_text", {}),
    "playwright_screenshot": ("playwright", "playwright_screenshot", {}),
}
