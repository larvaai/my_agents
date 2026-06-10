from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"
DEFAULT_LEDGER_DIR = WORKSPACE_DIR / "ledger"
LEDGER_PATH = Path(os.getenv("LEDGER_PATH", str(DEFAULT_LEDGER_DIR / "ledger.jsonl")))

mcp = FastMCP(
    "ledger-server",
    instructions=(
        "Append-only project ledger for decisions, observations, TODOs, and "
        "audit notes. Data is stored as JSONL under the workspace by default."
    ),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_ledger_path() -> Path:
    path = LEDGER_PATH
    if not path.is_absolute():
        path = WORKSPACE_DIR / path
    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise ValueError(f"Ledger path is outside workspace: {path}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _read_entries() -> list[dict[str, Any]]:
    path = _ensure_ledger_path()
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            entries.append({"id": "", "entry_type": "invalid", "raw": line})
    return entries


@mcp.tool()
def ledger_append(
    entry_type: str,
    title: str,
    data: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Append one entry to the project ledger.
    """
    try:
        if not entry_type.strip():
            return {"ok": False, "tool": "ledger_append", "error": "entry_type is required."}
        if not title.strip():
            return {"ok": False, "tool": "ledger_append", "error": "title is required."}

        entry = {
            "id": uuid.uuid4().hex,
            "timestamp": _utc_now(),
            "entry_type": entry_type.strip(),
            "title": title.strip(),
            "tags": tags or [],
            "data": data or {},
        }
        path = _ensure_ledger_path()
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return {"ok": True, "tool": "ledger_append", "entry": entry, "ledger_path": str(path)}
    except Exception as exc:
        return {"ok": False, "tool": "ledger_append", "error": str(exc)}


@mcp.tool()
def ledger_tail(limit: int = 20) -> dict[str, Any]:
    """
    Return the most recent ledger entries.
    """
    try:
        limit = max(1, min(int(limit), 200))
        entries = _read_entries()
        return {"ok": True, "tool": "ledger_tail", "entries": entries[-limit:], "count": len(entries)}
    except Exception as exc:
        return {"ok": False, "tool": "ledger_tail", "error": str(exc), "entries": []}


@mcp.tool()
def ledger_search(
    text: str | None = None,
    entry_type: str | None = None,
    tag: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search ledger entries by text, type, or tag.
    """
    try:
        limit = max(1, min(int(limit), 200))
        entries = _read_entries()
        results = []
        for entry in entries:
            if entry_type and entry.get("entry_type") != entry_type:
                continue
            if tag and tag not in (entry.get("tags") or []):
                continue
            if text:
                haystack = json.dumps(entry, ensure_ascii=False).lower()
                if text.lower() not in haystack:
                    continue
            results.append(entry)
        return {"ok": True, "tool": "ledger_search", "results": results[-limit:], "total_matches": len(results)}
    except Exception as exc:
        return {"ok": False, "tool": "ledger_search", "error": str(exc), "results": []}


@mcp.tool()
def ledger_get(entry_id: str) -> dict[str, Any]:
    """
    Get a ledger entry by id.
    """
    try:
        for entry in _read_entries():
            if entry.get("id") == entry_id:
                return {"ok": True, "tool": "ledger_get", "entry": entry}
        return {"ok": False, "tool": "ledger_get", "error": "Entry not found.", "entry_id": entry_id}
    except Exception as exc:
        return {"ok": False, "tool": "ledger_get", "error": str(exc), "entry_id": entry_id}


@mcp.tool()
def ledger_stats() -> dict[str, Any]:
    """
    Return simple ledger counts.
    """
    try:
        entries = _read_entries()
        by_type: dict[str, int] = {}
        for entry in entries:
            entry_type = str(entry.get("entry_type", "unknown"))
            by_type[entry_type] = by_type.get(entry_type, 0) + 1
        return {
            "ok": True,
            "tool": "ledger_stats",
            "ledger_path": str(_ensure_ledger_path()),
            "count": len(entries),
            "by_type": by_type,
        }
    except Exception as exc:
        return {"ok": False, "tool": "ledger_stats", "error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
