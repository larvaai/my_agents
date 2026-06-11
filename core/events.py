from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


EventListener = Callable[["KernelEvent"], None]


@dataclass(frozen=True)
class KernelEvent:
    event_type: str
    payload: dict[str, Any]
    source: str = "kernel"
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)


class EventBus:
    """
    In-process pub/sub bus for kernel events.

    Listeners are intentionally best-effort. A broken optional subscriber should
    not crash tool execution or task routing.
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[EventListener]] = {}
        self._history: list[KernelEvent] = []

    def subscribe(self, event_type: str, listener: EventListener) -> None:
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        source: str = "kernel",
    ) -> KernelEvent:
        event = KernelEvent(
            event_type=event_type,
            payload=dict(payload or {}),
            source=source,
        )
        self._history.append(event)

        listeners = [
            *self._listeners.get(event_type, []),
            *self._listeners.get("*", []),
        ]
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                continue

        return event

    def history(self, *, limit: int | None = None) -> list[KernelEvent]:
        if limit is None:
            return list(self._history)
        return self._history[-limit:]

    def clear(self) -> None:
        self._history.clear()
