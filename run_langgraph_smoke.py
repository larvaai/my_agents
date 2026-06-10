from __future__ import annotations

import json
import shutil
from pathlib import Path

from orchestration.langgraph_orchestrator import build_graph, make_tool_node
from tools.mcp_config import WORKSPACE_DIR
from tools.tool_registry import call_tool


SMOKE_DIR = WORKSPACE_DIR / "_langgraph_smoke"


def _cleanup(path: Path) -> None:
    if not path.exists():
        return

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved == workspace or not resolved.is_relative_to(workspace):
        raise RuntimeError(f"Refusing to clean unexpected path: {resolved}")

    if resolved.is_dir():
        shutil.rmtree(resolved)
    else:
        resolved.unlink()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _exercise_failure_capture_and_repair_guard() -> None:
    _cleanup(SMOKE_DIR)

    created = call_tool(
        "file_editor.file_editor_write_lines",
        {
            "path": "_langgraph_smoke/failing.py",
            "lines": ["value = 1"],
            "overwrite": True,
        },
    )
    _assert(bool(created.get("ok")), f"Failed to create repair guard file: {created}")

    repair_state = {
        "tool_name": "file_editor.file_editor_write_lines",
        "tool_args": {
            "path": "_langgraph_smoke/failing.py",
            "lines": ["value = 2"],
            "overwrite": True,
        },
        "last_agent": "code",
        "last_failure": {
            "file": "_langgraph_smoke/failing.py",
            "line": 1,
            "error": "AssertionError",
        },
        "messages": [],
        "repeated_tool_calls": {},
        "files_modified": [],
        "tests_run": [],
        "repair_attempts": {},
        "step_count": 0,
    }
    repair_out = make_tool_node()(repair_state)
    _assert(
        repair_out["tool_result"].get("policy_code") == "repair_requires_patch_tool",
        f"Whole-file repair rewrite was not blocked: {repair_out['tool_result']}",
    )
    _assert(repair_out.get("next_agent") == "code", f"Repair guard routed incorrectly: {repair_out}")
    print("LANGGRAPH_REPAIR_GUARD_OK")

    failing_test = call_tool(
        "file_editor.file_editor_write_lines",
        {
            "path": "_langgraph_smoke/test_failure_capture.py",
            "lines": [
                "def test():",
                "    raise AssertionError('captured')",
                "",
                "test()",
            ],
            "overwrite": True,
        },
    )
    _assert(bool(failing_test.get("ok")), f"Failed to create failing validation file: {failing_test}")

    validation_state = {
        "tool_name": "python.run_python",
        "tool_args": {
            "path": "_langgraph_smoke/test_failure_capture.py",
            "timeout": 10,
        },
        "last_agent": "test",
        "messages": [],
        "repeated_tool_calls": {},
        "files_modified": [],
        "tests_run": [],
        "last_failure": {},
        "repair_attempts": {},
        "step_count": 0,
    }
    validation_out = make_tool_node()(validation_state)
    failure = validation_out.get("last_failure", {})
    attempts = validation_out.get("repair_attempts", {})
    _assert(validation_out.get("next_agent") == "code", f"Failed validation did not route to Code: {validation_out}")
    _assert(not validation_out["tool_result"].get("ok"), f"Validation unexpectedly passed: {validation_out}")
    _assert(failure.get("file") == "_langgraph_smoke/test_failure_capture.py", f"Failure file not captured: {failure}")
    _assert(bool(attempts), f"Repair attempts were not incremented: {validation_out}")
    print("LANGGRAPH_FAILURE_CAPTURE_OK")

    _cleanup(SMOKE_DIR)


def main() -> int:
    app = build_graph()
    graph_type = type(app).__name__
    print(f"LANGGRAPH_COMPILE_OK graph={graph_type}")

    state = {
        "user_task": "compile smoke only",
        "messages": [{"role": "user", "content": "compile smoke only"}],
        "next_agent": "research",
        "step_count": 0,
        "max_steps": 1,
        "errors": [],
        "required_files": [],
        "missing_files": [],
        "files_modified": [],
        "tests_run": [],
        "role_outputs": {},
        "repeated_tool_calls": {},
        "json_retries": {},
        "role_visits": {},
        "subtask_visits": {},
        "last_failure": {},
        "repair_attempts": {},
    }
    print(json.dumps({"state_keys": sorted(state)}, ensure_ascii=False))
    _exercise_failure_capture_and_repair_guard()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
