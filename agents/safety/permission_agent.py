from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PermissionAgent:
    """Determines whether a plan can run in the current supervisor mode."""

    run_coding: bool = False
    research_use_tools: bool = False

    def run(self, route_decision: dict[str, Any]) -> dict[str, Any]:
        intent = route_decision.get("intent")
        needs_code = bool(route_decision.get("needs_code"))
        needs_web = bool(route_decision.get("needs_web"))

        approvals_required = []
        if needs_code and not self.run_coding:
            approvals_required.append("coding_execution")
        if needs_web and not self.research_use_tools:
            approvals_required.append("network_research")

        return {
            "agent": "permission_agent",
            "allowed": True,
            "intent": intent,
            "approvals_required": approvals_required,
            "mode_notes": [
                "Code execution will be delegated, not run, unless run_coding=True."
                if "coding_execution" in approvals_required
                else "Code execution mode is enabled or not needed.",
                "Network research will stay deterministic unless research_use_tools=True."
                if "network_research" in approvals_required
                else "Network research mode is enabled or not needed.",
            ],
        }
