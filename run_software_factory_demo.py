from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from core.runtime_paths import WORKSPACE_DIR
from orchestration.software_factory_orchestrator import SoftwareFactoryOrchestrator


DEFAULT_TASK = """
Design a small local Python product with a clear business spec, acceptance
criteria, technical analysis, implementation spec, validation plan, and docs
handoff.
""".strip()


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


def _read_task(args: argparse.Namespace) -> str:
    if args.task_file:
        return Path(args.task_file).read_text(encoding="utf-8", errors="replace")
    if args.task:
        return args.task
    return DEFAULT_TASK


def _compact_output(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": result.get("ok"),
        "status": result.get("status"),
        "version": result.get("version"),
        "run_id": result.get("run_id"),
        "artifact_dir": result.get("artifact_dir"),
        "implementation_spec": result.get("implementation_spec"),
        "code_handoff_packet": result.get("code_handoff_packet"),
        "summary_artifact": result.get("summary_artifact"),
        "exported_docs": result.get("exported_docs"),
        "next_recommended_command": result.get("next_recommended_command"),
        "agent_count": result.get("agent_count"),
        "stages": [
            {
                "agent": stage.get("agent"),
                "decision": stage.get("decision"),
                "next_agent": stage.get("route", {}).get("next_agent"),
                "ok": stage.get("ok"),
            }
            for stage in result.get("stage_results", [])
        ],
    }


def main() -> int:
    configure_console_encoding()
    parser = argparse.ArgumentParser(description="Run the v0.7 artifact-first software factory.")
    parser.add_argument("--task", default=None)
    parser.add_argument("--task-file", default=None)
    parser.add_argument("--artifact-root", default=str(WORKSPACE_DIR / "factory_runs"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--export-project-dir", default=None)
    parser.add_argument("--full-json", action="store_true", help="Print the full compact JSON envelope.")
    args = parser.parse_args()

    task = _read_task(args)
    orchestrator = SoftwareFactoryOrchestrator(artifact_root=args.artifact_root)
    result = orchestrator.run(
        task,
        run_id=args.run_id,
        export_project_dir=args.export_project_dir,
    )
    output = result if args.full_json else _compact_output(result)
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
