from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LedgerEntry:
    entry_type: str
    title: str
    data: dict[str, Any]
    tags: tuple[str, ...] = ()
    entry_id: str = ""
    timestamp: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.entry_id or uuid.uuid4().hex,
            "timestamp": self.timestamp or time.time(),
            "entry_type": self.entry_type,
            "title": self.title,
            "data": self.data,
            "tags": list(self.tags),
        }


class JsonlLedger:
    """Small append-only ledger for kernel-level records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, entry: LedgerEntry) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = entry.as_dict()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return payload
