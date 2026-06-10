from __future__ import annotations

from typing import Any

from agents.department_v05 import VERSION, append_ledger, compact_history, result_payload, run_lenses
from agents.lenses import LEDGER_LENSES


class LedgerAgent:
    """v0.5 Ledger / Audit / Operations runtime."""

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(self, task: str, context: dict[str, Any]) -> list:
        history = compact_history(context.get("history", []))
        deterministic = {
            "historian": {
                "lens": "historian",
                "events_to_record": history,
                "summary": "Company v0.5 chain reached Ledger.",
                "confidence": "high",
            },
            "task_state": {
                "lens": "task_state",
                "task_updates": [{"status": "ready_for_final", "reason": "Review approved."}],
                "invalid_transitions": [],
                "confidence": "high",
            },
            "decision_record": {
                "lens": "decision_record",
                "decisions_to_record": ["Use deterministic v0.5 department gates for smoke stability."],
                "adr_needed": False,
                "confidence": "medium",
            },
            "auditor": {
                "lens": "auditor",
                "consistency_status": "pass",
                "inconsistencies": [],
                "repairs_needed": [],
                "confidence": "high",
            },
            "incident_tracker": {
                "lens": "incident_tracker",
                "issues_to_create": [],
                "incidents_to_record": [],
                "severity": "low",
                "confidence": "high",
            },
        }
        return run_lenses(
            lenses=LEDGER_LENSES,
            task=task,
            context=context,
            deterministic=deterministic,
            use_llm=self.use_llm,
            model=self.model,
        )

    def synthesize(self, task: str, context: dict[str, Any], lens_results: list) -> dict[str, Any]:
        return {
            "agent": "ledger_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": "ready_for_final",
            "summary": "Ledger recorded the approved run and found no blocking inconsistency.",
            "history": compact_history(context.get("history", [])),
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
        records = {
            "ok": True,
            "stage": "recorded",
            "records": [
                append_ledger(
                    agent="ledger_agent",
                    title="Ledger Agent v0.5 run",
                    task=task,
                    synthesis=synthesis,
                    extra={"history": synthesis.get("history", [])},
                )
            ],
        }
        return result_payload(
            agent="ledger_agent",
            lens_results=lens_results,
            synthesis=synthesis,
            records=records,
            next_agent="final_agent",
            reason="Audit trail is ready for final user response.",
        )
