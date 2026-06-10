from __future__ import annotations

from typing import Any

from agents.department_v05 import VERSION, append_ledger, result_payload, run_lenses
from agents.lenses import PLANNER_LENSES


class PlannerAgent:
    """v0.5 Planning Department runtime."""

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(self, task: str, context: dict[str, Any]) -> list:
        milestones = ["research", "architecture", "implementation", "validation", "review", "ledger", "final"]
        deterministic = {
            "product_manager": {
                "lens": "product_manager",
                "user_goal": task,
                "success_criteria": [
                    "A scoped implementation exists.",
                    "The implementation is validated by QA.",
                    "Review and final communication are based on evidence.",
                ],
                "must_have": ["code/test/review loop", "finish gate"],
                "nice_to_have": ["LLM-generated lens details"],
                "confidence": "high",
            },
            "project_manager": {
                "lens": "project_manager",
                "milestones": milestones,
                "tasks": [
                    "prepare evidence",
                    "define architecture",
                    "implement narrowly",
                    "run validation",
                    "review and record",
                ],
                "execution_order": milestones,
                "confidence": "high",
            },
            "dependency_planner": {
                "lens": "dependency_planner",
                "dependencies": ["Research result before plan", "Architecture before Code", "Code before Test"],
                "blocked_tasks": [],
                "parallelizable_tasks": ["Ledger can record after each department run"],
                "confidence": "high",
            },
            "risk_manager": {
                "lens": "risk_manager",
                "risks": ["model may drift outside role", "tests may be too broad or too weak"],
                "mitigations": ["deterministic route gates", "narrow allowlisted executors", "finish gate"],
                "requires_human_approval": [],
                "confidence": "high",
            },
            "scope_control": {
                "lens": "scope_control",
                "in_scope": ["run full v0.5 company chain", "produce evidence", "record outcome"],
                "out_of_scope": ["git commit", "broad unrelated refactor"],
                "scope_warnings": [],
                "confidence": "high",
            },
        }
        return run_lenses(
            lenses=PLANNER_LENSES,
            task=task,
            context=context,
            deterministic=deterministic,
            use_llm=self.use_llm,
            model=self.model,
        )

    def synthesize(self, task: str, context: dict[str, Any], lens_results: list) -> dict[str, Any]:
        return {
            "agent": "planner_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": "ready_for_architecture",
            "summary": "Plan is scoped and ready for architecture.",
            "milestones": ["research", "architecture", "implementation", "validation", "review", "ledger", "final"],
            "quality_gates": ["Code execution ok", "QA validation ok", "Review approves"],
            "confidence": "high",
        }

    def run(
        self,
        task: str,
        research_result: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = {**(context or {}), "research_result": research_result or {}}
        lens_results = self.run_lenses(task, context)
        synthesis = self.synthesize(task, context, lens_results)
        records = {
            "ok": True,
            "stage": "recorded",
            "records": [
                append_ledger(
                    agent="planner_agent",
                    title="Planner Agent v0.5 run",
                    task=task,
                    synthesis=synthesis,
                )
            ],
        }
        return result_payload(
            agent="planner_agent",
            lens_results=lens_results,
            synthesis=synthesis,
            records=records,
            next_agent="architect_agent",
            reason="Plan is scoped and ready for architecture.",
        )
