from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PhilosophyAgent:
    """Read-only philosophy specialist for agency, autonomy, ethics, and meaning."""

    name: str = "philosophy_agent"
    department: str = "knowledge"

    def run(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        answer = self._answer(question)
        return {
            "department": self.department,
            "agent": self.name,
            "answer_draft": answer,
            "confidence": "medium",
            "needs_research": False,
            "sources": [],
            "limits": [
                "Deterministic phase-2 philosophy agent; no external scholarship lookup was used.",
            ],
            "tool_permissions": {
                "can_write_files": False,
                "can_run_terminal": False,
                "can_run_python": False,
            },
        }

    def _answer(self, question: str) -> str:
        folded = (question or "").lower()
        if "agency" in folded and "autonomy" in folded:
            return (
                "Agency is the capacity to initiate actions for reasons or goals. Autonomy is a "
                "stronger condition: the agent's actions are self-governed rather than merely caused "
                "by external control. A system can show limited agency without full autonomy."
            )
        if "free will" in folded:
            return (
                "Free will debates ask whether action can be meaningfully authored by the agent under "
                "conditions of causation, constraint, and self-control. Compatibilist views usually "
                "focus on reasons-responsive control rather than freedom from all causes."
            )
        return (
            "A useful philosophical analysis separates concepts, assumptions, and consequences. "
            "For this question, I would first define the key terms, then compare competing views, "
            "then state what follows for the system or decision being discussed."
        )
