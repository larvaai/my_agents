from __future__ import annotations

from typing import Any, Protocol


class BrowserPort(Protocol):
    def get_text(self, url: str, *, selector: str = "body") -> dict[str, Any]:
        ...

    def screenshot(self, url: str, path: str, *, full_page: bool = True) -> dict[str, Any]:
        ...
