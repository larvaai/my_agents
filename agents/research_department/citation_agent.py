from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class CitationAgent:
    """Formats source metadata for Final Synthesis."""

    def run(self, sources: list[dict[str, Any]]) -> dict[str, Any]:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        formatted = []
        for source in sources[:10]:
            title = source.get("title") or source.get("url") or source.get("url_or_path") or "Untitled source"
            url_or_path = source.get("url") or source.get("url_or_path") or ""
            formatted.append(
                {
                    "title": str(title),
                    "url_or_path": str(url_or_path),
                    "source_type": source.get("source_type", "web" if str(url_or_path).startswith("http") else "local_doc"),
                    "retrieved_at": retrieved_at,
                    "relevance": source.get("relevance", "medium"),
                }
            )
        return {
            "agent": "citation_agent",
            "ok": True,
            "sources": formatted,
            "citation_notes": (
                ["No external sources were collected in deterministic mode."]
                if not formatted
                else ["Citations are formatted from collected source metadata."]
            ),
        }
