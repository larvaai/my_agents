from __future__ import annotations

from copy import deepcopy
from typing import Any


class StateStore:
    """Small in-memory state manager owned by the kernel."""

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._state = dict(initial or {})

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def update(self, values: dict[str, Any]) -> None:
        self._state.update(values)

    def delete(self, key: str) -> None:
        self._state.pop(key, None)

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self._state)
