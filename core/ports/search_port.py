from __future__ import annotations

from typing import Any, Protocol


class SearchPort(Protocol):
    def search(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        ...
