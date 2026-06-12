from __future__ import annotations

import json
from pathlib import Path

from agents.role_agents import get_agent, list_agent_configs, list_agents


DATASET_PATH = Path("business_prompt_lab") / "ba_agent_eval_v0_1.jsonl"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load_cases() -> list[dict]:
    lines = DATASET_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def main() -> int:
    roles = {item["key"]: item for item in list_agents()}
    configs = {item["key"]: item for item in list_agent_configs()}
    _assert("business_analyst" in roles, "business_analyst role is missing")
    _assert("business_analyst" in configs, "business_analyst config is missing")

    agent = get_agent("business_analyst")
    _assert(agent.describe()["allowed_tools"] == [], "BA agent must be prompt-only with no tools")
    _assert(not agent.is_tool_allowed("filesystem.read_file"), "BA agent unexpectedly allows file reads")
    _assert(not agent.is_tool_allowed("search.web_search"), "BA agent unexpectedly allows web search")
    _assert(not agent.is_tool_allowed("file_editor.file_editor_create"), "BA agent unexpectedly allows file edits")

    blocked = agent._guard_output(
        json.dumps(
            {
                "action": "tool",
                "tool": "filesystem.read_file",
                "args": {"path": "README.md"},
            }
        )
    )
    blocked_payload = json.loads(blocked)
    _assert(blocked_payload.get("action") == "final", blocked_payload)
    _assert(blocked_payload.get("finish_reason") == "blocker", blocked_payload)

    lens_names = set(roles["business_analyst"].get("lens_names", []))
    expected_lenses = {
        "problem_framing",
        "evidence_separation",
        "stakeholder_mapping",
        "scope_control",
        "requirement_decomposition",
        "handoff_readiness",
    }
    _assert(expected_lenses <= lens_names, f"BA lenses missing: {sorted(expected_lenses - lens_names)}")

    cases = _load_cases()
    _assert(len(cases) == 12, f"Expected 12 BA eval cases, got {len(cases)}")
    for case in cases:
        _assert(case.get("id", "").startswith("BA-T"), f"Bad case id: {case}")
        _assert(case.get("user_prompt"), f"Missing user_prompt: {case.get('id')}")
        _assert(case.get("skill_labels"), f"Missing skill_labels: {case.get('id')}")
        _assert(case.get("constraint_labels"), f"Missing constraint_labels: {case.get('id')}")

    print("BA_AGENT_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
