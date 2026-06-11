from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RiskAgent:
    """Classifies operational risk for a planned global-supervisor route."""

    def run(self, route_decision: dict[str, Any]) -> dict[str, Any]:
        needs_repo = bool(route_decision.get("needs_repo"))
        needs_code = bool(route_decision.get("needs_code"))
        needs_web = bool(route_decision.get("needs_web"))
        intent = str(route_decision.get("intent", ""))

        risk = "low"
        reasons = []
        if needs_web:
            risk = "medium"
            reasons.append("Plan may use network or external content.")
        if needs_repo or needs_code:
            risk = "medium"
            reasons.append("Plan may use repo or code tools.")
        if intent in {"AGENT_CREATION", "MIXED_TASK", "PRODUCT_BUILD_TASK"} and needs_code:
            risk = "medium"
            reasons.append("Plan may alter agent/runtime capability.")
        if intent == "PRODUCT_BUILD_TASK":
            risk = "medium"
            reasons.append("Plan may write Software Factory artifacts and prepare a code handoff.")

        return {
            "agent": "risk_agent",
            "risk": risk,
            "reasons": reasons or ["No repo, code, write, or network need detected."],
        }
