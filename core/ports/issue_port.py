from __future__ import annotations

from typing import Any, Protocol


class IssuePort(Protocol):
    def create(
        self,
        title: str,
        description: str,
        *,
        kind: str = "task",
        priority: int = 3,
    ) -> dict[str, Any]:
        ...

    def list(self, *, status: str = "open", limit: int = 50) -> dict[str, Any]:
        ...
