from __future__ import annotations

from typing import Any

from core.schemas import ToolRequest


class NullToolFeature:
    name = "null_tool"

    def execute(self, request: ToolRequest) -> dict[str, Any]:
        return {
            "ok": False,
            "tool": request.name,
            "missing_capability": True,
            "error": f"Tool capability '{request.name}' is not installed.",
        }


class NullSearchFeature:
    def search(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        return {
            "ok": True,
            "query": query,
            "results": [],
            "module": "null_search",
            "message": "Search feature is not installed.",
        }


class NullMemoryFeature:
    def retrieve(self, query: str, *, top_k: int = 5) -> dict[str, Any]:
        return {
            "ok": True,
            "query": query,
            "hits": [],
            "module": "null_memory",
            "message": "Memory feature is not installed.",
        }

    def store(self, title: str, data: dict[str, Any], *, tags: list[str] | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "stored": False,
            "title": title,
            "tags": tags or [],
            "module": "null_memory",
            "message": "Memory feature is not installed.",
        }
