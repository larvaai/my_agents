from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"
MAX_VIEW_LINES = 500
MAX_FILE_CHARS = 1_000_000

mcp = FastMCP(
    "file-editor-server",
    instructions=(
        "Auditable file editor for workspace files. Use this for view/create/"
        "str_replace/insert operations instead of terminal commands."
    ),
)


class FileEditorError(ValueError):
    pass


def _safe_workspace_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = WORKSPACE_DIR / path

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise FileEditorError(f"Path is outside workspace: {raw_path}")
    return resolved


def _read_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > MAX_FILE_CHARS:
        raise FileEditorError(f"File too large for file_editor: {len(text)} chars")
    return text


def _rel(path: Path) -> str:
    return str(path.relative_to(WORKSPACE_DIR.resolve()))


@mcp.tool()
def file_editor_view(path: str, start_line: int = 1, max_lines: int = 200) -> dict[str, Any]:
    """
    View a workspace file with line numbers.
    """
    try:
        file_path = _safe_workspace_path(path)
        if not file_path.exists():
            return {"ok": False, "tool": "file_editor_view", "path": path, "error": "File does not exist."}
        if not file_path.is_file():
            return {"ok": False, "tool": "file_editor_view", "path": path, "error": "Path is not a file."}

        lines = _read_text(file_path).splitlines()
        start_line = max(1, int(start_line))
        max_lines = max(1, min(int(max_lines), MAX_VIEW_LINES))
        start_index = start_line - 1
        selected = lines[start_index:start_index + max_lines]
        numbered = [
            {"line": start_index + index + 1, "text": line}
            for index, line in enumerate(selected)
        ]
        return {
            "ok": True,
            "tool": "file_editor_view",
            "path": _rel(file_path),
            "start_line": start_line,
            "max_lines": max_lines,
            "total_lines": len(lines),
            "lines": numbered,
            "has_more": start_index + len(selected) < len(lines),
            "metadata": {
                "operation": "view",
                "auditable": True,
                "changed": False,
            },
        }
    except Exception as exc:
        return {"ok": False, "tool": "file_editor_view", "path": path, "error": str(exc)}


@mcp.tool()
def file_editor_create(path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    """
    Create or overwrite a workspace file.
    """
    try:
        file_path = _safe_workspace_path(path)
        existed = file_path.exists()
        if existed and not overwrite:
            return {
                "ok": False,
                "tool": "file_editor_create",
                "path": path,
                "error": "File exists and overwrite is false.",
            }
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "tool": "file_editor_create",
            "path": _rel(file_path),
            "chars_written": len(content),
                "metadata": {
                "operation": "overwrite" if existed else "create",
                "auditable": True,
                "changed": True,
            },
        }
    except Exception as exc:
        return {"ok": False, "tool": "file_editor_create", "path": path, "error": str(exc)}


@mcp.tool()
def file_editor_write_lines(
    path: str,
    lines: list[str],
    overwrite: bool = False,
    trailing_newline: bool = True,
) -> dict[str, Any]:
    """
    Create or overwrite a workspace file from a JSON list of lines.

    This avoids fragile large multiline JSON string payloads for generated code.
    Each item should be one logical line without a trailing newline.
    """
    try:
        file_path = _safe_workspace_path(path)
        existed = file_path.exists()
        if existed and not overwrite:
            return {
                "ok": False,
                "tool": "file_editor_write_lines",
                "path": path,
                "error": "File exists and overwrite is false.",
            }
        if not isinstance(lines, list):
            return {
                "ok": False,
                "tool": "file_editor_write_lines",
                "path": path,
                "error": "lines must be a list of strings.",
            }

        normalized_lines: list[str] = []
        for line in lines:
            if not isinstance(line, str):
                return {
                    "ok": False,
                    "tool": "file_editor_write_lines",
                    "path": path,
                    "error": "Every item in lines must be a string.",
                }
            normalized_lines.extend(line.splitlines() or [""])

        content = "\n".join(normalized_lines)
        if trailing_newline:
            content += "\n"

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "tool": "file_editor_write_lines",
            "path": _rel(file_path),
            "lines_written": len(normalized_lines),
            "chars_written": len(content),
            "metadata": {
                "operation": "overwrite" if existed else "create",
                "auditable": True,
                "changed": True,
            },
        }
    except Exception as exc:
        return {"ok": False, "tool": "file_editor_write_lines", "path": path, "error": str(exc)}


@mcp.tool()
def file_editor_str_replace(
    path: str,
    old_text: str,
    new_text: str,
    expected_replacements: int = 1,
) -> dict[str, Any]:
    """
    Replace exact text in a workspace file, guarded by an expected replacement count.
    """
    try:
        if not old_text:
            return {"ok": False, "tool": "file_editor_str_replace", "path": path, "error": "old_text is required."}
        expected_replacements = max(1, int(expected_replacements))
        file_path = _safe_workspace_path(path)
        if not file_path.exists():
            return {"ok": False, "tool": "file_editor_str_replace", "path": path, "error": "File does not exist."}
        if not file_path.is_file():
            return {"ok": False, "tool": "file_editor_str_replace", "path": path, "error": "Path is not a file."}

        text = _read_text(file_path)
        replacement_count = text.count(old_text)
        if replacement_count != expected_replacements:
            return {
                "ok": False,
                "tool": "file_editor_str_replace",
                "path": _rel(file_path),
                "error": (
                    "Replacement count mismatch. Refusing edit to avoid "
                    "ambiguous or broad changes."
                ),
                "found_replacements": replacement_count,
                "expected_replacements": expected_replacements,
            }

        updated = text.replace(old_text, new_text, expected_replacements)
        file_path.write_text(updated, encoding="utf-8")
        return {
            "ok": True,
            "tool": "file_editor_str_replace",
            "path": _rel(file_path),
            "replacements": expected_replacements,
            "old_chars": len(text),
            "new_chars": len(updated),
            "metadata": {
                "operation": "str_replace",
                "auditable": True,
                "changed": True,
            },
        }
    except Exception as exc:
        return {"ok": False, "tool": "file_editor_str_replace", "path": path, "error": str(exc)}


@mcp.tool()
def file_editor_insert(path: str, line: int, content: str) -> dict[str, Any]:
    """
    Insert text before a 1-based line number. Use line total_lines + 1 to append.
    """
    try:
        file_path = _safe_workspace_path(path)
        if not file_path.exists():
            return {"ok": False, "tool": "file_editor_insert", "path": path, "error": "File does not exist."}
        if not file_path.is_file():
            return {"ok": False, "tool": "file_editor_insert", "path": path, "error": "Path is not a file."}

        text = _read_text(file_path)
        lines = text.splitlines(keepends=True)
        line = int(line)
        if line < 1 or line > len(lines) + 1:
            return {
                "ok": False,
                "tool": "file_editor_insert",
                "path": _rel(file_path),
                "error": "Line is outside valid insert range.",
                "valid_range": [1, len(lines) + 1],
            }

        insert_text = content
        if insert_text and not insert_text.endswith("\n"):
            insert_text += "\n"
        lines.insert(line - 1, insert_text)
        updated = "".join(lines)
        file_path.write_text(updated, encoding="utf-8")
        return {
            "ok": True,
            "tool": "file_editor_insert",
            "path": _rel(file_path),
            "line": line,
            "chars_inserted": len(insert_text),
            "metadata": {
                "operation": "insert",
                "auditable": True,
                "changed": True,
            },
        }
    except Exception as exc:
        return {"ok": False, "tool": "file_editor_insert", "path": path, "error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
