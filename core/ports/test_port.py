from __future__ import annotations

from typing import Any, Protocol


class TestRunPort(Protocol):
    def run(self, target: str = ".", *, timeout: int = 60) -> dict[str, Any]:
        ...
