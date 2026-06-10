from __future__ import annotations

from typing import Any

from agents.department_v05 import VERSION, append_ledger, result_payload, run_lenses
from agents.lenses import ARCHITECT_LENSES


class ArchitectAgent:
    """v0.5 Architecture Department runtime."""

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(self, task: str, context: dict[str, Any]) -> list:
        deterministic = {
            "system_architect": {
                "lens": "system_architect",
                "modules": ["agents", "orchestration", "workspace"],
                "responsibilities": [
                    "agents synthesize department decisions",
                    "orchestration routes by explicit gates",
                    "workspace contains generated task artifacts",
                ],
                "boundaries": ["Code mutates workspace files", "Test validates without editing"],
                "confidence": "high",
            },
            "data_architect": {
                "lens": "data_architect",
                "entities": ["department result", "lens result", "route decision", "ledger entry"],
                "schemas": ["dict payloads with agent/version/synthesis/route"],
                "state_rules": ["Only move forward after gate evidence is present."],
                "migration_notes": [],
                "confidence": "high",
            },
            "api_contract": {
                "lens": "api_contract",
                "public_interfaces": ["Agent.run(...)", "CompanyOrchestratorV05.run(task)"],
                "input_contracts": ["task is a string", "context is a dict"],
                "output_contracts": ["result contains agent, version, lens_results, synthesis, records, route"],
                "compatibility_risks": [],
                "confidence": "high",
            },
            "security_architect": {
                "lens": "security_architect",
                "threats": ["unbounded shell", "role bypass", "path escape"],
                "security_requirements": ["workspace-only file editor", "tool allowlists", "no git mutation"],
                "blocked_patterns": ["terminal editing", "self-approval by Code Agent"],
                "confidence": "high",
            },
            "scalability": {
                "lens": "scalability",
                "bottlenecks": ["long histories", "large tool results"],
                "scaling_plan": ["compact history between departments", "store durable facts in ledger"],
                "do_not_overengineer": ["avoid extra queues until route gates need them"],
                "confidence": "high",
            },
        }
        return run_lenses(
            lenses=ARCHITECT_LENSES,
            task=task,
            context=context,
            deterministic=deterministic,
            use_llm=self.use_llm,
            model=self.model,
        )

    def synthesize(self, task: str, context: dict[str, Any], lens_results: list) -> dict[str, Any]:
        return {
            "agent": "architect_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": "ready_for_engineering",
            "architecture_summary": "Use explicit department result payloads and route gates.",
            "boundaries": ["Research/Planner/Architect stay read-only for code", "Code edits", "Test validates"],
            "contracts": ["Agent outputs must include route.next_agent and synthesis.decision"],
            "confidence": "high",
        }

    def run(
        self,
        task: str,
        planner_result: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = {**(context or {}), "planner_result": planner_result or {}}
        lens_results = self.run_lenses(task, context)
        synthesis = self.synthesize(task, context, lens_results)
        records = {
            "ok": True,
            "stage": "recorded",
            "records": [
                append_ledger(
                    agent="architect_agent",
                    title="Architect Agent v0.5 run",
                    task=task,
                    synthesis=synthesis,
                )
            ],
        }
        return result_payload(
            agent="architect_agent",
            lens_results=lens_results,
            synthesis=synthesis,
            records=records,
            next_agent="code_agent",
            reason="Architecture is ready for Engineering.",
        )
