from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _first_text(values: list[Any]) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


@dataclass
class FinalSynthesisAgent:
    """
    Single owner of the final user-facing answer in the global supervisor path.

    Departments return structured outputs. This agent turns them into the final
    answer and carries evidence/limits forward.
    """

    name: str = "final_synthesis_agent"
    department: str = "communication"

    def run(
        self,
        *,
        user_request: str,
        route_decision: dict[str, Any],
        department_outputs: dict[str, Any],
        execution_plan: list[dict[str, Any]] | None = None,
        validation_evidence: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
        limits: list[str] | None = None,
    ) -> dict[str, Any]:
        execution_plan = execution_plan or []
        validation_evidence = validation_evidence or []
        citations = citations or []
        limits = limits or []

        final_answer = self._compose_answer(
            user_request=user_request,
            route_decision=route_decision,
            department_outputs=department_outputs,
            validation_evidence=validation_evidence,
            citations=citations,
            limits=limits,
        )
        return {
            "agent": self.name,
            "department": self.department,
            "decision": "final_answer_ready",
            "route_decision": route_decision,
            "execution_plan": execution_plan,
            "department_outputs": department_outputs,
            "validation_evidence": validation_evidence,
            "citations": citations,
            "limits": limits,
            "final_answer": final_answer,
        }

    def _compose_answer(
        self,
        *,
        user_request: str,
        route_decision: dict[str, Any],
        department_outputs: dict[str, Any],
        validation_evidence: list[dict[str, Any]],
        citations: list[dict[str, Any]],
        limits: list[str],
    ) -> str:
        intent = route_decision.get("intent", "UNKNOWN")
        knowledge = department_outputs.get("knowledge", {})
        research = department_outputs.get("research", {})
        software_factory = department_outputs.get("software_factory", {})
        coding = department_outputs.get("coding", {})
        agent_factory = department_outputs.get("agent_factory", {})
        planning = department_outputs.get("planning", {})
        writing = department_outputs.get("writing", {})
        safety = department_outputs.get("safety", {})

        answer = _first_text(
            [
                knowledge.get("answer_draft") if isinstance(knowledge, dict) else "",
                research.get("summary") if isinstance(research, dict) else "",
                software_factory.get("summary") if isinstance(software_factory, dict) else "",
                coding.get("final_message") if isinstance(coding, dict) else "",
                agent_factory.get("summary") if isinstance(agent_factory, dict) else "",
                planning.get("summary") if isinstance(planning, dict) else "",
                writing.get("summary") if isinstance(writing, dict) else "",
                (
                    f"Safety Department {safety.get('status')} the route."
                    if isinstance(safety, dict) and safety.get("status") == "blocked"
                    else ""
                ),
            ]
        )
        if not answer:
            answer = "The request was routed, but no department produced a substantive answer yet."

        lines = [answer]

        if validation_evidence:
            evidence_text = ", ".join(
                str(item.get("command") or item.get("name") or item)
                for item in validation_evidence[:5]
            )
            lines.append(f"Validation evidence: {evidence_text}.")

        if citations:
            citation_text = "; ".join(
                str(item.get("title") or item.get("url_or_path") or item)
                for item in citations[:5]
            )
            lines.append(f"Sources: {citation_text}.")

        if isinstance(software_factory, dict) and software_factory:
            implementation = software_factory.get("implementation_spec") or {}
            handoff = software_factory.get("code_handoff_packet") or {}
            if implementation.get("path"):
                lines.append(f"Implementation spec: {implementation.get('path')}.")
            if handoff.get("path"):
                lines.append(f"Code handoff packet: {handoff.get('path')}.")
            if software_factory.get("next_recommended_command"):
                lines.append(f"Next command: {software_factory.get('next_recommended_command')}.")

        if isinstance(safety, dict) and safety:
            lines.append(f"Safety: {safety.get('status', 'unknown')} risk={safety.get('risk', 'unknown')}.")

        combined_limits = list(limits)
        for output in department_outputs.values():
            if isinstance(output, dict):
                combined_limits.extend(str(item) for item in output.get("limits", [])[:3])
        if combined_limits:
            lines.append("Limits: " + "; ".join(dict.fromkeys(combined_limits[:5])) + ".")

        if intent in {"CODE_TASK", "DEBUG_TASK", "REPO_TASK", "MIXED_TASK"} and coding and not validation_evidence:
            lines.append("No validation command was run in this global-supervisor stage.")
        if intent == "PRODUCT_BUILD_TASK" and software_factory:
            lines.append("No source implementation was executed in this global-supervisor stage.")

        return "\n".join(lines)
