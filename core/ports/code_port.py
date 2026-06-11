from __future__ import annotations

from typing import Any, Protocol


class CodeEditPort(Protocol):
    def view(self, path: str, *, start_line: int = 1, max_lines: int = 200) -> dict[str, Any]:
        ...

    def replace(
        self,
        path: str,
        old_text: str,
        new_text: str,
        *,
        expected_replacements: int = 1,
    ) -> dict[str, Any]:
        ...

    def insert(self, path: str, line: int, content: str) -> dict[str, Any]:
        ...
