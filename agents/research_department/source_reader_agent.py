from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.capabilities import call_tool
from core.schemas import capability_data


@dataclass
class SourceReaderAgent:
    """Reads source URLs through Fetch MCP when explicitly enabled."""

    use_tools: bool = False
    max_chars: int = 6000

    def run(self, sources: list[dict[str, Any]]) -> dict[str, Any]:
        read_items: list[dict[str, Any]] = []
        if self.use_tools:
            for source in sources[:5]:
                url = source.get("url") or source.get("url_or_path")
                if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                    continue
                result = call_tool("fetch.fetch_url", {"url": url, "max_chars": self.max_chars})
                data = capability_data(result)
                read_items.append(
                    {
                        "url": url,
                        "ok": result.get("ok") is True,
                        "title": data.get("title") or source.get("title", ""),
                        "text_excerpt": (data.get("text") or "")[:1200],
                        "error": result.get("error"),
                    }
                )

        return {
            "agent": "source_reader_agent",
            "ok": all(item.get("ok") for item in read_items) if read_items else True,
            "read_items": read_items,
            "used_tool": "fetch.fetch_url" if self.use_tools else None,
            "notes": [] if read_items else ["No URL fetch was performed."],
        }
