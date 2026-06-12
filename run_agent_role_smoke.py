from __future__ import annotations

import json
from typing import Callable

from agents.role_agents import get_agent, list_agent_configs, list_agents


class AgentRoleSmokeFailure(AssertionError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AgentRoleSmokeFailure(message)


def _allowed(role: str, tool: str) -> bool:
    return get_agent(role).is_tool_allowed(tool)


def _has_lenses(role: str, expected: set[str]) -> bool:
    agent = next(item for item in list_agents() if item["key"] == role)
    return expected <= set(agent.get("lens_names", []))


def main() -> int:
    expected_roles = {
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
    }
    roles = {item["key"] for item in list_agents()}
    role_configs = {item["key"]: item for item in list_agent_configs()}
    _require(expected_roles <= roles, f"Missing roles: {sorted(expected_roles - roles)}")
    _require(expected_roles <= set(role_configs), f"Missing role configs: {sorted(expected_roles - set(role_configs))}")

    checks: list[tuple[str, Callable[[], bool]]] = [
        ("research_read_search", lambda: _allowed("research", "search.web_search")),
        ("research_no_edit", lambda: not _allowed("research", "file_editor.file_editor_create")),
        ("ba_prompt_only_no_file_read", lambda: not _allowed("business_analyst", "filesystem.read_file")),
        ("ba_prompt_only_no_web", lambda: not _allowed("business_analyst", "search.web_search")),
        ("ba_prompt_only_no_edit", lambda: not _allowed("business_analyst", "file_editor.file_editor_create")),
        ("planner_can_issue", lambda: _allowed("planner", "issue.issue_create")),
        ("planner_no_edit", lambda: not _allowed("planner", "file_editor.file_editor_str_replace")),
        ("architect_can_write_design_doc", lambda: _allowed("architect", "document.document_write_markdown")),
        ("architect_no_source_edit", lambda: not _allowed("architect", "file_editor.file_editor_insert")),
        ("code_can_edit", lambda: _allowed("code", "file_editor.file_editor_str_replace")),
        ("code_no_validate", lambda: not _allowed("code", "lint_test.test_smoke_suite")),
        ("test_can_validate", lambda: _allowed("test", "lint_test.lint_compile")),
        ("test_no_edit", lambda: not _allowed("test", "file_editor.file_editor_create")),
        ("review_can_diff", lambda: _allowed("review", "git.git_diff_unstaged")),
        ("review_no_commit", lambda: not _allowed("review", "git.git_commit")),
        ("ledger_can_write_memory", lambda: _allowed("ledger", "ledger.ledger_append")),
        ("ledger_no_terminal", lambda: not _allowed("ledger", "terminal.terminal_run")),
        ("final_can_read_issue", lambda: _allowed("final", "issue.issue_get")),
        ("final_no_edit", lambda: not _allowed("final", "file_editor.file_editor_create")),
        ("tool_agent_backcompat_allows_edit", lambda: _allowed("tool", "file_editor.file_editor_create")),
        (
            "role_configs_define_route_permissions",
            lambda: all(isinstance(item.get("route_permissions"), dict) for item in role_configs.values()),
        ),
        (
            "role_configs_define_test_ownership",
            lambda: all(isinstance(item.get("test_ownership"), dict) for item in role_configs.values()),
        ),
        (
            "code_config_hands_validation_to_test",
            lambda: role_configs["code"]["test_ownership"].get("must_handoff_to") == "test",
        ),
        (
            "test_config_owns_validation",
            lambda: role_configs["test"]["test_ownership"].get("owns_validation") is True,
        ),
        (
            "research_department_lenses",
            lambda: _has_lenses(
                "research",
                {"source_scout", "source_credibility", "fact_check", "synthesis", "knowledge_curator"},
            ),
        ),
        (
            "business_analysis_department_lenses",
            lambda: _has_lenses(
                "business_analyst",
                {
                    "problem_framing",
                    "evidence_separation",
                    "stakeholder_mapping",
                    "scope_control",
                    "requirement_decomposition",
                    "handoff_readiness",
                },
            ),
        ),
        (
            "planner_department_lenses",
            lambda: _has_lenses(
                "planner",
                {"product_manager", "project_manager", "dependency_planner", "risk_manager", "scope_control"},
            ),
        ),
        (
            "architect_department_lenses",
            lambda: _has_lenses(
                "architect",
                {"system_architect", "data_architect", "api_contract", "security_architect", "scalability"},
            ),
        ),
        (
            "code_department_lenses",
            lambda: _has_lenses(
                "code",
                {"implementation", "integration", "defensive_coding", "refactor_discipline", "developer_experience"},
            ),
        ),
        (
            "test_department_lenses",
            lambda: _has_lenses(
                "test",
                {
                    "logic",
                    "critical_thinking",
                    "experienced_qa",
                    "regression",
                    "edge_case",
                    "purpose_alignment",
                    "test_executor",
                },
            ),
        ),
        (
            "review_department_lenses",
            lambda: _has_lenses(
                "review",
                {"senior_engineer", "scope_diff", "security_review", "maintainability", "release_risk"},
            ),
        ),
        (
            "ledger_department_lenses",
            lambda: _has_lenses(
                "ledger",
                {"historian", "task_state", "decision_record", "auditor", "incident_tracker"},
            ),
        ),
        (
            "final_department_lenses",
            lambda: _has_lenses(
                "final",
                {
                    "executive_summary",
                    "technical_writer",
                    "user_facing_explanation",
                    "limitation_disclosure",
                    "next_step_recommendation",
                },
            ),
        ),
    ]

    results = []
    for name, check in checks:
        passed = bool(check())
        results.append({"name": name, "status": "PASS" if passed else "FAIL"})
        print(f"{'PASS' if passed else 'FAIL'} {name}")

    disallowed_output = get_agent("planner")._guard_output(
        json.dumps(
            {
                "action": "tool",
                "tool": "file_editor.file_editor_create",
                "args": {"path": "code/nope.py", "content": ""},
            }
        )
    )
    disallowed_payload = json.loads(disallowed_output)
    guard_passed = (
        disallowed_payload.get("action") == "final"
        and disallowed_payload.get("finish_reason") == "blocker"
    )
    results.append({"name": "base_agent_blocks_disallowed_tool_output", "status": "PASS" if guard_passed else "FAIL"})
    print(f"{'PASS' if guard_passed else 'FAIL'} base_agent_blocks_disallowed_tool_output")

    fenced_disallowed_output = get_agent("research")._guard_output(
        "```json\n"
        + json.dumps(
            {
                "action": "tool",
                "tool": "ledger.ledger_append",
                "args": {"entry_type": "note", "title": "nope"},
            }
        )
        + "\n```"
    )
    fenced_payload = json.loads(fenced_disallowed_output)
    fenced_guard_passed = (
        fenced_payload.get("action") == "final"
        and fenced_payload.get("finish_reason") == "blocker"
    )
    results.append({"name": "base_agent_blocks_fenced_disallowed_tool_output", "status": "PASS" if fenced_guard_passed else "FAIL"})
    print(f"{'PASS' if fenced_guard_passed else 'FAIL'} base_agent_blocks_fenced_disallowed_tool_output")

    allowed_raw = json.dumps(
        {
            "action": "tool",
            "tool": "file_editor.file_editor_create",
            "args": {"path": "code/ok.py", "content": ""},
        }
    )
    allowed_output = get_agent("code")._guard_output(allowed_raw)
    allowed_passed = allowed_output == allowed_raw
    results.append({"name": "base_agent_allows_role_tool_output", "status": "PASS" if allowed_passed else "FAIL"})
    print(f"{'PASS' if allowed_passed else 'FAIL'} base_agent_allows_role_tool_output")

    failed = [item for item in results if item["status"] != "PASS"]
    print(json.dumps({"roles": sorted(roles), "checks": results}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
