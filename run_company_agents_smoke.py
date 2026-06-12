from __future__ import annotations

from core.schemas import capability_get
from orchestration.company_orchestrator import CompanyOrchestratorV05


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    task = (
        "Create a small Python file code/company_v05_smoke.py that prints "
        "COMPANY_AGENTS_V05_OK. Then validate that it runs."
    )
    result = CompanyOrchestratorV05(max_cycles=2).run(task)
    _assert(result.get("ok") is True, f"company orchestrator did not pass: {result}")
    _assert(result.get("status") == "completed", f"unexpected status: {result.get('status')}")
    _assert(result.get("final_route", {}).get("next_agent") == "done", "final route did not finish")

    history = result.get("history", [])
    agents = [item.get("agent") for item in history]
    expected_agents = [
        "research_agent",
        "business_analyst_agent",
        "planner_agent",
        "architect_agent",
        "code_agent",
        "test_agent",
        "review_agent",
        "ledger_agent",
        "final_agent",
    ]
    for agent in expected_agents:
        _assert(agent in agents, f"missing history agent: {agent}")

    code_result = next(item["result"] for item in history if item.get("agent") == "code_agent")
    test_result = next(item["result"] for item in history if item.get("agent") == "test_agent")
    review_result = next(item["result"] for item in history if item.get("agent") == "review_agent")

    _assert(code_result["route"]["next_agent"] == "test_agent", "Code did not route to Test")
    _assert(test_result["route"]["next_agent"] == "review_agent", "Test did not route to Review")
    _assert(review_result["route"]["next_agent"] == "ledger_agent", "Review did not route to Ledger")
    _assert(test_result["execution"]["ok"] is True, "Test execution failed")

    stdout = capability_get(test_result["execution"]["test_results"][0], "stdout", "")
    _assert("COMPANY_AGENTS_V05_OK" in stdout, "sentinel missing from test stdout")

    print("COMPANY_AGENTS_V05_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
