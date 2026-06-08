from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"


@dataclass(frozen=True)
class MCPServerConfig:
    command: str
    args: list[str]
    cwd: Path = PROJECT_DIR
    env: dict[str, str] | None = None


def _context7_env() -> dict[str, str] | None:
    api_key = os.getenv("CONTEXT7_API_KEY")
    if not api_key:
        return None
    return {"CONTEXT7_API_KEY": api_key}


MCP_SERVERS: dict[str, MCPServerConfig] = {
    "filesystem": MCPServerConfig(
        command="cmd",
        args=[
            "/c",
            "npx",
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(WORKSPACE_DIR),
        ],
    ),
    "git": MCPServerConfig(
        command="python",
        args=[
            "-m",
            "mcp_server_git",
            "--repository",
            str(PROJECT_DIR),
        ],
    ),
    "context7": MCPServerConfig(
        command="cmd",
        args=[
            "/c",
            "npx",
            "-y",
            "@upstash/context7-mcp",
        ],
        env=_context7_env(),
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
}


TOOL_ALIASES: dict[str, tuple[str, str, dict[str, str]]] = {
    "list_files": ("filesystem", "list_directory", {"folder": "path"}),
    "read_file": ("filesystem", "read_file", {}),
    "write_file": ("filesystem", "write_file", {}),
}
