from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestration.global_supervisor import run_global_supervisor


DEFAULT_TASK = "What is RAG?"


def configure_console_encoding() -> None:
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _read_task(args: argparse.Namespace) -> str:
    if args.task_file:
        return Path(args.task_file).read_text(encoding="utf-8", errors="replace")
    if args.task:
        return args.task
    return DEFAULT_TASK


def _compact_result(result: dict[str, Any], log_path: Path) -> dict[str, Any]:
    departments = result.get("department_outputs", {})
    software_factory = departments.get("software_factory", {}) if isinstance(departments, dict) else {}
    return {
        "ok": result.get("ok"),
        "status": result.get("status"),
        "route_decision": result.get("route_decision"),
        "execution_plan": result.get("execution_plan"),
        "departments": sorted(departments.keys()) if isinstance(departments, dict) else [],
        "safety": departments.get("safety") if isinstance(departments, dict) else None,
        "software_factory": {
            "ok": software_factory.get("ok"),
            "status": software_factory.get("status"),
            "run_id": software_factory.get("run_id"),
            "artifact_dir": software_factory.get("artifact_dir"),
            "implementation_spec": software_factory.get("implementation_spec"),
            "code_handoff_packet": software_factory.get("code_handoff_packet"),
            "exported_docs": software_factory.get("exported_docs"),
            "next_recommended_command": software_factory.get("next_recommended_command"),
            "stage_count": software_factory.get("stage_count"),
            "agent_count": software_factory.get("agent_count"),
            "stages": software_factory.get("stages", []),
        } if software_factory else None,
        "final_answer": result.get("final_answer"),
        "log_path": str(log_path),
    }


def main() -> int:
    configure_console_encoding()
    parser = argparse.ArgumentParser(description="Run a task through Global Supervisor.")
    parser.add_argument("--task", default=None)
    parser.add_argument("--task-file", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--artifact-root", default=str(Path("workspace") / "factory_runs"))
    parser.add_argument("--log-dir", default=str(Path("test_runs") / "global_supervisor"))
    parser.add_argument("--run-coding", action="store_true")
    parser.add_argument("--research-use-tools", action="store_true")
    parser.add_argument("--full-json", action="store_true")
    args = parser.parse_args()

    task = _read_task(args)
    result = run_global_supervisor(
        task,
        context={
            "run_id": args.run_id,
            "artifact_root": args.artifact_root,
        },
        run_coding=args.run_coding,
        research_use_tools=args.research_use_tools,
    )

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    run_label = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"{run_label}.json"
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    output = result if args.full_json else _compact_result(result, log_path)
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
