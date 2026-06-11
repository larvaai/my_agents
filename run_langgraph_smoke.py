from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import orchestration.langgraph_orchestrator as lgo
from orchestration.langgraph_orchestrator import (
    _extract_required_files,
    _forced_test_action,
    _validation_complete,
    build_graph,
    make_tool_node,
)
from core.runtime_paths import WORKSPACE_DIR
from core.capabilities import call_tool
from core.schemas import capability_get


SMOKE_NAME = f"_langgraph_smoke_{os.getpid()}"
COMPLEX_SMOKE_NAME = f"_langgraph_smoke_complex_{os.getpid()}"
FALLBACK_SMOKE_NAME = f"_langgraph_smoke_fallback_{os.getpid()}"
SMOKE_DIR = WORKSPACE_DIR / SMOKE_NAME
COMPLEX_SMOKE_DIR = WORKSPACE_DIR / COMPLEX_SMOKE_NAME
FALLBACK_SMOKE_DIR = WORKSPACE_DIR / FALLBACK_SMOKE_NAME


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
            "path": f"{SMOKE_NAME}/failing.py",
            "lines": ["value = 1"],
            "overwrite": True,
        },
    )
    _assert(bool(created.get("ok")), f"Failed to create repair guard file: {created}")

    repair_state = {
        "tool_name": "file_editor.file_editor_write_lines",
        "tool_args": {
            "path": f"{SMOKE_NAME}/failing.py",
            "lines": ["value = 2"],
            "overwrite": True,
        },
        "last_agent": "code",
        "last_failure": {
            "file": f"{SMOKE_NAME}/failing.py",
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
        capability_get(repair_out["tool_result"], "policy_code") == "repair_requires_patch_tool",
        f"Whole-file repair rewrite was not blocked: {repair_out['tool_result']}",
    )
    _assert(repair_out.get("next_agent") == "code", f"Repair guard routed incorrectly: {repair_out}")
    print("LANGGRAPH_REPAIR_GUARD_OK")

    failing_test = call_tool(
        "file_editor.file_editor_write_lines",
        {
            "path": f"{SMOKE_NAME}/test_failure_capture.py",
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
            "path": f"{SMOKE_NAME}/test_failure_capture.py",
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
    _assert(failure.get("file") == f"{SMOKE_NAME}/test_failure_capture.py", f"Failure file not captured: {failure}")
    _assert(bool(attempts), f"Repair attempts were not incremented: {validation_out}")
    print("LANGGRAPH_FAILURE_CAPTURE_OK")

    _cleanup(SMOKE_DIR)


def _exercise_complex_project_guards() -> None:
    prompt = """
    Build project `society_sim_complex`.

    Required files:
    society_sim_complex/__init__.py
    society_sim_complex/constants.py
    society_sim_complex/models.py
    society_sim_complex/autonomy.py
    society_sim_complex/cli_demo.py
    society_sim_complex/test_society_sim_complex.py

    Example command, not a required project file:
    python main_langgraph.py prompts/the_sims_complex_prompt.md

    Placeholder examples, not required files:
    path/to/file.py
    path/to/test.py

    Acceptance markers:
    SOCIETY_SIM_COMPLEX_TESTS_OK
    SOCIETY_SIM_COMPLEX_DEMO_OK
    """.strip()
    required = _extract_required_files(prompt)
    _assert("society_sim_complex/__init__.py" in required, required)
    _assert("society_sim_complex/autonomy.py" in required, required)
    _assert("society_sim_complex/test_society_sim_complex.py" in required, required)
    _assert("constants.py" not in required, required)
    _assert("main_langgraph.py" not in required, required)
    _assert("path/to/file.py" not in required, required)

    state = {
        "user_task": prompt,
        "required_files": required,
        "tests_run": [
            {
                "ok": True,
                "path": "society_sim_complex/test_society_sim_complex.py",
                "stdout": "SOCIETY_SIM_COMPLEX_TESTS_OK\n",
            }
        ],
    }
    _assert(not _validation_complete(state), "validation should require complex cli demo marker")
    forced = _forced_test_action(state)
    _assert(forced is not None, "cli demo action should be forced after tests")
    _assert(forced["args"]["path"] == "society_sim_complex/cli_demo.py", forced)

    state["tests_run"].append(
        {
            "ok": True,
            "path": "society_sim_complex/cli_demo.py",
            "stdout": "SOCIETY_SIM_COMPLEX_DEMO_OK\n",
        }
    )
    _assert(_validation_complete(state), "complex validation should pass after test and demo markers")

    _cleanup(COMPLEX_SMOKE_DIR)
    scoped_state = {
        "tool_name": "file_editor.file_editor_write_lines",
        "tool_args": {
            "path": "__init__.py",
            "lines": ["# package marker"],
            "overwrite": True,
        },
        "last_agent": "code",
        "messages": [],
        "repeated_tool_calls": {},
        "files_modified": [],
        "tests_run": [],
        "last_failure": {},
        "repair_attempts": {},
        "required_files": [f"{COMPLEX_SMOKE_NAME}/__init__.py"],
        "step_count": 0,
    }
    scoped_out = make_tool_node()(scoped_state)
    _assert(scoped_out["tool_result"].get("ok") is True, scoped_out)
    _assert(
        f"{COMPLEX_SMOKE_NAME}/__init__.py" in scoped_out.get("files_modified", []),
        scoped_out,
    )
    _assert((COMPLEX_SMOKE_DIR / "__init__.py").exists(), scoped_out)
    _cleanup(COMPLEX_SMOKE_DIR)
    print("LANGGRAPH_COMPLEX_PROJECT_GUARDS_OK")


def _exercise_json_retry_reset_after_valid_action() -> None:
    class FakeAgent:
        def run(self, messages: list[dict[str, str]]) -> str:
            return json.dumps(
                {
                    "action": "final",
                    "finish_reason": "handoff",
                    "message": "valid action after earlier JSON errors",
                }
            )

    original_get_agent = lgo.get_agent
    lgo.get_agent = lambda role: FakeAgent()  # type: ignore[assignment]
    try:
        state = {
            "user_task": "noop",
            "messages": [{"role": "user", "content": "noop"}],
            "step_count": 0,
            "max_steps": 10,
            "errors": [],
            "required_files": [],
            "missing_files": [],
            "files_modified": ["society_sim_complex/models.py"],
            "tests_run": [],
            "role_outputs": {},
            "repeated_tool_calls": {},
            "json_retries": {"code": 2},
            "role_visits": {},
            "subtask_visits": {},
            "last_failure": {},
            "repair_attempts": {},
        }
        out = lgo.make_role_node("code")(state)
    finally:
        lgo.get_agent = original_get_agent  # type: ignore[assignment]

    _assert(out.get("json_retries", {}).get("code") == 0, out)
    _assert(out.get("next_agent") == "test", out)
    print("LANGGRAPH_JSON_RETRY_RESET_OK")


def _exercise_json_retry_test_file_fallback() -> None:
    _cleanup(FALLBACK_SMOKE_DIR)
    created = call_tool(
        "file_editor.file_editor_write_lines",
        {
            "path": f"{FALLBACK_SMOKE_NAME}/core.py",
            "lines": ["VALUE = 1"],
            "overwrite": True,
        },
    )
    _assert(bool(created.get("ok")), f"Failed to create fallback core file: {created}")

    class UnexpectedAgent:
        def run(self, messages: list[dict[str, str]]) -> str:
            raise AssertionError("Code LLM should not be called for deterministic test fallback")

    original_get_agent = lgo.get_agent
    lgo.get_agent = lambda role: UnexpectedAgent()  # type: ignore[assignment]
    try:
        state = {
            "user_task": "Build project with FALLBACK_TESTS_OK marker.",
            "messages": [{"role": "user", "content": "noop"}],
            "step_count": 0,
            "max_steps": 10,
            "errors": [],
            "required_files": [
                f"{FALLBACK_SMOKE_NAME}/core.py",
                f"{FALLBACK_SMOKE_NAME}/test_generated.py",
            ],
            "missing_files": [],
            "files_modified": [f"{FALLBACK_SMOKE_NAME}/core.py"],
            "tests_run": [],
            "role_outputs": {},
            "repeated_tool_calls": {},
            "json_retries": {},
            "role_visits": {},
            "subtask_visits": {},
            "last_failure": {},
            "repair_attempts": {},
        }
        out = lgo.make_role_node("code")(state)
    finally:
        lgo.get_agent = original_get_agent  # type: ignore[assignment]

    tool_args = out.get("tool_args", {})
    lines = tool_args.get("lines", []) if isinstance(tool_args, dict) else []
    _assert(out.get("next_agent") == "tool", out)
    _assert(out.get("tool_name") == "file_editor.file_editor_write_lines", out)
    _assert(tool_args.get("path") == f"{FALLBACK_SMOKE_NAME}/test_generated.py", out)
    _assert(out.get("json_retries", {}).get("code") == 0, out)
    _assert(any("FALLBACK_TESTS_OK" in line for line in lines), out)

    tool_state = {
        **state,
        "last_agent": "code",
        "tool_name": out["tool_name"],
        "tool_args": tool_args,
        "repeated_tool_calls": {},
    }
    tool_out = make_tool_node()(tool_state)
    _assert(tool_out["tool_result"].get("ok") is True, tool_out)

    run_result = call_tool(
        "python.run_python",
        {"path": f"{FALLBACK_SMOKE_NAME}/test_generated.py", "timeout": 30},
    )
    _assert(run_result.get("ok") is True, run_result)
    _assert("FALLBACK_TESTS_OK" in capability_get(run_result, "stdout", ""), run_result)

    broken = call_tool(
        "file_editor.file_editor_write_lines",
        {
            "path": f"{FALLBACK_SMOKE_NAME}/test_generated.py",
            "lines": ["from nowhere import Missing", "", "print(Missing)"],
            "overwrite": True,
        },
    )
    _assert(bool(broken.get("ok")), f"Failed to create broken test fixture: {broken}")

    repair_state = {
        **state,
        "files_modified": [
            f"{FALLBACK_SMOKE_NAME}/core.py",
            f"{FALLBACK_SMOKE_NAME}/test_generated.py",
        ],
        "last_failure": {
            "file": f"{FALLBACK_SMOKE_NAME}/test_generated.py",
            "line": 1,
            "error": "ImportError: cannot import name 'Missing'",
        },
        "repair_attempts": {
            f"{FALLBACK_SMOKE_NAME}/test_generated.py:1:ImportError": 1,
        },
        "role_visits": {},
        "subtask_visits": {},
    }
    lgo.get_agent = lambda role: UnexpectedAgent()  # type: ignore[assignment]
    try:
        repair_out = lgo.make_role_node("code")(repair_state)
    finally:
        lgo.get_agent = original_get_agent  # type: ignore[assignment]

    repair_args = repair_out.get("tool_args", {})
    _assert(repair_out.get("next_agent") == "tool", repair_out)
    _assert(repair_out.get("parsed_action", {}).get("reason") == "fallback_test_file_after_validation_failure", repair_out)
    _assert(repair_args.get("path") == f"{FALLBACK_SMOKE_NAME}/test_generated.py", repair_out)

    repair_tool_out = make_tool_node()(
        {
            **repair_state,
            "last_agent": "code",
            "parsed_action": repair_out["parsed_action"],
            "tool_name": repair_out["tool_name"],
            "tool_args": repair_args,
            "repeated_tool_calls": {},
        }
    )
    _assert(repair_tool_out["tool_result"].get("ok") is True, repair_tool_out)

    repaired_run = call_tool(
        "python.run_python",
        {"path": f"{FALLBACK_SMOKE_NAME}/test_generated.py", "timeout": 30},
    )
    _assert(repaired_run.get("ok") is True, repaired_run)
    _assert("FALLBACK_TESTS_OK" in capability_get(repaired_run, "stdout", ""), repaired_run)
    _cleanup(FALLBACK_SMOKE_DIR)
    print("LANGGRAPH_TEST_FILE_FALLBACK_OK")


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
    _exercise_complex_project_guards()
    _exercise_json_retry_reset_after_valid_action()
    _exercise_json_retry_test_file_fallback()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
