from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

from tools.event_log import DEFAULT_RUNS_DIR


def get_runs_dir(raw_path: str | None = None) -> Path:
    return Path(raw_path or os.getenv("AGENT_RUNS_DIR", str(DEFAULT_RUNS_DIR)))


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return {
            "run_id": path.parent.name,
            "status": "invalid_summary",
            "summary_path": str(path),
        }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    events = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            events.append(
                {
                    "kind": "InvalidEvent",
                    "line_number": line_number,
                    "error": str(exc),
                    "raw": line,
                }
            )
    return events


def load_runs(runs_dir: str | None = None) -> list[dict[str, Any]]:
    root = get_runs_dir(runs_dir)
    records: dict[str, dict[str, Any]] = {}

    index_path = root / "index.jsonl"
    for record in _read_jsonl(index_path):
        run_id = record.get("run_id")
        if isinstance(run_id, str):
            records[run_id] = record

    if root.exists():
        for summary_path in root.glob("*/summary.json"):
            summary = _read_json(summary_path)
            if not summary:
                continue
            run_id = summary.get("run_id") or summary_path.parent.name
            merged = {
                **records.get(str(run_id), {}),
                **summary,
                "run_id": str(run_id),
                "summary_path": str(summary_path),
                "events_path": str(summary_path.parent / "events.jsonl"),
            }
            records[str(run_id)] = merged

    return sorted(
        records.values(),
        key=lambda item: str(item.get("finished_at", "")),
        reverse=True,
    )


def resolve_run_id(run_id: str | None, runs_dir: str | None = None) -> str:
    runs = load_runs(runs_dir)
    if not runs:
        raise ValueError("No agent runs found.")

    if not run_id or run_id == "latest":
        return str(runs[0]["run_id"])

    matches = [str(run["run_id"]) for run in runs if str(run["run_id"]).startswith(run_id)]
    if not matches:
        raise ValueError(f"No run matches: {run_id}")
    if len(matches) > 1:
        raise ValueError(f"Run prefix is ambiguous: {run_id} -> {matches}")
    return matches[0]


def load_events(run_id: str | None = None, runs_dir: str | None = None) -> list[dict[str, Any]]:
    root = get_runs_dir(runs_dir)
    resolved = resolve_run_id(run_id, runs_dir)
    return _read_jsonl(root / resolved / "events.jsonl")


def _contains(value: Any, needle: str) -> bool:
    return needle.lower() in json.dumps(value, ensure_ascii=False).lower()


def filter_events(
    events: Iterable[dict[str, Any]],
    *,
    kind: str | None = None,
    status: str | None = None,
    tool: str | None = None,
    text: str | None = None,
) -> list[dict[str, Any]]:
    filtered = []
    for event in events:
        if kind and event.get("kind") != kind:
            continue
        if status and event.get("status") != status:
            continue
        if tool and event.get("tool") != tool:
            continue
        if text and not _contains(event, text):
            continue
        filtered.append(event)
    return filtered


def summarize_event(event: dict[str, Any]) -> str:
    sequence = event.get("sequence", "?")
    kind = event.get("kind", "?")
    step = event.get("step")
    prefix = f"#{sequence} {kind}"
    if step is not None:
        prefix += f" step={step}"

    if kind == "MessageEvent":
        role = event.get("role", "?")
        content = str(event.get("content", "")).replace("\n", " ")
        return f"{prefix} role={role} {content[:160]}"

    if kind == "ActionEvent":
        action = event.get("action", "?")
        tool = event.get("tool")
        if tool:
            return f"{prefix} action={action} tool={tool}"
        return f"{prefix} action={action}"

    if kind == "ObservationEvent":
        result = event.get("result", {})
        ok = result.get("ok") if isinstance(result, dict) else None
        tool = event.get("tool", "?")
        if isinstance(result, dict):
            metadata = result.get("command_metadata") or {}
            if isinstance(metadata, dict) and metadata:
                summary = metadata.get("summary", "")
                risk = metadata.get("security_risk", "")
                return f"{prefix} tool={tool} ok={ok} risk={risk} summary={summary}"
        return f"{prefix} tool={tool} ok={ok}"

    if kind == "StateEvent":
        status = event.get("status", "?")
        return f"{prefix} status={status}"

    return prefix
