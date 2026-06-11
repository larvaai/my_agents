from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _brief_question(question: str, *, limit: int = 180) -> str:
    text = " ".join((question or "").strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


@dataclass
class GeneralKnowledgeAgent:
    """Read-only deterministic knowledge agent for stable conceptual questions."""

    name: str = "general_knowledge_agent"
    department: str = "knowledge"

    def run(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        answer = self._answer(question, context)
        return {
            "department": self.department,
            "agent": self.name,
            "answer_draft": answer,
            "confidence": "medium",
            "needs_research": False,
            "sources": [],
            "limits": [
                "Deterministic phase-2 knowledge agent; no external search or RAG was used.",
            ],
            "tool_permissions": {
                "can_write_files": False,
                "can_run_terminal": False,
                "can_run_python": False,
            },
        }

    def _answer(self, question: str, context: dict[str, Any]) -> str:
        folded = (question or "").lower()
        if "amygdala" in folded:
            return (
                "Amygdala is a brain structure involved in threat detection, emotional salience, "
                "fear learning, and prioritizing attention toward biologically important signals. "
                "It does not work alone; it interacts with memory, body-state, and control systems."
            )
        if "dopamine" in folded or "goal-gradient" in folded or "goal gradient" in folded:
            return (
                "Goal-gradient describes motivation increasing as a goal feels closer. Dopamine is "
                "often discussed here because reward-prediction and action-selection systems can make "
                "near goals feel more urgent, valuable, and worth pursuing."
            )
        if "rag" in folded:
            return (
                "RAG means retrieval-augmented generation: the system retrieves relevant external or "
                "local knowledge first, then uses that evidence to produce a grounded answer."
            )
        subject = _brief_question(question) or "the requested topic"
        return (
            f"{subject}: this looks like a stable general-knowledge question. "
            "At this stage I can provide a concise conceptual explanation without repo tools. "
            "If the answer needs current facts, the router should send it to Research Department."
        )
