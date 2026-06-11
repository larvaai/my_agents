from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DEPARTMENT_TOOL_SCOPES: dict[str, dict[str, bool]] = {
    "knowledge": {"can_write_files": False, "can_run_code": False, "can_use_network": False},
    "research": {"can_write_files": False, "can_run_code": False, "can_use_network": True},
    "software_factory": {"can_write_files": True, "can_run_code": False, "can_use_network": False},
    "coding": {"can_write_files": True, "can_run_code": True, "can_use_network": False},
    "agent_factory": {"can_write_files": True, "can_run_code": True, "can_use_network": False},
    "planning": {"can_write_files": False, "can_run_code": False, "can_use_network": False},
    "writing": {"can_write_files": False, "can_run_code": False, "can_use_network": False},
    "final_synthesis": {"can_write_files": False, "can_run_code": False, "can_use_network": False},
}


@dataclass
class ToolScopeAgent:
    """Checks department-level tool boundaries for an execution plan."""

    def run(self, steps: list[dict[str, Any]]) -> dict[str, Any]:
        violations = []
        scopes = []
        for step in steps:
            department = str(step.get("department", ""))
            scope = DEPARTMENT_TOOL_SCOPES.get(department)
            if scope is None:
                violations.append({"department": department, "reason": "Unknown department scope."})
                continue
            scopes.append({"department": department, **scope})

        return {
            "agent": "tool_scope_agent",
            "status": "pass" if not violations else "blocked",
            "violations": violations,
            "scopes": scopes,
        }
