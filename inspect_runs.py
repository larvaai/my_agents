from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from tools.event_reader import (
    filter_events,
    load_events,
    load_runs,
    resolve_run_id,
    summarize_event,
)


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def configure_console_encoding() -> None:
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def cmd_list(args: argparse.Namespace) -> int:
    runs = load_runs(args.runs_dir)
    for run in runs[: args.limit]:
        metrics = run.get("metrics") or {}
        print(
            f"{run.get('run_id')}  "
            f"status={run.get('status')}  "
            f"steps={metrics.get('steps')}  "
            f"tools={metrics.get('tool_calls')}  "
            f"failures={metrics.get('tool_failures')}  "
            f"finished={run.get('finished_at')}"
        )
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    run_id = resolve_run_id(args.run_id, args.runs_dir)
    runs = {run["run_id"]: run for run in load_runs(args.runs_dir)}
    _print_json(runs[run_id])
    return 0


def cmd_events(args: argparse.Namespace) -> int:
    events = load_events(args.run_id, args.runs_dir)
    events = filter_events(
        events,
        kind=args.kind,
        status=args.status,
        tool=args.tool,
        text=args.text,
    )

    if args.json:
        _print_json(events[: args.limit])
        return 0

    for event in events[: args.limit]:
        print(summarize_event(event))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect local my_agents run summaries and event logs."
    )
    parser.add_argument(
        "--runs-dir",
        default=None,
        help="Override agent runs directory. Defaults to AGENT_RUNS_DIR or ./agent_runs.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List recent runs.")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.set_defaults(func=cmd_list)

    summary_parser = subparsers.add_parser("summary", help="Show one run summary.")
    summary_parser.add_argument("run_id", nargs="?", default="latest")
    summary_parser.set_defaults(func=cmd_summary)

    events_parser = subparsers.add_parser("events", help="Show or search run events.")
    events_parser.add_argument("run_id", nargs="?", default="latest")
    events_parser.add_argument("--kind", default=None)
    events_parser.add_argument("--status", default=None)
    events_parser.add_argument("--tool", default=None)
    events_parser.add_argument("--text", default=None)
    events_parser.add_argument("--limit", type=int, default=100)
    events_parser.add_argument("--json", action="store_true")
    events_parser.set_defaults(func=cmd_events)

    return parser


def main() -> int:
    configure_console_encoding()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
