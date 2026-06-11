from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


MUTATING_GIT_TOOLS = {
    "git_add",
    "git_commit",
    "git_reset",
    "git_checkout",
    "git_create_branch",
}


@dataclass(frozen=True)
class ToolPolicyDecision:
    allowed: bool
    reason: str = ""
    code: str = ""


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def check_tool_policy(
    server_name: str,
    tool_name: str,
    args: dict[str, Any],
) -> ToolPolicyDecision:
    """
    Hard safety layer for tool calls.

    Prompt rules are useful, but they are not a security boundary. This policy
    blocks repository-mutating Git tools unless the operator deliberately opts in
    with AGENT_ALLOW_GIT_MUTATIONS=1 for that run.
    """

    if server_name == "git" and tool_name in MUTATING_GIT_TOOLS:
        if _truthy_env("AGENT_ALLOW_GIT_MUTATIONS"):
            return ToolPolicyDecision(allowed=True)

        return ToolPolicyDecision(
            allowed=False,
            code="git_mutation_blocked",
            reason=(
                f"Blocked mutating Git tool '{tool_name}'. "
                "Set AGENT_ALLOW_GIT_MUTATIONS=1 for this run only if the user "
                "explicitly requested repository mutation."
            ),
        )

    return ToolPolicyDecision(allowed=True)
