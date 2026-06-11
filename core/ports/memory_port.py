from __future__ import annotations

from typing import Any, Protocol


class MemoryPort(Protocol):
    def retrieve(self, query: str, *, top_k: int = 5) -> dict[str, Any]:
        ...

    def store(self, title: str, data: dict[str, Any], *, tags: list[str] | None = None) -> dict[str, Any]:
        ...
