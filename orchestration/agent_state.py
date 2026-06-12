from __future__ import annotations

from typing import Any, Literal, TypedDict


AgentName = Literal[
    "research",
    "business_analyst",
    "planner",
    "architect",
    "code",
    "test",
    "review",
    "ledger",
    "final",
    "tool",
]


class AgentState(TypedDict, total=False):
    user_task: str
    messages: list[dict[str, str]]

    next_agent: AgentName
    last_agent: str
    step_count: int
    max_steps: int

    agent_output: str
    parsed_action: dict[str, Any]
    role_outputs: dict[str, list[dict[str, Any]]]

    tool_name: str
    tool_args: dict[str, Any]
    tool_result: dict[str, Any]
    repeated_tool_calls: dict[str, int]
    json_retries: dict[str, int]
    role_visits: dict[str, int]
    subtask_visits: dict[str, int]

    plan: str
    required_files: list[str]
    missing_files: list[str]
    last_failure: dict[str, Any]
    repair_attempts: dict[str, int]
    files_modified: list[str]
    tests_run: list[dict[str, Any]]
    review_result: dict[str, Any]
    ledger_result: dict[str, Any]

    errors: list[str]
    final_message: str
