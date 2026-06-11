from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.safety.permission_agent import PermissionAgent
from agents.safety.prompt_injection_agent import PromptInjectionAgent
from agents.safety.risk_agent import RiskAgent
from agents.safety.tool_scope_agent import ToolScopeAgent


@dataclass
class SafetyDepartment:
    """Phase-6 safety gate for global-supervisor plans."""

    run_coding: bool = False
    research_use_tools: bool = False

    def run(
        self,
        *,
        user_request: str,
        route_decision: dict[str, Any],
        execution_plan: list[dict[str, Any]],
    ) -> dict[str, Any]:
        permission = PermissionAgent(
            run_coding=self.run_coding,
            research_use_tools=self.research_use_tools,
        ).run(route_decision)
        risk = RiskAgent().run(route_decision)
        injection = PromptInjectionAgent().run(user_request)
        tool_scope = ToolScopeAgent().run(execution_plan)

        blocked = injection["status"] == "blocked" or tool_scope["status"] == "blocked"
        return {
            "department": "safety",
            "status": "blocked" if blocked else "pass",
            "risk": risk.get("risk", "unknown"),
            "permission": permission,
            "risk_report": risk,
            "prompt_injection": injection,
            "tool_scope": tool_scope,
            "notes": self._notes(permission, risk, injection, tool_scope),
        }

    def _notes(
        self,
        permission: dict[str, Any],
        risk: dict[str, Any],
        injection: dict[str, Any],
        tool_scope: dict[str, Any],
    ) -> list[str]:
        notes = []
        notes.extend(permission.get("mode_notes", []))
        notes.extend(risk.get("reasons", []))
        if injection.get("status") == "blocked":
            notes.append(injection.get("reason", "Prompt injection blocked."))
        if tool_scope.get("status") == "blocked":
            notes.append("Execution plan contains unknown or disallowed department scope.")
        return notes
