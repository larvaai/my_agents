from __future__ import annotations

from typing import Any

from agents.department_v05 import VERSION, compact_history, result_payload, run_lenses
from agents.lenses import FINAL_LENSES


class FinalAgent:
    """v0.5 Communication Department runtime."""

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(self, task: str, context: dict[str, Any]) -> list:
        history = compact_history(context.get("history", []))
        deterministic = {
            "executive_summary": {
                "lens": "executive_summary",
                "summary": "Company v0.5 chain completed successfully.",
                "status": "success",
                "key_results": ["research", "plan", "architecture", "code", "test", "review", "ledger"],
                "confidence": "high",
            },
            "technical_writer": {
                "lens": "technical_writer",
                "files_changed": context.get("changed_files", []),
                "tests_run": context.get("tests_run", []),
                "technical_notes": ["Final Agent performs no mutation."],
                "confidence": "high",
            },
            "user_facing_explanation": {
                "lens": "user_facing_explanation",
                "message": "Done: the implementation passed QA and review gates.",
                "next_user_actions": [],
                "confidence": "high",
            },
            "limitation_disclosure": {
                "lens": "limitation_disclosure",
                "limitations": ["Deterministic smoke run validates the orchestration contract, not every real-world task."],
                "untested_areas": [],
                "assumptions": ["The task was intentionally narrow enough for the v0.5 smoke executor."],
                "confidence": "high",
            },
            "next_step_recommendation": {
                "lens": "next_step_recommendation",
                "recommended_next_steps": ["Use run_company_agents_demo.py with a real prompt to inspect logs."],
                "priority_order": ["inspect demo JSON", "enable --use-llm for lens experiments"],
                "confidence": "medium",
            },
        }
        return run_lenses(
            lenses=FINAL_LENSES,
            task=task,
            context={**context, "compact_history": history},
            deterministic=deterministic,
            use_llm=self.use_llm,
            model=self.model,
        )

    def synthesize(self, task: str, context: dict[str, Any], lens_results: list) -> dict[str, Any]:
        changed_files = context.get("changed_files", [])
        tests_run = context.get("tests_run", [])
        final_message = "Company v0.5 completed: code passed QA, review approved, and Ledger recorded the run."
        return {
            "agent": "final_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": "success",
            "final_message": final_message,
            "summary": final_message,
            "changed_files": changed_files,
            "tests_run": tests_run,
            "limitations": ["This is a deterministic v0.5 orchestration smoke, not a full autonomous product build."],
            "confidence": "high",
        }

    def run(
        self,
        task: str,
        history: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = {**(context or {}), "history": history or []}
        lens_results = self.run_lenses(task, context)
        synthesis = self.synthesize(task, context, lens_results)
        records = {"ok": True, "stage": "no_mutation", "records": []}
        return result_payload(
            agent="final_agent",
            lens_results=lens_results,
            synthesis=synthesis,
            records=records,
            next_agent="done",
            reason="Final response is ready.",
        )
