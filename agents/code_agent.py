from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agents.lenses import CODE_LENSES
from agents.lenses.base_lens import LensResult, lens_results_to_dict, run_prompt_lens, safe_json_dumps
from tools.tool_registry import call_tool


VERSION = "v0.5"
CODE_EXECUTOR_ALLOWED_TOOLS = {
    "file_editor.file_editor_write_lines",
    "file_editor.file_editor_create",
}


@dataclass(frozen=True)
class CodeTaskShape:
    path: str
    sentinel: str


def _normalize_workspace_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip().strip("`'\"")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("workspace/"):
        normalized = normalized.removeprefix("workspace/")
    return normalized


def _extract_task_shape(task: str) -> CodeTaskShape:
    path = "code/lens_smoke_test.py"
    for match in re.finditer(r"(?<![A-Za-z0-9_./\\-])([A-Za-z0-9_./\\-]+\.py)(?![A-Za-z0-9_./\\-])", task):
        candidate = _normalize_workspace_path(match.group(1))
        if candidate.endswith(".py") and not candidate.rsplit("/", 1)[-1].startswith("test_"):
            path = candidate
            break

    sentinel = "CODE_TEST_LENS_OK"
    sentinel_match = re.search(r"\b([A-Z][A-Z0-9_]{4,}_OK)\b", task)
    if sentinel_match:
        sentinel = sentinel_match.group(1)

    return CodeTaskShape(path=path, sentinel=sentinel)


