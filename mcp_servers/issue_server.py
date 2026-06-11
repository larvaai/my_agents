from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.runtime_paths import PROJECT_DIR, WORKSPACE_DIR

from mcp.server.fastmcp import FastMCP


DEFAULT_DB_PATH = WORKSPACE_DIR / "issues" / "issues.db"
ALLOWED_KIND = {"bug", "feature", "task", "review", "risk", "question"}
ALLOWED_STATUS = {"open", "in_progress", "blocked", "review", "resolved", "closed"}
MAX_TEXT = 20000

mcp = FastMCP(
    "issue-server",
    instructions=(
        "Local SQLite issue tracker for multi-agent planning, bugs, review "
        "findings, risks, and follow-up tasks."
    ),
)


class IssueError(ValueError):
    pass


def _db_path() -> Path:
    configured = os.getenv("ISSUE_DB_PATH", "").strip()
    path = Path(configured) if configured else DEFAULT_DB_PATH
    if not path.is_absolute():
        path = PROJECT_DIR / path

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise IssueError(f"Issue DB must be inside workspace: {path}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def _load_json(value: str | None) -> Any:
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _clean_text(value: str, field: str) -> str:
    value = str(value or "").strip()
    if not value:
        raise IssueError(f"{field} is required.")
    if len(value) > MAX_TEXT:
        raise IssueError(f"{field} is too long: {len(value)} chars.")
    return value


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            priority INTEGER NOT NULL,
            assignee TEXT,
            labels TEXT NOT NULL,
            related_files TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issue_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(issue_id) REFERENCES issues(id)
        )
        """
    )
    conn.commit()
    return conn


def _row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ("labels", "related_files"):
        if key in data:
            data[key] = _load_json(data.get(key))
    return data


def _priority(value: int) -> int:
    return max(1, min(int(value), 5))


@mcp.tool()
def issue_create(
    title: str,
    description: str,
    kind: str = "task",
    priority: int = 3,
    assignee: str = "",
    labels: list[str] | None = None,
    related_files: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a local issue.
    """
    try:
        title = _clean_text(title, "title")
        description = _clean_text(description, "description")
        if kind not in ALLOWED_KIND:
            return {"ok": False, "tool": "issue_create", "error": f"Invalid kind: {kind}", "allowed_kind": sorted(ALLOWED_KIND)}

        now = _now()
        with _connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO issues
                (title, description, kind, status, priority, assignee, labels, related_files, created_at, updated_at)
                VALUES (?, ?, ?, 'open', ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    description,
                    kind,
                    _priority(priority),
                    assignee,
                    _json(labels or []),
                    _json(related_files or []),
                    now,
                    now,
                ),
            )
            conn.commit()
            issue_id = int(cursor.lastrowid)

        return {"ok": True, "tool": "issue_create", "issue_id": issue_id, "title": title}
    except Exception as exc:
        return {"ok": False, "tool": "issue_create", "error": str(exc)}


