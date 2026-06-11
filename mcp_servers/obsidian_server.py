from __future__ import annotations

import os
import re
from datetime import date as date_cls, datetime
from pathlib import Path
from typing import Any

from core.runtime_paths import PROJECT_DIR, WORKSPACE_DIR

from mcp.server.fastmcp import FastMCP


DEFAULT_VAULT_DIR = WORKSPACE_DIR / "obsidian_vault"
MAX_NOTE_CHARS = 1_000_000
MAX_SEARCH_RESULTS = 100
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S{8,}"),
)

mcp = FastMCP(
    "obsidian-server",
    instructions=(
        "Local Obsidian-style markdown vault. Sandboxed to OBSIDIAN_VAULT_DIR "
        "or workspace/obsidian_vault. Do not store secrets."
    ),
)


class ObsidianError(ValueError):
    pass


def _vault_dir() -> Path:
    configured = os.getenv("OBSIDIAN_VAULT_DIR", "").strip()
    root = Path(configured) if configured else DEFAULT_VAULT_DIR
    if not root.is_absolute():
        root = PROJECT_DIR / root
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _safe_note_path(raw_path: str) -> Path:
    if not raw_path or not raw_path.strip():
        raise ObsidianError("path is required")

    path = Path(raw_path)
    if path.suffix.lower() != ".md":
        path = path.with_suffix(".md")
    if path.is_absolute():
        candidate = path
    else:
        candidate = _vault_dir() / path

    resolved = candidate.resolve()
    vault = _vault_dir()
    if resolved != vault and not resolved.is_relative_to(vault):
        raise ObsidianError(f"Path is outside Obsidian vault: {raw_path}")
    return resolved


def _rel(path: Path) -> str:
    return str(path.resolve().relative_to(_vault_dir())).replace("\\", "/")


def _check_content(content: str) -> None:
    if len(content) > MAX_NOTE_CHARS:
        raise ObsidianError(f"Note content too large: {len(content)} chars")
    for pattern in SECRET_PATTERNS:
        if pattern.search(content):
            raise ObsidianError("Content looks like it may contain a secret/token. Refusing to write.")


def _read(path: Path, max_chars: int) -> tuple[str, bool]:
    text = path.read_text(encoding="utf-8", errors="replace")
    max_chars = max(1, min(int(max_chars), MAX_NOTE_CHARS))
    return text[:max_chars], len(text) > max_chars


@mcp.tool()
def obsidian_list_notes(folder: str = ".", limit: int = 100) -> dict[str, Any]:
    """
    List markdown notes under a vault folder.
    """
    try:
        folder_path = _safe_note_path(folder) if folder.endswith(".md") else (_vault_dir() / folder).resolve()
        vault = _vault_dir()
        if folder_path != vault and not folder_path.is_relative_to(vault):
            raise ObsidianError(f"Folder is outside Obsidian vault: {folder}")
        if folder_path.is_file():
            notes = [folder_path]
        elif folder_path.exists():
            notes = sorted(path for path in folder_path.rglob("*.md") if path.is_file())
        else:
            notes = []

        limit = max(1, min(int(limit), 500))
        selected = notes[:limit]
        return {
            "ok": True,
            "tool": "obsidian_list_notes",
            "folder": folder,
            "count": len(selected),
            "total": len(notes),
            "truncated": len(notes) > limit,
            "notes": [{"path": _rel(path), "size": path.stat().st_size} for path in selected],
            "vault": str(vault),
        }
    except Exception as exc:
        return {"ok": False, "tool": "obsidian_list_notes", "folder": folder, "error": str(exc)}


@mcp.tool()
def obsidian_read_note(path: str, max_chars: int = 20000) -> dict[str, Any]:
    """
    Read one markdown note.
    """
    try:
        note_path = _safe_note_path(path)
        if not note_path.exists():
            return {"ok": False, "tool": "obsidian_read_note", "path": path, "error": "Note does not exist."}
        text, truncated = _read(note_path, max_chars=max_chars)
        return {
            "ok": True,
            "tool": "obsidian_read_note",
            "path": _rel(note_path),
            "text": text,
            "truncated": truncated,
            "chars": len(text),
        }
    except Exception as exc:
        return {"ok": False, "tool": "obsidian_read_note", "path": path, "error": str(exc)}


@mcp.tool()
def obsidian_write_note(path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    """
    Create or overwrite one markdown note.
    """
    try:
        _check_content(content)
        note_path = _safe_note_path(path)
        existed = note_path.exists()
        if existed and not overwrite:
            return {"ok": False, "tool": "obsidian_write_note", "path": path, "error": "Note exists and overwrite is false."}
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "tool": "obsidian_write_note",
            "path": _rel(note_path),
            "chars_written": len(content),
            "metadata": {
                "operation": "overwrite" if existed else "create",
                "security_risk": "low",
                "changed": True,
            },
        }
    except Exception as exc:
        return {"ok": False, "tool": "obsidian_write_note", "path": path, "error": str(exc)}


@mcp.tool()
def obsidian_append_note(path: str, content: str) -> dict[str, Any]:
    """
    Append text to a markdown note, creating it if missing.
    """
    try:
        _check_content(content)
        note_path = _safe_note_path(path)
        note_path.parent.mkdir(parents=True, exist_ok=True)
        existing = note_path.read_text(encoding="utf-8", errors="replace") if note_path.exists() else ""
        separator = "" if not existing or existing.endswith("\n") or content.startswith("\n") else "\n"
        note_path.write_text(existing + separator + content, encoding="utf-8")
        return {
            "ok": True,
            "tool": "obsidian_append_note",
            "path": _rel(note_path),
            "chars_appended": len(separator + content),
            "metadata": {"operation": "append", "security_risk": "low", "changed": True},
        }
    except Exception as exc:
        return {"ok": False, "tool": "obsidian_append_note", "path": path, "error": str(exc)}


@mcp.tool()
def obsidian_search_notes(query: str, folder: str = ".", limit: int = 20) -> dict[str, Any]:
    """
    Search markdown notes by simple case-insensitive text match.
    """
    try:
        if not query:
            return {"ok": False, "tool": "obsidian_search_notes", "error": "query is required."}

        listed = obsidian_list_notes(folder=folder, limit=500)
        if not listed.get("ok"):
            return listed

        query_lower = query.lower()
        limit = max(1, min(int(limit), MAX_SEARCH_RESULTS))
        matches: list[dict[str, Any]] = []

        for item in listed.get("notes", []):
            note_path = _safe_note_path(item["path"])
            text = note_path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if query_lower in line.lower():
                    matches.append({"path": _rel(note_path), "lineno": lineno, "line": line.strip()[:300]})
                    break
            if len(matches) >= limit:
                break

        return {
            "ok": True,
            "tool": "obsidian_search_notes",
            "query": query,
            "count": len(matches),
            "matches": matches,
        }
    except Exception as exc:
        return {"ok": False, "tool": "obsidian_search_notes", "query": query, "error": str(exc)}


@mcp.tool()
def obsidian_create_daily_note(date: str = "", content: str = "") -> dict[str, Any]:
    """
    Create or overwrite Daily/YYYY-MM-DD.md.
    """
    try:
        _check_content(content)
        if date:
            parsed = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            parsed = date_cls.today()
        note_path = f"Daily/{parsed.isoformat()}.md"
        body = content or f"# {parsed.isoformat()}\n"
        return obsidian_write_note(note_path, body, overwrite=True)
    except Exception as exc:
        return {"ok": False, "tool": "obsidian_create_daily_note", "date": date, "error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")

