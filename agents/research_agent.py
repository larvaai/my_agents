from __future__ import annotations

from typing import Any

from agents.department_v05 import VERSION, result_payload, run_lenses
from agents.lenses import RESEARCH_LENSES


class ResearchAgent:
    """v0.5 Research Department runtime."""

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(self, task: str, context: dict[str, Any]) -> list:
        deterministic = {
            "source_scout": {
                "lens": "source_scout",
                "queries": [task],
                "candidate_sources": context.get("candidate_sources", []),
                "recommended_fetch": [],
                "confidence": "medium",
            },
            "source_credibility": {
                "lens": "source_credibility",
                "accepted_sources": context.get("accepted_sources", []),
                "rejected_sources": [],
                "credibility_notes": ["Deterministic v0.5 run uses supplied context and local code evidence."],
                "confidence": "medium",
            },
            "fact_check": {
                "lens": "fact_check",
                "claims": [{"claim": "Task is ready for planning.", "source": "user_prompt"}],
                "supported_claims": ["User prompt defines the requested outcome."],
                "conflicting_claims": [],
                "uncertain_claims": [],
                "confidence": "high",
            },
            "synthesis": {
                "lens": "synthesis",
                "summary": "Research context prepared for Planning.",
                "key_points": [task],
                "actionable_knowledge": ["Proceed with a bounded plan and explicit validation gate."],
                "sources": context.get("accepted_sources", []),
                "confidence": "high",
            },
            "knowledge_curator": {
                "lens": "knowledge_curator",
                "should_ingest": False,
                "note_path": "",
                "tags": ["v0.5", "research"],
                "reason": "Smoke-oriented run has no durable external source to ingest.",
                "confidence": "medium",
            },
        }
        return run_lenses(
            lenses=RESEARCH_LENSES,
            task=task,
            context=context,
            deterministic=deterministic,
            use_llm=self.use_llm,
            model=self.model,
        )

    def synthesize(self, task: str, context: dict[str, Any], lens_results: list) -> dict[str, Any]:
        return {
            "agent": "research_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": "ready_for_business_analysis",
            "summary": "Research found enough local context for business analysis.",
            "sources": context.get("accepted_sources", []),
            "open_questions": [],
            "confidence": "high",
        }

    def run(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        lens_results = self.run_lenses(task, context)
        synthesis = self.synthesize(task, context, lens_results)
        records = {"ok": True, "stage": "no_mutation", "records": []}
        return result_payload(
            agent="research_agent",
            lens_results=lens_results,
            synthesis=synthesis,
            records=records,
            next_agent="business_analyst_agent",
            reason="Research context is ready for business analysis.",
        )
