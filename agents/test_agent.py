from __future__ import annotations

from typing import Any

from agents.lenses import TEST_LENSES
from agents.lenses.base_lens import LensResult, lens_results_to_dict, run_prompt_lens, safe_json_dumps
from core.capabilities import call_tool
from core.schemas import capability_get


VERSION = "v0.5"
ALLOWED_TEST_EXECUTOR_TOOLS = {
    "python.run_python",
    "lint_test.lint_compile",
    "lint_test.lint_ruff_check",
    "lint_test.lint_ruff_format_check",
    "lint_test.test_python_file",
    "filesystem.read_file",
    "filesystem.read_text_file",
    "git.git_diff_unstaged",
    "code_index.code_index",
    "code_index.code_find_symbol",
    "code_index.code_find_references",
}


def _safe_tool_call(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = call_tool(tool, args)
        if isinstance(result, dict):
            return result
        return {"ok": False, "tool": tool, "error": "Tool returned non-dict result.", "raw": str(result)}
    except Exception as exc:
        return {"ok": False, "tool": tool, "error": str(exc)}


def _code_tests_to_run(code_result: dict[str, Any]) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    executor_plan = code_result.get("executor_plan", {})
    if isinstance(executor_plan, dict):
        for item in executor_plan.get("tests_to_run", []):
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if isinstance(path, str) and path.endswith(".py"):
                tests.append(
                    {
                        "tool": "python.run_python",
                        "args": {"path": path, "timeout": int(item.get("timeout", 10))},
                        "expected_stdout": item.get("expected_stdout"),
                    }
                )

    if tests:
        return tests

    synthesis = code_result.get("synthesis", {})
    if isinstance(synthesis, dict):
        for item in synthesis.get("tests_to_run_after", []):
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if isinstance(path, str) and path.endswith(".py"):
                tests.append(
                    {
                        "tool": "python.run_python",
                        "args": {"path": path, "timeout": int(item.get("timeout", 10))},
                        "expected_stdout": item.get("expected_stdout"),
                    }
                )
    return tests


class TestAgent:
    """
    v0.5 QA Department.

    The Test Agent runs reasoning lenses, synthesizes a test plan, executes only
    allowlisted validation tools, records audit data, then routes by result.
    """

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(
        self,
        task: str,
        code_result: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[LensResult]:
        context = context or {}
        tests = _code_tests_to_run(code_result)
        deterministic = {
            "logic": {
                "lens": "logic",
                "invariants": ["Target Python file executes with returncode 0."],
                "possible_violations": ["file missing", "wrong sentinel output", "runtime error"],
                "must_test": tests,
                "confidence": "high",
            },
            "critical_thinking": {
                "lens": "critical_thinking",
                "hidden_assumptions": ["A created file is not useful unless it actually runs."],
                "adversarial_cases": ["empty stdout", "non-zero return code"],
                "false_pass_risks": ["Tool ok but expected stdout missing."],
                "confidence": "high",
            },
            "experienced_qa": {
                "lens": "experienced_qa",
                "test_strategy": ["Run the exact generated Python entry point."],
                "high_value_tests": tests,
                "low_value_tests_to_skip": ["broad repository lint for a single generated smoke file"],
                "confidence": "high",
            },
            "regression": {
                "lens": "regression",
                "related_old_failures": [],
                "affected_tests": tests,
                "recommended_regression_tests": [],
                "confidence": "medium",
            },
            "edge_case": {
                "lens": "edge_case",
                "edge_cases": ["missing file", "non-zero exit", "stdout without expected sentinel"],
                "boundary_values": ["empty stdout", "timeout at test executor limit"],
                "must_test": tests,
                "confidence": "high",
            },
            "purpose_alignment": {
                "lens": "purpose_alignment",
                "alignment": "pass" if tests else "warning",
                "conceptual_issues": [] if tests else ["No executable test target found."],
                "behavior_that_must_remain_true": ["Expected sentinel must appear in stdout."],
                "confidence": "high",
            },
            "test_executor": {
                "lens": "test_executor",
                "status": "planned",
                "tests_run": tests,
                "passed": None,
                "failures": [],
                "stdout_summary": "pending execution",
                "stderr_summary": "",
            },
        }

        results: list[LensResult] = []
        payload = {
            "task": task,
            "code_result": code_result,
            "context": context,
            "version": self.version,
        }
        for spec in TEST_LENSES:
            if self.use_llm and spec.name != "test_executor":
                result = run_prompt_lens(spec.name, spec.to_prompt_block(), payload, model=self.model)
                if result.ok:
                    results.append(result)
                    continue
            data = deterministic.get(spec.name, {"lens": spec.name, "notes": [], "confidence": "medium"})
            results.append(LensResult(lens=spec.name, ok=True, data=data))
        return results

    def synthesize(
        self,
        task: str,
        code_result: dict[str, Any],
        context: dict[str, Any],
        lens_results: list[LensResult],
    ) -> dict[str, Any]:
        tests = _code_tests_to_run(code_result)
        decision = "ready_to_execute" if tests else "blocked"
        return {
            "agent": "test_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": decision,
            "test_plan": ["Run executable tests produced by Code Agent."] if tests else [],
            "tests_to_run": tests,
            "quality_gates": [
                "returncode must be 0",
                "expected_stdout must be present when provided",
            ],
            "risk_notes": [
                "Do not edit source from QA.",
                "Route failures back to Code Agent with evidence.",
            ],
            "confidence": "high" if tests else "medium",
            "lens_summary": lens_results_to_dict(lens_results),
        }

    def execute_tests(self, synthesis: dict[str, Any]) -> dict[str, Any]:
        test_results: list[dict[str, Any]] = []
        for test in synthesis.get("tests_to_run", []):
            if not isinstance(test, dict):
                test_results.append({"ok": False, "error": "Invalid test item.", "item": test})
                continue
            tool = test.get("tool")
            args = test.get("args", {})
            if tool not in ALLOWED_TEST_EXECUTOR_TOOLS:
                test_results.append(
                    {
                        "ok": False,
                        "tool": tool,
                        "error": "Tool is not allowed for Test Agent executor.",
                        "allowed_tools": sorted(ALLOWED_TEST_EXECUTOR_TOOLS),
                    }
                )
                continue
            if not isinstance(args, dict):
                test_results.append({"ok": False, "tool": tool, "error": "Tool args must be a dict."})
                continue

            result = _safe_tool_call(str(tool), args)
            expected = test.get("expected_stdout")
            if result.get("ok") and isinstance(expected, str) and expected not in str(capability_get(result, "stdout", "")):
                result = {
                    **result,
                    "ok": False,
                    "error": f"Expected stdout token not found: {expected}",
                    "expected_stdout": expected,
                }
            test_results.append(result)

        ok = all(result.get("ok", False) for result in test_results) if test_results else False
        return {"ok": ok, "stage": "tests_executed", "test_results": test_results}

    def record_to_ledger_or_issue(
        self,
        task: str,
        synthesis: dict[str, Any],
        execution: dict[str, Any],
    ) -> dict[str, Any]:
        records = [
            _safe_tool_call(
                "ledger.ledger_append",
                {
                    "entry_type": "test_result",
                    "title": "Test Agent v0.5 run",
                    "data": {
                        "task": task,
                        "decision": synthesis.get("decision"),
                        "execution_ok": execution.get("ok"),
                        "test_count": len(execution.get("test_results", [])),
                    },
                    "tags": ["v0.5", "test_agent"],
                },
            )
        ]

        if not execution.get("ok"):
            records.append(
                _safe_tool_call(
                    "issue.issue_create",
                    {
                        "title": "Test Agent v0.5 quality gate failed",
                        "description": safe_json_dumps(
                            {
                                "task": task,
                                "synthesis": synthesis,
                                "execution": execution,
                            }
                        ),
                        "kind": "bug",
                        "priority": 2,
                        "assignee": "code_agent",
                        "labels": ["agent", "v0.5", "test"],
                        "related_files": [],
                    },
                )
            )

        return {"ok": True, "stage": "recorded", "records": records}

    def route_decision(self, synthesis: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
        if synthesis.get("decision") == "blocked":
            return {"next_agent": "planner_agent", "reason": "Test Agent could not build a validation plan."}
        if not execution.get("ok"):
            return {"next_agent": "code_agent", "reason": "Validation failed; send evidence back to Code Agent."}
        return {"next_agent": "review_agent", "reason": "Validation passed; ready for review."}

    def run(
        self,
        task: str,
        code_result: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = context or {}
        code_result = code_result or {}
        lens_results = self.run_lenses(task, code_result, context)
        synthesis = self.synthesize(task, code_result, context, lens_results)
        execution = self.execute_tests(synthesis)
        records = self.record_to_ledger_or_issue(task, synthesis, execution)
        route = self.route_decision(synthesis, execution)
        return {
            "agent": "test_agent",
            "version": self.version,
            "lens_results": lens_results_to_dict(lens_results),
            "synthesis": synthesis,
            "execution": execution,
            "records": records,
            "route": route,
        }
