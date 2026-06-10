from __future__ import annotations

from dataclasses import dataclass
from typing import Any


JSON_TYPE_NAMES = {
    "str": str,
    "int": int,
    "number": (int, float),
    "bool": bool,
    "dict": dict,
    "list": list,
}


@dataclass(frozen=True)
class ArgSpec:
    type_name: str
    required: bool = False
    description: str = ""


@dataclass(frozen=True)
class ToolSchema:
    name: str
    args: dict[str, ArgSpec]
    output: dict[str, str]
    errors: tuple[str, ...]
    metadata: dict[str, Any]
    allow_extra: bool = False


def _schema(
    name: str,
    args: dict[str, tuple[str, bool, str]],
    *,
    output: dict[str, str] | None = None,
    errors: tuple[str, ...] = ("error",),
    metadata: dict[str, Any] | None = None,
    allow_extra: bool = False,
) -> ToolSchema:
    return ToolSchema(
        name=name,
        args={
            key: ArgSpec(type_name=type_name, required=required, description=description)
            for key, (type_name, required, description) in args.items()
        },
        output=output or {"ok": "bool", "server": "str", "tool": "str"},
        errors=errors,
        metadata=metadata or {},
        allow_extra=allow_extra,
    )


TOOL_SCHEMAS: dict[str, ToolSchema] = {
    "filesystem.read_file": _schema(
        "filesystem.read_file",
        {"path": ("str", True, "Workspace file path")},
        output={"ok": "bool", "content": "str"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.read_text_file": _schema(
        "filesystem.read_text_file",
        {
            "path": ("str", True, "Workspace file path"),
            "head": ("int", False, "Optional first N lines"),
            "tail": ("int", False, "Optional last N lines"),
        },
        output={"ok": "bool", "content": "str"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.read_media_file": _schema(
        "filesystem.read_media_file",
        {"path": ("str", True, "Workspace media file path")},
        output={"ok": "bool", "content": "str", "mimeType": "str"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.read_multiple_files": _schema(
        "filesystem.read_multiple_files",
        {"paths": ("list", True, "Workspace file paths")},
        output={"ok": "bool", "content": "list"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.write_file": _schema(
        "filesystem.write_file",
        {
            "path": ("str", True, "Workspace file path"),
            "content": ("str", True, "File content"),
        },
        output={"ok": "bool", "path": "str"},
        metadata={"category": "filesystem", "risk": "medium", "changes_file": True},
    ),
    "filesystem.edit_file": _schema(
        "filesystem.edit_file",
        {
            "path": ("str", True, "Workspace file path"),
            "edits": ("list", True, "List of oldText/newText edits"),
            "dryRun": ("bool", False, "Preview edit without writing"),
        },
        output={"ok": "bool", "path": "str", "diff": "str"},
        metadata={"category": "filesystem", "risk": "medium", "changes_file": True},
    ),
    "filesystem.create_directory": _schema(
        "filesystem.create_directory",
        {"path": ("str", True, "Workspace directory path")},
        output={"ok": "bool", "path": "str"},
        metadata={"category": "filesystem", "risk": "medium", "changes_file": True},
    ),
    "filesystem.list_directory": _schema(
        "filesystem.list_directory",
        {"path": ("str", True, "Workspace directory path")},
        output={"ok": "bool", "entries": "list"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.list_directory_with_sizes": _schema(
        "filesystem.list_directory_with_sizes",
        {
            "path": ("str", True, "Workspace directory path"),
            "sortBy": ("str", False, "Sort field"),
        },
        output={"ok": "bool", "entries": "list"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.directory_tree": _schema(
        "filesystem.directory_tree",
        {"path": ("str", True, "Workspace directory path")},
        output={"ok": "bool", "tree": "dict|list"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.move_file": _schema(
        "filesystem.move_file",
        {
            "source": ("str", True, "Workspace source path"),
            "destination": ("str", True, "Workspace destination path"),
        },
        output={"ok": "bool"},
        metadata={"category": "filesystem", "risk": "medium", "changes_file": True},
    ),
    "filesystem.search_files": _schema(
        "filesystem.search_files",
        {
            "path": ("str", True, "Workspace directory path"),
            "pattern": ("str", True, "Search pattern"),
            "excludePatterns": ("list", False, "Optional exclude patterns"),
        },
        output={"ok": "bool", "matches": "list"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.get_file_info": _schema(
        "filesystem.get_file_info",
        {"path": ("str", True, "Workspace file path")},
        output={"ok": "bool", "metadata": "dict"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "filesystem.list_allowed_directories": _schema(
        "filesystem.list_allowed_directories",
        {},
        output={"ok": "bool", "directories": "list"},
        metadata={"category": "filesystem", "risk": "low", "read_only": True},
    ),
    "git.git_status": _schema(
        "git.git_status",
        {"repo_path": ("str", False, "Repository path")},
        output={"ok": "bool", "status": "str"},
        metadata={"category": "git", "risk": "low", "read_only": True},
    ),
    "git.git_diff_unstaged": _schema(
        "git.git_diff_unstaged",
        {"repo_path": ("str", False, "Repository path")},
        output={"ok": "bool", "diff": "str"},
        metadata={"category": "git", "risk": "low", "read_only": True},
    ),
    "git.git_diff_staged": _schema(
        "git.git_diff_staged",
        {"repo_path": ("str", False, "Repository path")},
        output={"ok": "bool", "diff": "str"},
        metadata={"category": "git", "risk": "low", "read_only": True},
    ),
    "git.git_diff": _schema(
        "git.git_diff",
        {
            "repo_path": ("str", False, "Repository path"),
            "target": ("str", False, "Diff target"),
        },
        output={"ok": "bool", "diff": "str"},
        metadata={"category": "git", "risk": "low", "read_only": True},
    ),
    "git.git_commit": _schema(
        "git.git_commit",
        {
            "repo_path": ("str", False, "Repository path"),
            "message": ("str", True, "Commit message"),
        },
        output={"ok": "bool", "commit": "str"},
        metadata={"category": "git", "risk": "high", "changes_repo": True},
    ),
    "git.git_add": _schema(
        "git.git_add",
        {
            "repo_path": ("str", False, "Repository path"),
            "files": ("list", True, "Files to stage"),
        },
        output={"ok": "bool"},
        metadata={"category": "git", "risk": "high", "changes_repo": True},
    ),
    "git.git_reset": _schema(
        "git.git_reset",
        {"repo_path": ("str", False, "Repository path")},
        output={"ok": "bool"},
        metadata={"category": "git", "risk": "high", "changes_repo": True},
    ),
    "git.git_log": _schema(
        "git.git_log",
        {
            "repo_path": ("str", False, "Repository path"),
            "max_count": ("int", False, "Max commits"),
        },
        output={"ok": "bool", "log": "list"},
        metadata={"category": "git", "risk": "low", "read_only": True},
    ),
    "git.git_create_branch": _schema(
        "git.git_create_branch",
        {
            "repo_path": ("str", False, "Repository path"),
            "branch_name": ("str", True, "Branch name"),
            "base_branch": ("str", False, "Base branch"),
        },
        output={"ok": "bool"},
        metadata={"category": "git", "risk": "high", "changes_repo": True},
    ),
    "git.git_checkout": _schema(
        "git.git_checkout",
        {
            "repo_path": ("str", False, "Repository path"),
            "branch_name": ("str", True, "Branch name"),
        },
        output={"ok": "bool"},
        metadata={"category": "git", "risk": "high", "changes_repo": True},
    ),
    "git.git_show": _schema(
        "git.git_show",
        {
            "repo_path": ("str", False, "Repository path"),
            "revision": ("str", True, "Revision or object to show"),
        },
        output={"ok": "bool", "content": "str"},
        metadata={"category": "git", "risk": "low", "read_only": True},
    ),
    "git.git_branch": _schema(
        "git.git_branch",
        {
            "repo_path": ("str", False, "Repository path"),
            "branch_type": ("str", False, "local, remote, or all"),
        },
        output={"ok": "bool", "branches": "list"},
        metadata={"category": "git", "risk": "low", "read_only": True},
    ),
    "context7.resolve-library-id": _schema(
        "context7.resolve-library-id",
        {
            "libraryName": ("str", True, "Library name"),
            "query": ("str", False, "Optional search query"),
        },
        output={"ok": "bool", "results": "list"},
        metadata={"category": "docs", "risk": "low", "read_only": True},
    ),
    "context7.query-docs": _schema(
        "context7.query-docs",
        {
            "libraryId": ("str", True, "Context7 library id"),
            "query": ("str", True, "Docs query"),
            "tokens": ("int", False, "Optional token budget"),
        },
        output={"ok": "bool", "content": "str"},
        metadata={"category": "docs", "risk": "low", "read_only": True},
    ),
    "python.run_python": _schema(
        "python.run_python",
        {"path": ("str", True, "Workspace .py file path"), "timeout": ("int", False, "1-30 seconds")},
        output={"ok": "bool", "stdout": "str", "stderr": "str", "returncode": "int|null"},
        metadata={"category": "validation", "risk": "medium", "sandbox": "workspace"},
    ),
    "python.python_probe": _schema(
        "python.python_probe",
        {"timeout": ("int", False, "1-30 seconds")},
        output={"ok": "bool", "stdout": "str", "stderr": "str", "python_executable": "str"},
        metadata={"category": "validation", "risk": "low", "sandbox": "workspace"},
    ),
    "terminal.terminal_run": _schema(
        "terminal.terminal_run",
        {
            "argv": ("list", True, "Command argv list; no shell string"),
            "timeout": ("int", False, "1-120 seconds"),
            "cwd": ("str", False, "Project-relative cwd"),
            "purpose": ("str", False, "Short reason for audit log"),
        },
        output={
            "ok": "bool",
            "stdout": "str",
            "stderr": "str",
            "returncode": "int|null",
            "command_metadata": "dict",
        },
        errors=("error", "blocked", "command_metadata"),
        metadata={"category": "terminal", "risk": "dynamic", "shell": False},
    ),
    "code_index.code_index": _schema(
        "code_index.code_index",
        {
            "path": ("str", False, "Project-relative file or folder path"),
            "max_files": ("int", False, "1-1000 files"),
        },
        output={"ok": "bool", "files_count": "int", "symbols": "list", "imports": "list", "errors": "list"},
        metadata={"category": "code_index", "risk": "low", "read_only": True},
    ),
    "code_index.code_find_symbol": _schema(
        "code_index.code_find_symbol",
        {
            "name": ("str", True, "Symbol name or partial name"),
            "path": ("str", False, "Project-relative file or folder path"),
            "max_files": ("int", False, "1-1000 files"),
            "max_results": ("int", False, "1-500 matches"),
        },
        output={"ok": "bool", "matches": "list", "count": "int"},
        metadata={"category": "code_index", "risk": "low", "read_only": True},
    ),
    "code_index.code_find_references": _schema(
        "code_index.code_find_references",
        {
            "name": ("str", True, "Name/text to find"),
            "path": ("str", False, "Project-relative file or folder path"),
            "max_files": ("int", False, "1-1000 files"),
            "max_results": ("int", False, "1-500 references"),
        },
        output={"ok": "bool", "references": "list", "count": "int"},
        metadata={"category": "code_index", "risk": "low", "read_only": True},
    ),
    "code_index.code_dependency_graph": _schema(
        "code_index.code_dependency_graph",
        {
            "path": ("str", False, "Project-relative file or folder path"),
            "max_files": ("int", False, "1-1000 files"),
        },
        output={"ok": "bool", "graph": "dict", "files_count": "int"},
        metadata={"category": "code_index", "risk": "low", "read_only": True},
    ),
    "lint_test.lint_compile": _schema(
        "lint_test.lint_compile",
        {
            "path": ("str", False, "Project-relative file or folder path"),
            "timeout": ("int", False, "1-120 seconds"),
        },
        output={"ok": "bool", "checked_files": "int", "failures": "list", "metadata": "dict"},
        metadata={"category": "validation", "risk": "low", "validation": True},
    ),
    "lint_test.lint_ruff_check": _schema(
        "lint_test.lint_ruff_check",
        {
            "path": ("str", False, "Project-relative file or folder path"),
            "timeout": ("int", False, "1-120 seconds"),
        },
        output={"ok": "bool", "stdout": "str", "stderr": "str", "returncode": "int|null", "metadata": "dict"},
        errors=("error", "dependency_failure"),
        metadata={"category": "validation", "risk": "low", "validation": True},
    ),
    "lint_test.lint_ruff_format_check": _schema(
        "lint_test.lint_ruff_format_check",
        {
            "path": ("str", False, "Project-relative file or folder path"),
            "timeout": ("int", False, "1-120 seconds"),
        },
        output={"ok": "bool", "stdout": "str", "stderr": "str", "returncode": "int|null", "metadata": "dict"},
        errors=("error", "dependency_failure"),
        metadata={"category": "validation", "risk": "low", "validation": True},
    ),
    "lint_test.test_python_file": _schema(
        "lint_test.test_python_file",
        {
            "path": ("str", True, "Project-relative .py file path"),
            "timeout": ("int", False, "1-120 seconds"),
        },
        output={"ok": "bool", "stdout": "str", "stderr": "str", "returncode": "int|null", "metadata": "dict"},
        metadata={"category": "validation", "risk": "medium", "validation": True},
    ),
    "lint_test.test_smoke_suite": _schema(
        "lint_test.test_smoke_suite",
        {"timeout": ("int", False, "1-120 seconds")},
        output={"ok": "bool", "results": "list", "metadata": "dict"},
        metadata={"category": "validation", "risk": "medium", "validation": True},
    ),
    "docker.docker_health": _schema(
        "docker.docker_health",
        {"timeout": ("int", False, "1-180 seconds")},
        output={"ok": "bool", "stdout": "str", "stderr": "str", "command_metadata": "dict"},
        errors=("error", "dependency_failure", "command_metadata"),
        metadata={"category": "docker", "risk": "low", "read_only": True},
    ),
    "docker.docker_ps": _schema(
        "docker.docker_ps",
        {
            "all": ("bool", False, "Include stopped containers"),
            "timeout": ("int", False, "1-180 seconds"),
        },
        output={"ok": "bool", "stdout": "str", "stderr": "str", "command_metadata": "dict"},
        errors=("error", "dependency_failure", "command_metadata"),
        metadata={"category": "docker", "risk": "low", "read_only": True},
    ),
    "docker.docker_compose_ps": _schema(
        "docker.docker_compose_ps",
        {"timeout": ("int", False, "1-180 seconds")},
        output={"ok": "bool", "stdout": "str", "stderr": "str", "command_metadata": "dict"},
        errors=("error", "dependency_failure", "command_metadata"),
        metadata={"category": "docker", "risk": "low", "read_only": True},
    ),
    "docker.docker_compose_logs": _schema(
        "docker.docker_compose_logs",
        {
            "service": ("str", False, "Optional compose service"),
            "tail": ("int", False, "1-1000 lines"),
            "timeout": ("int", False, "1-180 seconds"),
        },
        output={"ok": "bool", "stdout": "str", "stderr": "str", "command_metadata": "dict"},
        errors=("error", "dependency_failure", "command_metadata"),
        metadata={"category": "docker", "risk": "low", "read_only": True},
    ),
    "docker.docker_compose_up": _schema(
        "docker.docker_compose_up",
        {
            "service": ("str", False, "Optional compose service"),
            "timeout": ("int", False, "1-180 seconds"),
        },
        output={"ok": "bool", "stdout": "str", "stderr": "str", "blocked": "bool", "command_metadata": "dict"},
        errors=("error", "blocked", "command_metadata"),
        metadata={"category": "docker", "risk": "medium", "changes_infra": True},
    ),
    "docker.docker_compose_stop": _schema(
        "docker.docker_compose_stop",
        {
            "service": ("str", False, "Optional compose service"),
            "timeout": ("int", False, "1-180 seconds"),
        },
        output={"ok": "bool", "stdout": "str", "stderr": "str", "blocked": "bool", "command_metadata": "dict"},
        errors=("error", "blocked", "command_metadata"),
        metadata={"category": "docker", "risk": "medium", "changes_infra": True},
    ),
    "obsidian.obsidian_list_notes": _schema(
        "obsidian.obsidian_list_notes",
        {
            "folder": ("str", False, "Vault-relative folder"),
            "limit": ("int", False, "1-500 notes"),
        },
        output={"ok": "bool", "notes": "list", "count": "int", "vault": "str"},
        metadata={"category": "knowledge", "risk": "low", "read_only": True},
    ),
    "obsidian.obsidian_read_note": _schema(
        "obsidian.obsidian_read_note",
        {
            "path": ("str", True, "Vault-relative markdown note"),
            "max_chars": ("int", False, "Max chars"),
        },
        output={"ok": "bool", "text": "str", "truncated": "bool"},
        metadata={"category": "knowledge", "risk": "low", "read_only": True},
    ),
    "obsidian.obsidian_write_note": _schema(
        "obsidian.obsidian_write_note",
        {
            "path": ("str", True, "Vault-relative markdown note"),
            "content": ("str", True, "Markdown content"),
            "overwrite": ("bool", False, "Allow overwrite"),
        },
        output={"ok": "bool", "path": "str", "chars_written": "int", "metadata": "dict"},
        metadata={"category": "knowledge", "risk": "low", "changes_file": True},
    ),
    "obsidian.obsidian_append_note": _schema(
        "obsidian.obsidian_append_note",
        {
            "path": ("str", True, "Vault-relative markdown note"),
            "content": ("str", True, "Markdown content"),
        },
        output={"ok": "bool", "path": "str", "chars_appended": "int", "metadata": "dict"},
        metadata={"category": "knowledge", "risk": "low", "changes_file": True},
    ),
    "obsidian.obsidian_search_notes": _schema(
        "obsidian.obsidian_search_notes",
        {
            "query": ("str", True, "Search query"),
            "folder": ("str", False, "Vault-relative folder"),
            "limit": ("int", False, "1-100 matches"),
        },
        output={"ok": "bool", "matches": "list", "count": "int"},
        metadata={"category": "knowledge", "risk": "low", "read_only": True},
    ),
    "obsidian.obsidian_create_daily_note": _schema(
        "obsidian.obsidian_create_daily_note",
        {
            "date": ("str", False, "YYYY-MM-DD; defaults to today"),
            "content": ("str", False, "Markdown content"),
        },
        output={"ok": "bool", "path": "str", "chars_written": "int"},
        metadata={"category": "knowledge", "risk": "low", "changes_file": True},
    ),
    "issue.issue_create": _schema(
        "issue.issue_create",
        {
            "title": ("str", True, "Issue title"),
            "description": ("str", True, "Issue description"),
            "kind": ("str", False, "bug|feature|task|review|risk|question"),
            "priority": ("int", False, "1 highest, 5 lowest"),
            "assignee": ("str", False, "Agent/person name"),
            "labels": ("list", False, "Labels"),
            "related_files": ("list", False, "Project-relative files"),
        },
        output={"ok": "bool", "issue_id": "int", "title": "str"},
        metadata={"category": "issue", "risk": "low", "changes_file": True},
    ),
    "issue.issue_update": _schema(
        "issue.issue_update",
        {
            "issue_id": ("int", True, "Issue id"),
            "status": ("str", False, "open|in_progress|blocked|review|resolved|closed"),
            "assignee": ("str", False, "Agent/person name"),
            "priority": ("int", False, "1 highest, 5 lowest"),
            "labels": ("list", False, "Labels"),
            "related_files": ("list", False, "Project-relative files"),
        },
        output={"ok": "bool", "rows_updated": "int"},
        metadata={"category": "issue", "risk": "low", "changes_file": True},
    ),
    "issue.issue_add_comment": _schema(
        "issue.issue_add_comment",
        {
            "issue_id": ("int", True, "Issue id"),
            "message": ("str", True, "Comment text"),
            "author": ("str", False, "Comment author"),
        },
        output={"ok": "bool", "comment_id": "int"},
        metadata={"category": "issue", "risk": "low", "changes_file": True},
    ),
    "issue.issue_list": _schema(
        "issue.issue_list",
        {
            "status": ("str", False, "Status filter"),
            "kind": ("str", False, "Kind filter"),
            "assignee": ("str", False, "Assignee filter"),
            "limit": ("int", False, "1-200 issues"),
        },
        output={"ok": "bool", "issues": "list", "count": "int"},
        metadata={"category": "issue", "risk": "low", "read_only": True},
    ),
    "issue.issue_get": _schema(
        "issue.issue_get",
        {"issue_id": ("int", True, "Issue id")},
        output={"ok": "bool", "issue": "dict", "comments": "list"},
        metadata={"category": "issue", "risk": "low", "read_only": True},
    ),
    "issue.issue_search": _schema(
        "issue.issue_search",
        {
            "query": ("str", True, "Search text"),
            "limit": ("int", False, "1-200 issues"),
        },
        output={"ok": "bool", "issues": "list", "count": "int"},
        metadata={"category": "issue", "risk": "low", "read_only": True},
    ),
    "issue.issue_stats": _schema(
        "issue.issue_stats",
        {},
        output={"ok": "bool", "count": "int", "by_status": "dict", "by_kind": "dict"},
        metadata={"category": "issue", "risk": "low", "read_only": True},
    ),
    "file_editor.file_editor_view": _schema(
        "file_editor.file_editor_view",
        {
            "path": ("str", True, "Workspace file path"),
            "start_line": ("int", False, "1-based line"),
            "max_lines": ("int", False, "Maximum lines to return"),
        },
        output={"ok": "bool", "lines": "list", "total_lines": "int", "metadata": "dict"},
        metadata={"category": "file_editor", "risk": "low", "changes_file": False},
    ),
    "file_editor.file_editor_create": _schema(
        "file_editor.file_editor_create",
        {
            "path": ("str", True, "Workspace file path"),
            "content": ("str", True, "File content"),
            "overwrite": ("bool", False, "Allow overwrite"),
        },
        output={"ok": "bool", "path": "str", "chars_written": "int", "metadata": "dict"},
        metadata={"category": "file_editor", "risk": "medium", "changes_file": True},
    ),
    "file_editor.file_editor_write_lines": _schema(
        "file_editor.file_editor_write_lines",
        {
            "path": ("str", True, "Workspace file path"),
            "lines": (
                "list",
                True,
                "JSON array of double-quoted file lines; preferred one source line per item, embedded newlines are normalized",
            ),
            "overwrite": ("bool", False, "Allow overwrite"),
            "trailing_newline": ("bool", False, "Append final newline"),
        },
        output={"ok": "bool", "path": "str", "lines_written": "int", "chars_written": "int", "metadata": "dict"},
        metadata={"category": "file_editor", "risk": "medium", "changes_file": True},
    ),
    "file_editor.file_editor_str_replace": _schema(
        "file_editor.file_editor_str_replace",
        {
            "path": ("str", True, "Workspace file path"),
            "old_text": ("str", True, "Exact text to replace"),
            "new_text": ("str", True, "Replacement text"),
            "expected_replacements": ("int", False, "Guard count"),
        },
        output={"ok": "bool", "replacements": "int", "metadata": "dict"},
        metadata={"category": "file_editor", "risk": "medium", "changes_file": True},
    ),
    "file_editor.file_editor_insert": _schema(
        "file_editor.file_editor_insert",
        {
            "path": ("str", True, "Workspace file path"),
            "line": ("int", True, "1-based insertion line"),
            "content": ("str", True, "Text to insert"),
        },
        output={"ok": "bool", "line": "int", "chars_inserted": "int", "metadata": "dict"},
        metadata={"category": "file_editor", "risk": "medium", "changes_file": True},
    ),
    "fetch.fetch_url": _schema(
        "fetch.fetch_url",
        {
            "url": ("str", True, "HTTP/HTTPS URL"),
            "max_chars": ("int", False, "Max readable chars"),
            "timeout": ("int", False, "Seconds"),
            "user_agent": ("str", False, "HTTP User-Agent"),
        },
        output={"ok": "bool", "status": "int", "title": "str", "text": "str", "truncated": "bool"},
        metadata={"category": "research", "risk": "medium", "network": True},
    ),
    "search.search_health": _schema(
        "search.search_health",
        {},
        output={"ok": "bool", "providers": "list"},
        metadata={"category": "research", "risk": "low", "network": False},
    ),
    "search.web_search": _schema(
        "search.web_search",
        {"query": ("str", True, "Search query"), "limit": ("int", False, "1-10 results")},
        output={"ok": "bool", "provider": "str", "results": "list"},
        metadata={"category": "research", "risk": "medium", "network": True},
    ),
    "document.document_extract_text": _schema(
        "document.document_extract_text",
        {"path": ("str", True, "Workspace document path"), "max_chars": ("int", False, "Max chars")},
        output={"ok": "bool", "text": "str", "truncated": "bool"},
        metadata={"category": "document", "risk": "low", "changes_file": False},
    ),
    "document.document_write_markdown": _schema(
        "document.document_write_markdown",
        {
            "path": ("str", True, "Workspace .md/.txt path"),
            "title": ("str", True, "Document title"),
            "content": ("str", True, "Document body"),
            "overwrite": ("bool", False, "Allow overwrite"),
        },
        output={"ok": "bool", "path": "str", "chars": "int"},
        metadata={"category": "document", "risk": "medium", "changes_file": True},
    ),
    "document.document_append_section": _schema(
        "document.document_append_section",
        {
            "path": ("str", True, "Workspace .md/.txt path"),
            "heading": ("str", True, "Section heading"),
            "content": ("str", True, "Section body"),
        },
        output={"ok": "bool", "path": "str", "chars_appended": "int"},
        metadata={"category": "document", "risk": "medium", "changes_file": True},
    ),
    "document.document_outline": _schema(
        "document.document_outline",
        {"path": ("str", True, "Workspace document path"), "max_items": ("int", False, "Max outline items")},
        output={"ok": "bool", "items": "list"},
        metadata={"category": "document", "risk": "low", "changes_file": False},
    ),
    "ledger.ledger_append": _schema(
        "ledger.ledger_append",
        {
            "entry_type": ("str", True, "Entry type"),
            "title": ("str", True, "Entry title"),
            "data": ("dict", False, "Structured payload"),
            "tags": ("list", False, "Tags"),
        },
        output={"ok": "bool", "entry": "dict", "ledger_path": "str"},
        metadata={"category": "ledger", "risk": "low", "changes_file": True},
    ),
    "ledger.ledger_tail": _schema(
        "ledger.ledger_tail",
        {"limit": ("int", False, "Max entries")},
        output={"ok": "bool", "entries": "list"},
        metadata={"category": "ledger", "risk": "low"},
    ),
    "ledger.ledger_search": _schema(
        "ledger.ledger_search",
        {
            "text": ("str", False, "Text filter"),
            "entry_type": ("str", False, "Entry type filter"),
            "tag": ("str", False, "Tag filter"),
            "limit": ("int", False, "Max entries"),
        },
        output={"ok": "bool", "results": "list", "total_matches": "int"},
        metadata={"category": "ledger", "risk": "low"},
    ),
    "ledger.ledger_get": _schema(
        "ledger.ledger_get",
        {"entry_id": ("str", True, "Ledger entry id")},
        output={"ok": "bool", "entry": "dict"},
        metadata={"category": "ledger", "risk": "low"},
    ),
    "ledger.ledger_stats": _schema(
        "ledger.ledger_stats",
        {},
        output={"ok": "bool", "count": "int", "by_type": "dict"},
        metadata={"category": "ledger", "risk": "low"},
    ),
    "playwright.playwright_health": _schema(
        "playwright.playwright_health",
        {},
        output={"ok": "bool", "dependency": "str"},
        metadata={"category": "browser", "risk": "low"},
    ),
    "playwright.playwright_get_text": _schema(
        "playwright.playwright_get_text",
        {
            "url": ("str", True, "HTTP/HTTPS/file URL"),
            "selector": ("str", False, "CSS selector"),
            "timeout_ms": ("int", False, "Timeout milliseconds"),
            "max_chars": ("int", False, "Max text chars"),
        },
        output={"ok": "bool", "title": "str", "text": "str"},
        metadata={"category": "browser", "risk": "medium", "network": True},
    ),
    "playwright.playwright_screenshot": _schema(
        "playwright.playwright_screenshot",
        {
            "url": ("str", True, "HTTP/HTTPS/file URL"),
            "path": ("str", True, "Workspace output image path"),
            "full_page": ("bool", False, "Full page screenshot"),
            "timeout_ms": ("int", False, "Timeout milliseconds"),
        },
        output={"ok": "bool", "path": "str", "title": "str"},
        metadata={"category": "browser", "risk": "medium", "network": True, "changes_file": True},
    ),
    "rag.rag_health": _schema(
        "rag.rag_health",
        {},
        output={"ok": "bool"},
        metadata={"category": "rag", "risk": "low"},
    ),
    "rag.rag_ingest": _schema(
        "rag.rag_ingest",
        {"path": ("str", True, "Workspace file or folder path")},
        output={"ok": "bool", "ingested_chunks": "int"},
        metadata={"category": "rag", "risk": "medium", "changes_index": True},
    ),
    "rag.rag_search": _schema(
        "rag.rag_search",
        {
            "query": ("str", True, "Search query"),
            "top_k": ("int", False, "Max hits"),
            "score_threshold": ("number", False, "Minimum score"),
        },
        output={"ok": "bool", "hits": "list"},
        metadata={"category": "rag", "risk": "low"},
    ),
}


def canonical_tool_name(server_name: str, tool_name: str) -> str:
    return f"{server_name}.{tool_name}"


def get_tool_schema(server_name: str, tool_name: str) -> ToolSchema | None:
    return TOOL_SCHEMAS.get(canonical_tool_name(server_name, tool_name))


def get_tool_metadata(server_name: str, tool_name: str) -> dict[str, Any]:
    schema = get_tool_schema(server_name, tool_name)
    if schema:
        return {
            "schema_version": "1.0",
            "input_schema": {
                key: {
                    "type": spec.type_name,
                    "required": spec.required,
                    "description": spec.description,
                }
                for key, spec in schema.args.items()
            },
            "output_schema": schema.output,
            "errors": list(schema.errors),
            **schema.metadata,
        }
    return {
        "schema_version": "mcp-server",
        "category": server_name,
        "risk": "unknown",
    }


def validate_tool_args(server_name: str, tool_name: str, args: dict[str, Any]) -> str | None:
    schema = get_tool_schema(server_name, tool_name)
    if not schema:
        return None

    for key, spec in schema.args.items():
        if spec.required and key not in args:
            return f"Missing required argument '{key}' for {schema.name}."

    if not schema.allow_extra:
        allowed = set(schema.args)
        extra = sorted(set(args) - allowed)
        if extra:
            return f"Unexpected argument(s) for {schema.name}: {', '.join(extra)}."

    for key, value in args.items():
        spec = schema.args.get(key)
        if not spec:
            continue
        expected = JSON_TYPE_NAMES.get(spec.type_name)
        if expected and value is not None and not isinstance(value, expected):
            return (
                f"Invalid type for {schema.name}.{key}: expected "
                f"{spec.type_name}, got {type(value).__name__}."
            )

    return None


def build_tool_protocol_prompt(allowed_tools: set[str] | None = None) -> str:
    lines = [
        "Tool protocol:",
        "- Tool calls must use server-qualified names: server.tool_name.",
        "- Tool args are validated against registered schemas before execution.",
        "- Tool results always include ok/server/tool and may include tool_metadata.",
        "- Failures return ok=false plus error; policy/schema failures add policy_code or schema_error.",
        "- Terminal commands must use terminal.terminal_run with argv list, never shell strings.",
        "",
        "Validated local tool schemas:",
    ]
    schema_names = sorted(TOOL_SCHEMAS)
    if allowed_tools is not None:
        schema_names = [
            name
            for name in schema_names
            if name in allowed_tools
        ]

    for name in schema_names:
        schema = TOOL_SCHEMAS[name]
        args = ", ".join(
            f"{key}:{spec.type_name}{'*' if spec.required else ''}"
            for key, spec in schema.args.items()
        )
        risk = schema.metadata.get("risk", "unknown")
        category = schema.metadata.get("category", "unknown")
        lines.append(f"- {name}({args}) -> risk={risk}, category={category}")
    return "\n".join(lines)