def _safe_tool_call(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = call_tool(tool, args)
        if isinstance(result, dict):
            return result
        return {"ok": False, "tool": tool, "error": "Tool returned non-dict result.", "raw": str(result)}
    except Exception as exc:
        return {"ok": False, "tool": tool, "error": str(exc)}


class CodeAgent:
    """
    v0.5 Engineering Department.

    This class skips the earlier staged versions and exposes the complete v0.5
    behavior directly: lens report, synthesis, gated executor, ledger/issue
    recording, and routing decision.
    """

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(self, task: str, context: dict[str, Any] | None = None) -> list[LensResult]:
        context = context or {}
        shape = _extract_task_shape(task)
        deterministic = {
            "implementation": {
                "lens": "implementation",
                "files_to_modify": [shape.path],
                "implementation_steps": [
                    "Create the requested Python file with a small executable main function.",
                    "Keep generated content compact and JSON-safe.",
                ],
                "notes": ["Use file_editor tools, not terminal editing."],
                "confidence": "high",
            },
            "integration": {
                "lens": "integration",
                "integration_points": ["workspace Python sandbox", "Test Agent python.run_python"],
                "required_config_updates": [],
                "compatibility_notes": ["Path is workspace-relative."],
                "confidence": "high",
            },
            "defensive_coding": {
                "lens": "defensive_coding",
                "failure_modes": ["invalid path", "malformed JSON payload", "test file missing"],
                "guards_to_add": ["executor tool allowlist", "workspace-relative path normalization"],
                "error_messages": ["Execution tool failure is routed back to Code Agent."],
                "confidence": "high",
            },
            "refactor_discipline": {
                "lens": "refactor_discipline",
                "refactor_needed": False,
                "safe_refactors": [],
                "forbidden_refactors": ["unrelated repository cleanup", "git mutation"],
                "confidence": "high",
            },
            "developer_experience": {
                "lens": "developer_experience",
                "readability_notes": ["Generated file has an obvious sentinel print."],
                "naming_notes": [f"Target file: {shape.path}"],
                "docs_needed": ["Document v0.5 runner and smoke commands."],
                "confidence": "high",
            },
        }

        results: list[LensResult] = []
        payload = {"task": task, "context": context, "version": self.version}
        for spec in CODE_LENSES:
            if self.use_llm:
                result = run_prompt_lens(
                    spec.name,
                    spec.to_prompt_block(),
                    payload,
                    model=self.model,
                )
                if result.ok:
                    results.append(result)
                    continue

            data = deterministic.get(spec.name, {"lens": spec.name, "notes": [], "confidence": "medium"})
            results.append(LensResult(lens=spec.name, ok=True, data=data))
        return results

    def synthesize(
        self,
        task: str,
        context: dict[str, Any],
        lens_results: list[LensResult],
    ) -> dict[str, Any]:
        shape = _extract_task_shape(task)
        return {
            "agent": "code_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": "ready_to_execute",
            "implementation_plan": [
                f"Write {shape.path}.",
                f"Include sentinel output {shape.sentinel}.",
                "Hand off to Test Agent for python.run_python validation.",
            ],
            "files_to_modify": [shape.path],
            "tests_to_run_after": [{"path": shape.path, "timeout": 10}],
            "risks": [
                "Local LLM may request broader work than needed; v0.5 executor keeps this task narrow.",
            ],
            "scope_limits": ["No git mutation", "No terminal editing", "No unrelated file changes"],
            "confidence": "high",
            "lens_summary": lens_results_to_dict(lens_results),
        }

    def build_executor_plan(self, task: str, synthesis: dict[str, Any]) -> dict[str, Any]:
        shape = _extract_task_shape(task)
        lines = [
            "from __future__ import annotations",
            "",
            "",
            "def main() -> None:",
            f"    print('{shape.sentinel}')",
            "",
            "",
            "if __name__ == '__main__':",
            "    main()",
        ]
        return {
            "lens": "code_executor",
            "files_to_write": [
                {
                    "path": shape.path,
                    "lines": lines,
                    "overwrite": True,
                    "trailing_newline": True,
                }
            ],
            "tests_to_run": [{"path": shape.path, "timeout": 10, "expected_stdout": shape.sentinel}],
            "notes": ["Executor uses an explicit tool allowlist."],
            "confidence": "high",
        }

    def execute(self, executor_plan: dict[str, Any]) -> dict[str, Any]:
        tool_results: list[dict[str, Any]] = []
        for item in executor_plan.get("files_to_write", []):
            if not isinstance(item, dict):
                tool_results.append({"ok": False, "error": "Invalid files_to_write item.", "item": item})
                continue
            tool = "file_editor.file_editor_write_lines"
            if tool not in CODE_EXECUTOR_ALLOWED_TOOLS:
                tool_results.append({"ok": False, "tool": tool, "error": "Tool not allowed."})
                continue
            args = {
                "path": item.get("path"),
                "lines": item.get("lines", []),
                "overwrite": bool(item.get("overwrite", True)),
                "trailing_newline": bool(item.get("trailing_newline", True)),
            }
            tool_results.append(_safe_tool_call(tool, args))

        ok = all(result.get("ok", False) for result in tool_results) if tool_results else False
        return {
            "ok": ok,
            "stage": "executed",
            "tool_results": tool_results,
        }

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
                    "entry_type": "agent_run",
                    "title": "Code Agent v0.5 run",
                    "data": {
                        "task": task,
                        "decision": synthesis.get("decision"),
                        "execution_ok": execution.get("ok"),
                        "files_to_modify": synthesis.get("files_to_modify", []),
                    },
                    "tags": ["v0.5", "code_agent"],
                },
            )
        ]

        if not execution.get("ok"):
            records.append(
                _safe_tool_call(
                    "issue.issue_create",
                    {
                        "title": "Code Agent v0.5 execution failed",
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
                        "labels": ["agent", "v0.5", "code"],
                        "related_files": synthesis.get("files_to_modify", []),
                    },
                )
            )

        return {"ok": True, "stage": "recorded", "records": records}

    def route_decision(self, synthesis: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
        if synthesis.get("decision") in {"blocked", "needs_more_info"}:
            return {"next_agent": "planner_agent", "reason": "Code Agent needs planning input."}
        if not execution.get("ok"):
            return {"next_agent": "code_agent", "reason": "Code executor failed; retry Code Agent."}
        return {"next_agent": "test_agent", "reason": "Implementation is ready for QA validation."}

    def run(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        lens_results = self.run_lenses(task, context)
        synthesis = self.synthesize(task, context, lens_results)
        executor_plan = self.build_executor_plan(task, synthesis)
        execution = self.execute(executor_plan)
        records = self.record_to_ledger_or_issue(task, synthesis, execution)
        route = self.route_decision(synthesis, execution)
        return {
            "agent": "code_agent",
            "version": self.version,
            "lens_results": lens_results_to_dict(lens_results),
            "synthesis": synthesis,
            "executor_plan": executor_plan,
            "execution": execution,
            "records": records,
            "route": route,
        }
