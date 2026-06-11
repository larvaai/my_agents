from __future__ import annotations

from typing import Any, Protocol

from core.schemas import ToolRequest


class ToolPort(Protocol):
    name: str

    def execute(self, request: ToolRequest) -> dict[str, Any]:
        ...
