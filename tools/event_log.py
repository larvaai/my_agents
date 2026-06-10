from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RUNS_DIR = PROJECT_DIR / "agent_runs"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> str:
    return str(value)


def _make_run_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"{timestamp}_{suffix}"


class EventLogger:
    """
    Append-only JSONL event log for a single agent run.

    The goal is intentionally close to OpenHands' event model, but smaller:
    every user message, action, observation, and state update is persisted so a
    run can be replayed or inspected after stdout scrollback is gone.
    """

    def __init__(self, run_id: str | None = None, enabled: bool | None = None) -> None:
        if enabled is None:
            enabled = os.getenv("AGENT_EVENT_LOG", "1") != "0"

        self.enabled = enabled
        self.run_id = run_id or os.getenv("AGENT_RUN_ID") or _make_run_id()
        runs_dir = Path(os.getenv("AGENT_RUNS_DIR", str(DEFAULT_RUNS_DIR)))
        self.runs_dir = runs_dir
        self.run_dir = runs_dir / self.run_id
        self.events_path = self.run_dir / "events.jsonl"
        self.summary_path = self.run_dir / "summary.json"
        self.index_path = runs_dir / "index.jsonl"
        self.started_monotonic = time.monotonic()
        self.sequence = 0

        if self.enabled:
            self.run_dir.mkdir(parents=True, exist_ok=True)
            self.runs_dir.mkdir(parents=True, exist_ok=True)

    def emit(self, kind: str, **payload: Any) -> None:
        if not self.enabled:
            return

        self.sequence += 1
        event = {
            "sequence": self.sequence,
            "timestamp": _utc_now(),
            "run_id": self.run_id,
            "kind": kind,
            **payload,
        }
        with self.events_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False, default=_json_default) + "\n")

    def write_summary(self, **summary: Any) -> None:
        if not self.enabled:
            return

        payload = {
            "run_id": self.run_id,
            "finished_at": _utc_now(),
            "duration_seconds": round(time.monotonic() - self.started_monotonic, 3),
            "events_path": str(self.events_path),
            **summary,
        }
        self.summary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
        index_record = {
            "run_id": self.run_id,
            "finished_at": payload["finished_at"],
            "duration_seconds": payload["duration_seconds"],
            "status": payload.get("status"),
            "events_path": str(self.events_path),
            "summary_path": str(self.summary_path),
            "metrics": payload.get("metrics", {}),
        }
        with self.index_path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(index_record, ensure_ascii=False, default=_json_default)
                + "\n"
            )
