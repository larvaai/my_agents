from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agents.code_agent import CodeAgent
from agents.test_agent import TestAgent
from orchestration.code_test_orchestrator import CodeTestOrchestrator


DEFAULT_TASK = """
Create a small Python file code/lens_smoke_test.py that prints CODE_TEST_LENS_OK.
Then validate that the generated Python file runs successfully.
""".strip()


def _read_task(args: argparse.Namespace) -> str:
    if args.task_file:
        return Path(args.task_file).read_text(encoding="utf-8")
    if args.task:
        return args.task
    return DEFAULT_TASK


def _compact_for_exit(result: dict[str, Any]) -> bool:
    if "ok" in result:
        return bool(result["ok"])
    execution = result.get("execution", {})
    if isinstance(execution, dict) and "ok" in execution:
        return bool(execution["ok"])
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Code/Test department agents at v0.5.")
    parser.add_argument("--version", default="v0.5", choices=["v0.5"])
    parser.add_argument("--agent", default="orchestrator", choices=["code", "test", "orchestrator"])
    parser.add_argument("--task", default=None)
    parser.add_argument("--task-file", default=None)
    parser.add_argument("--max-cycles", type=int, default=2)
    parser.add_argument("--use-llm", action="store_true", help="Use LLM prompt lenses instead of deterministic lenses.")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    task = _read_task(args)

    if args.agent == "code":
        result = CodeAgent(use_llm=args.use_llm, model=args.model).run(task)
    elif args.agent == "test":
        code_result = CodeAgent(use_llm=args.use_llm, model=args.model).run(task)
        result = TestAgent(use_llm=args.use_llm, model=args.model).run(task, code_result=code_result)
    else:
        result = CodeTestOrchestrator(
            max_cycles=args.max_cycles,
            use_llm=args.use_llm,
            model=args.model,
        ).run(task)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if _compact_for_exit(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
