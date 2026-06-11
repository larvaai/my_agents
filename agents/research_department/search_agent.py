from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.capabilities import call_tool
from core.schemas import capability_data


@dataclass
class SearchAgent:
    """Research search agent with deterministic default and optional MCP use."""

    use_tools: bool = False
    limit: int = 5

    def run(self, query: str) -> dict[str, Any]:
        if self.use_tools:
            result = call_tool("search.web_search", {"query": query, "limit": self.limit})
            data = capability_data(result)
            if result.get("ok") is True:
                return {
                    "agent": "search_agent",
                    "ok": True,
                    "query": query,
                    "results": data.get("results", []),
                    "provider": data.get("provider"),
                    "used_tool": "search.web_search",
                }
            return {
                "agent": "search_agent",
                "ok": False,
                "query": query,
                "results": [],
                "error": result.get("error") or data.get("errors") or "search failed",
                "used_tool": "search.web_search",
            }

        return {
            "agent": "search_agent",
            "ok": True,
            "query": query,
            "results": [],
            "provider": "deterministic_stub",
            "used_tool": None,
            "notes": ["Search MCP is wired but not used in deterministic smoke mode."],
        }
