from __future__ import annotations

from typing import Any

from agents.code_agent import CodeAgent
from agents.test_agent import TestAgent


class CodeTestOrchestrator:
    """
    v0.5 orchestrator for the Engineering and QA departments.

    It is intentionally small and separate from the main LangGraph pipeline. The
    purpose is to test the v0.5 department model end to end before wiring it into
    broader Research/Planner/Architect/Review/Ledger/Final orchestration.
    """

    def __init__(
        self,
        *,
        max_cycles: int = 2,
        use_llm: bool = False,
        model: str | None = None,
    ) -> None:
        self.version = "v0.5"
        self.max_cycles = max(1, int(max_cycles))
        self.code_agent = CodeAgent(use_llm=use_llm, model=model)
        self.test_agent = TestAgent(use_llm=use_llm, model=model)

    def run(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        history: list[dict[str, Any]] = []
        current_task = task

        for cycle in range(1, self.max_cycles + 1):
            code_result = self.code_agent.run(
                current_task,
                context={
                    **context,
                    "cycle": cycle,
                    "history": history,
                },
            )
            history.append({"cycle": cycle, "agent": "code_agent", "result": code_result})

            code_route = code_result.get("route", {})
            if code_route.get("next_agent") == "planner_agent":
                return {
                    "ok": False,
                    "status": "blocked_needs_planning",
                    "version": self.version,
                    "cycles": cycle,
                    "history": history,
                    "final_route": code_route,
                }
            if code_route.get("next_agent") != "test_agent":
                return {
                    "ok": False,
                    "status": "blocked_after_code",
                    "version": self.version,
                    "cycles": cycle,
                    "history": history,
                    "final_route": code_route,
                }

            test_result = self.test_agent.run(
                task=current_task,
                code_result=code_result,
                context={
                    **context,
                    "cycle": cycle,
                    "history": history,
                },
            )
            history.append({"cycle": cycle, "agent": "test_agent", "result": test_result})

            test_route = test_result.get("route", {})
            next_agent = test_route.get("next_agent")
            if next_agent == "review_agent":
                return {
                    "ok": True,
                    "status": "ready_for_review",
                    "version": self.version,
                    "cycles": cycle,
                    "history": history,
                    "final_route": test_route,
                }
            if next_agent == "planner_agent":
                return {
                    "ok": False,
                    "status": "blocked_needs_planning",
                    "version": self.version,
                    "cycles": cycle,
                    "history": history,
                    "final_route": test_route,
                }

            current_task = (
                task
                + "\n\nPrevious QA evidence requires a Code Agent repair:\n"
                + str(test_result.get("execution", {}))
            )

        return {
            "ok": False,
            "status": "max_cycles_reached",
            "version": self.version,
            "cycles": self.max_cycles,
            "history": history,
            "final_route": {"next_agent": "code_agent", "reason": "Max cycles reached."},
        }
