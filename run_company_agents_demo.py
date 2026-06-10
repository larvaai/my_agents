from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from orchestration.company_orchestrator import CompanyOrchestratorV05


DEFAULT_TASK = """
Create a small Python file code/company_v05_smoke.py that prints COMPANY_AGENTS_V05_OK.
Then validate that the generated Python file runs successfully.
""".strip()


def _read_task(args: argparse.Namespace) -> str:
    if args.task_file:
        return Path(args.task_file).read_text(encoding="utf-8")
    if args.task:
        return args.task
    return DEFAULT_TASK


def _ok(result: dict[str, Any]) -> bool:
    return result.get("ok") is True and result.get("final_route", {}).get("next_agent") == "done"


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


def main() -> int:
    configure_console_encoding()
    parser = argparse.ArgumentParser(description="Run full company-style department agents at v0.5.")
    parser.add_argument("--version", default="v0.5", choices=["v0.5"])
    parser.add_argument("--task", default=None)
    parser.add_argument("--task-file", default=None)
    parser.add_argument("--max-cycles", type=int, default=2)
    parser.add_argument("--real", action="store_true", help="Run the real LangGraph LLM/tool company pipeline.")
    parser.add_argument("--real-max-steps", type=int, default=None)
    parser.add_argument("--use-llm", action="store_true", help="Use LLM prompt lenses instead of deterministic lenses.")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    orchestrator = CompanyOrchestratorV05(
        max_cycles=args.max_cycles,
        use_llm=args.use_llm,
        model=args.model,
    )
    task = _read_task(args)
    if args.real:
        result = orchestrator.run_real(task, max_steps=args.real_max_steps)
    else:
        result = orchestrator.run(task)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if _ok(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
