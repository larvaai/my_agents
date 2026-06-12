from __future__ import annotations

from typing import Any

from agents.department_v05 import VERSION, result_payload, run_lenses
from agents.lenses import BUSINESS_ANALYST_LENSES


def _short_task(task: str, limit: int = 280) -> str:
    cleaned = " ".join((task or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


class BusinessAnalystAgent:
    """v0.5 prompt-only Business Analysis Department runtime."""

    def __init__(self, *, use_llm: bool = False, model: str | None = None) -> None:
        self.version = VERSION
        self.use_llm = use_llm
        self.model = model

    def run_lenses(self, task: str, context: dict[str, Any]) -> list:
        task_excerpt = _short_task(task)
        deterministic = {
            "problem_framing": {
                "lens": "problem_framing",
                "problem_statement": "The user request must be clarified before technical planning.",
                "business_goal": "Reduce wrong-scope planning and implementation by making intent testable first.",
                "expected_value": "Planner and downstream agents receive scope, requirements, risks, and acceptance signals.",
                "success_metrics": [
                    "requirements are traceable to the user goal",
                    "acceptance criteria are observable as pass/fail",
                    "unknowns and assumptions are not treated as confirmed requirements",
                ],
                "open_questions": ["Which details are mandatory versus acceptable assumptions?"],
                "confidence": "medium",
            },
            "evidence_separation": {
                "lens": "evidence_separation",
                "given_facts": [task_excerpt],
                "inferences": [
                    "The request needs a scoped handoff before planning.",
                    "Missing business context should be marked instead of invented.",
                ],
                "assumptions": [
                    "Planner can proceed with explicit assumptions when the user does not answer clarification questions.",
                ],
                "unknowns": [
                    "confirmed stakeholder list",
                    "final success metric",
                    "hard out-of-scope boundaries",
                ],
                "open_questions": [
                    "Who is the primary user or stakeholder?",
                    "What outcome proves the work is successful?",
                    "What is explicitly out of scope?",
                ],
                "confidence": "medium",
            },
            "stakeholder_mapping": {
                "lens": "stakeholder_mapping",
                "primary_users": ["requesting user"],
                "secondary_users": ["downstream planner", "downstream tester"],
                "business_owner": "Unknown",
                "approvers": ["Unknown"],
                "operators": ["maintainer or project operator"],
                "affected_parties": ["future users", "maintainers", "QA/review roles"],
                "confidence": "medium",
            },
            "scope_control": {
                "lens": "scope_control",
                "in_scope": [
                    "clarify problem, goal, scope, requirements, user stories, and acceptance criteria",
                    "flag assumptions, risks, dependencies, and open questions",
                ],
                "out_of_scope": [
                    "write code",
                    "choose technical stack",
                    "browse external sources",
                    "treat guessed features as confirmed scope",
                ],
                "unknown_scope": ["domain-specific rules not present in the request"],
                "scope_creep_warnings": ["Any feature not stated by the user must remain an assumption or backlog candidate."],
                "confidence": "high",
            },
            "requirement_decomposition": {
                "lens": "requirement_decomposition",
                "business_requirements": [
                    "The system must clarify ambiguous requests before technical planning.",
                    "The handoff must preserve unknowns and assumptions separately from facts.",
                ],
                "user_requirements": [
                    "As a requester, I want my vague goal turned into clear requirements so downstream agents do not invent scope.",
                    "As a Planner Agent, I want a bounded BA handoff so I can create a realistic plan.",
                    "As a Test Agent, I want pass/fail acceptance criteria so I can validate the result.",
                ],
                "functional_requirements": [
                    "Produce given facts, inferences, assumptions, and open questions.",
                    "Produce stakeholder, scope, requirement, story, and acceptance-criteria sections.",
                    "Ask at most five high-value clarification questions when critical information is missing.",
                ],
                "non_functional_requirements": [
                    "Output must be stable enough for another agent to consume.",
                    "Requirements should be atomic, testable, and traceable.",
                ],
                "business_rules": [
                    "Do not convert assumptions into confirmed requirements.",
                    "Do not choose implementation details unless explicitly requested.",
                ],
                "data_requirements": ["Mark required but missing data definitions as Unknown."],
                "permission_requirements": ["Mark access rules as Unknown when not specified."],
                "confidence": "medium",
            },
            "handoff_readiness": {
                "lens": "handoff_readiness",
                "epics": ["Requirement Clarification Gateway"],
                "user_stories": [
                    "As a Planner Agent, I want a BA handoff with scope and requirements so that planning does not start from vague intent.",
                    "As a Test Agent, I want acceptance criteria tied to user stories so that validation can be pass/fail.",
                ],
                "acceptance_criteria": [
                    "Given a vague request, when BA analysis is produced, then it separates facts, inferences, assumptions, and open questions.",
                    "Given generated user stories, when acceptance criteria are listed, then each criterion is observable as pass or fail.",
                ],
                "risks": ["The request may remain underspecified if the user skips clarification."],
                "dependencies": ["Planner must accept BA handoff fields as planning input."],
                "ready_for_planner": True,
                "confidence": "high",
            },
        }
        return run_lenses(
            lenses=BUSINESS_ANALYST_LENSES,
            task=task,
            context=context,
            deterministic=deterministic,
            use_llm=self.use_llm,
            model=self.model,
        )

    def synthesize(self, task: str, context: dict[str, Any], lens_results: list) -> dict[str, Any]:
        return {
            "agent": "business_analyst_agent",
            "version": self.version,
            "stage": "synthesis",
            "decision": "ready_for_planning",
            "summary": "BA gate created a prompt-only requirement handoff for Planner.",
            "handoff": {
                "business_goal": "Clarify user intent before technical planning.",
                "scope": {
                    "in_scope": ["business analysis", "requirement decomposition", "acceptance criteria"],
                    "out_of_scope": ["code implementation", "technical stack selection"],
                    "unknown": ["domain details not present in the task"],
                },
                "requirements": {
                    "business": ["Reduce wrong-scope planning from vague requests."],
                    "functional": ["Produce facts, assumptions, requirements, stories, and pass/fail AC."],
                    "non_functional": ["Output should be stable, concise, and handoff-ready."],
                },
                "assumptions": ["Planner can proceed when assumptions are explicitly labeled."],
                "open_questions": [
                    "Who is the primary stakeholder?",
                    "What success metric matters most?",
                    "What is explicitly out of scope?",
                ],
                "risk_level": "medium",
            },
            "quality_gate": {
                "facts_separated": True,
                "scope_defined": True,
                "requirements_testable": True,
                "acceptance_criteria_present": True,
                "ready_for_planner": True,
            },
            "confidence": "medium",
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
        records = {"ok": True, "stage": "prompt_only_no_mutation", "records": []}
        return result_payload(
            agent="business_analyst_agent",
            lens_results=lens_results,
            synthesis=synthesis,
            records=records,
            next_agent="planner_agent",
            reason="Business analysis handoff is ready for planning.",
        )
