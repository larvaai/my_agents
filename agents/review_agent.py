from __future__ import annotations

from typing import Any

from agents.department_v05 import (
    VERSION,
    append_ledger,
    changed_files_from_code_result,
    execution_ok,
    result_payload,
    run_lenses,
    safe_tool_call,
    test_commands_from_test_result,
)
from agents.lenses import REVIEW_LENSES
from agents.lenses.base_lens import safe_json_dumps


class ReviewAgent:
    """v0.5 Senior Review Board runtime."""

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(self, task: str, context: dict[str, Any]) -> list:
        code_result = context.get("code_result", {})
        test_result = context.get("test_result", {})
        files = changed_files_from_code_result(code_result)
        test_ok = execution_ok(test_result)
        deterministic = {
            "senior_engineer": {
                "lens": "senior_engineer",
                "approved": test_ok,
                "issues": [] if test_ok else ["Validation evidence is not passing."],
                "suggested_fixes": [] if test_ok else ["Return to Code Agent with QA evidence."],
                "confidence": "high",
            },
            "scope_diff": {
                "lens": "scope_diff",
                "changed_files": files,
                "out_of_scope_changes": [],
                "scope_status": "ok",
                "confidence": "high",
            },
            "security_review": {
                "lens": "security_review",
                "security_status": "pass",
                "findings": [],
                "must_fix": [],
                "confidence": "medium",
            },
            "maintainability": {
                "lens": "maintainability",
                "maintainability_status": "pass",
                "issues": [],
                "recommendations": ["Keep generated smoke artifacts small and explicit."],
                "confidence": "medium",
            },
            "release_risk": {
                "lens": "release_risk",
                "risk_level": "low" if test_ok else "high",
                "blocking_issues": [] if test_ok else ["QA gate failed."],
                "approval_recommendation": "approve" if test_ok else "request_changes",
                "confidence": "high",
            },
        }
        return run_lenses(
            lenses=REVIEW_LENSES,
            task=task,
            context=context,
            deterministic=deterministic,
            use_llm=self.use_llm,
            model=self.model,
        )

    def synthesize(self, task: str, context: dict[str, Any], lens_results: list) -> dict[str, Any]:
        code_result = context.get("code_result", {})
        test_result = context.get("test_result", {})
        test_ok = execution_ok(test_result)
        decision = "approve" if test_ok else "request_changes"
        return {
            "agent": "review_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": decision,
            "summary": "Review approves the change based on QA evidence." if test_ok else "Review requests changes.",
            "changed_files": changed_files_from_code_result(code_result),
            "tests_reviewed": test_commands_from_test_result(test_result),
            "findings": [] if test_ok else ["QA execution did not pass."],
            "confidence": "high",
        }

    def record_to_ledger_or_issue(self, task: str, synthesis: dict[str, Any]) -> dict[str, Any]:
        records = [
            append_ledger(
                agent="review_agent",
                title="Review Agent v0.5 run",
                task=task,
                synthesis=synthesis,
            )
        ]
        if synthesis.get("decision") != "approve":
            records.append(
                safe_tool_call(
                    "issue.issue_create",
                    {
                        "title": "Review Agent v0.5 requested changes",
                        "description": safe_json_dumps({"task": task, "synthesis": synthesis}),
                        "kind": "bug",
                        "priority": 2,
                        "assignee": "code_agent",
                        "labels": ["agent", "v0.5", "review"],
                        "related_files": synthesis.get("changed_files", []),
                    },
                )
            )
        return {"ok": True, "stage": "recorded", "records": records}

    def run(
        self,
        task: str,
        code_result: dict[str, Any] | None = None,
        test_result: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = {
            **(context or {}),
            "code_result": code_result or {},
            "test_result": test_result or {},
        }
        lens_results = self.run_lenses(task, context)
        synthesis = self.synthesize(task, context, lens_results)
        records = self.record_to_ledger_or_issue(task, synthesis)
        if synthesis.get("decision") == "approve":
            next_agent = "ledger_agent"
            reason = "Review approved; record final state."
        else:
            next_agent = "code_agent"
            reason = "Review requested changes; return to Engineering."
        return result_payload(
            agent="review_agent",
            lens_results=lens_results,
            synthesis=synthesis,
            records=records,
            next_agent=next_agent,
            reason=reason,
        )
