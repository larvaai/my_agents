from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.tool_registry import call_tool


@dataclass
class SearchAgent:
    """Research search agent with deterministic default and optional MCP use."""

    use_tools: bool = False
    limit: int = 5

    def run(self, query: str) -> dict[str, Any]:
        if self.use_tools:
            result = call_tool("search.web_search", {"query": query, "limit": self.limit})
            if result.get("ok") is True:
                return {
                    "agent": "search_agent",
                    "ok": True,
                    "query": query,
                    "results": result.get("results", []),
                    "provider": result.get("provider"),
                    "used_tool": "search.web_search",
                }
            return {
                "agent": "search_agent",
                "ok": False,
                "query": query,
                "results": [],
                "error": result.get("error") or result.get("errors") or "search failed",
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