@mcp.tool()
def issue_update(
    issue_id: int,
    status: str | None = None,
    assignee: str | None = None,
    priority: int | None = None,
    labels: list[str] | None = None,
    related_files: list[str] | None = None,
) -> dict[str, Any]:
    """
    Update status/assignee/priority/labels/related files.
    """
    try:
        updates: list[str] = []
        params: list[Any] = []

        if status is not None:
            if status not in ALLOWED_STATUS:
                return {"ok": False, "tool": "issue_update", "error": f"Invalid status: {status}", "allowed_status": sorted(ALLOWED_STATUS)}
            updates.append("status = ?")
            params.append(status)
            if status == "closed":
                updates.append("closed_at = ?")
                params.append(_now())

        if assignee is not None:
            updates.append("assignee = ?")
            params.append(assignee)

        if priority is not None:
            updates.append("priority = ?")
            params.append(_priority(priority))

        if labels is not None:
            updates.append("labels = ?")
            params.append(_json(labels))

        if related_files is not None:
            updates.append("related_files = ?")
            params.append(_json(related_files))

        if not updates:
            return {"ok": False, "tool": "issue_update", "error": "No fields to update."}

        updates.append("updated_at = ?")
        params.append(_now())
        params.append(int(issue_id))

        with _connect() as conn:
            cursor = conn.execute(f"UPDATE issues SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()

        return {"ok": cursor.rowcount > 0, "tool": "issue_update", "issue_id": issue_id, "rows_updated": cursor.rowcount}
    except Exception as exc:
        return {"ok": False, "tool": "issue_update", "issue_id": issue_id, "error": str(exc)}


@mcp.tool()
def issue_add_comment(issue_id: int, message: str, author: str = "agent") -> dict[str, Any]:
    """
    Add a comment to an issue.
    """
    try:
        message = _clean_text(message, "message")
        author = _clean_text(author or "agent", "author")
        with _connect() as conn:
            exists = conn.execute("SELECT id FROM issues WHERE id = ?", (int(issue_id),)).fetchone()
            if not exists:
                return {"ok": False, "tool": "issue_add_comment", "issue_id": issue_id, "error": "Issue not found."}
            cursor = conn.execute(
                """
                INSERT INTO issue_comments (issue_id, author, message, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (int(issue_id), author, message, _now()),
            )
            conn.execute("UPDATE issues SET updated_at = ? WHERE id = ?", (_now(), int(issue_id)))
            conn.commit()
            comment_id = int(cursor.lastrowid)

        return {"ok": True, "tool": "issue_add_comment", "issue_id": issue_id, "comment_id": comment_id}
    except Exception as exc:
        return {"ok": False, "tool": "issue_add_comment", "issue_id": issue_id, "error": str(exc)}


@mcp.tool()
def issue_list(status: str | None = None, kind: str | None = None, assignee: str | None = None, limit: int = 50) -> dict[str, Any]:
    """
    List local issues.
    """
    try:
        limit = max(1, min(int(limit), 200))
        query = "SELECT * FROM issues"
        clauses: list[str] = []
        params: list[Any] = []

        if status:
            clauses.append("status = ?")
            params.append(status)
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if assignee:
            clauses.append("assignee = ?")
            params.append(assignee)

        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY priority ASC, id DESC LIMIT ?"
        params.append(limit)

        with _connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return {"ok": True, "tool": "issue_list", "count": len(rows), "issues": [_row(row) for row in rows]}
    except Exception as exc:
        return {"ok": False, "tool": "issue_list", "error": str(exc)}


@mcp.tool()
def issue_get(issue_id: int) -> dict[str, Any]:
    """
    Get one issue and its comments.
    """
    try:
        with _connect() as conn:
            issue = conn.execute("SELECT * FROM issues WHERE id = ?", (int(issue_id),)).fetchone()
            comments = conn.execute(
                "SELECT * FROM issue_comments WHERE issue_id = ? ORDER BY id ASC",
                (int(issue_id),),
            ).fetchall()

        if not issue:
            return {"ok": False, "tool": "issue_get", "issue_id": issue_id, "error": "Issue not found."}

        return {
            "ok": True,
            "tool": "issue_get",
            "issue": _row(issue),
            "comments": [dict(row) for row in comments],
        }
    except Exception as exc:
        return {"ok": False, "tool": "issue_get", "issue_id": issue_id, "error": str(exc)}


@mcp.tool()
def issue_search(query: str, limit: int = 50) -> dict[str, Any]:
    """
    Search issues by title/description.
    """
    try:
        query = _clean_text(query, "query")
        limit = max(1, min(int(limit), 200))
        pattern = f"%{query}%"
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM issues
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY priority ASC, id DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()

        return {"ok": True, "tool": "issue_search", "query": query, "count": len(rows), "issues": [_row(row) for row in rows]}
    except Exception as exc:
        return {"ok": False, "tool": "issue_search", "query": query, "error": str(exc)}


@mcp.tool()
def issue_stats() -> dict[str, Any]:
    """
    Return counts by status and kind.
    """
    try:
        with _connect() as conn:
            by_status = {
                row["status"]: row["count"]
                for row in conn.execute("SELECT status, COUNT(*) AS count FROM issues GROUP BY status").fetchall()
            }
            by_kind = {
                row["kind"]: row["count"]
                for row in conn.execute("SELECT kind, COUNT(*) AS count FROM issues GROUP BY kind").fetchall()
            }
            total = conn.execute("SELECT COUNT(*) AS count FROM issues").fetchone()["count"]
        return {"ok": True, "tool": "issue_stats", "count": total, "by_status": by_status, "by_kind": by_kind}
    except Exception as exc:
        return {"ok": False, "tool": "issue_stats", "error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")

