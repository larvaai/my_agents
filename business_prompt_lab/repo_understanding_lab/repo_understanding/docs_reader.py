from __future__ import annotations

from pathlib import Path
from typing import Any


MAX_DOCS = 80
MAX_DOC_BYTES = 60_000


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def summarize(text: str, max_chars: int = 500) -> str:
    chunks = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    summary = " ".join(chunks)
    return summary[:max_chars]


def read_docs(repo_path: Path, file_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for node in file_map:
        if node["role"] != "docs" or node["language"] != "markdown":
            continue
        if len(docs) >= MAX_DOCS:
            break
        path = repo_path / node["path"]
        if path.stat().st_size > MAX_DOC_BYTES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        docs.append(
            {
                "id": f"doc:{node['path']}",
                "path": node["path"],
                "title": extract_title(text, node["path"]),
                "summary": summarize(text),
                "content": text,
            }
        )
    return docs

