from __future__ import annotations

from typing import Any

from agents.architect_agent import ArchitectAgent
from agents.business_analyst_agent import BusinessAnalystAgent
from agents.code_agent import CodeAgent
from agents.department_v05 import VERSION, changed_files_from_code_result, test_commands_from_test_result
from agents.final_agent import FinalAgent
from agents.ledger_agent import LedgerAgent
from agents.planner_agent import PlannerAgent
from agents.research_agent import ResearchAgent
from agents.review_agent import ReviewAgent
from agents.test_agent import TestAgent


def _has_required_success_marker(task: str, final_message: str) -> bool:
    markers = []
    if "SOCIETY_SIM_TESTS_OK" in task:
        markers.append("SOCIETY_SIM_TESTS_OK")
    if "COMPANY_AGENTS_V05_OK" in task:
        markers.append("COMPANY_AGENTS_V05_OK")
    if "CODE_TEST_LENS_OK" in task:
        markers.append("CODE_TEST_LENS_OK")
    if "LANGGRAPH_SMOKE_OK" in task:
        markers.append("LANGGRAPH_SMOKE_OK")

    if not markers:
        markers_ok = True
    else:
        markers_ok = all(marker in final_message for marker in markers)

    folded_task = task.lower()
    if "cli_demo.py" in folded_task or "cli_demo" in folded_task:
        demo_ok = "cli_demo.py: ran successfully" in final_message or "DEMO COMPLETE" in final_message
        return markers_ok and demo_ok
    return markers_ok


class CompanyOrchestratorV05:
    """
    Full v0.5 company-style coding-agent chain.

    The orchestrator owns routing. Departments own decisions. Executor tools
    remain narrow and explicit inside Code/Test.
    """

    def __init__(
        self,
        *,
        max_cycles: int = 2,
        use_llm: bool = False,
        model: str | None = None,
    ) -> None:
        self.version = VERSION
        self.max_cycles = max(1, int(max_cycles))
        self.research_agent = ResearchAgent(use_llm=use_llm, model=model)
        self.business_analyst_agent = BusinessAnalystAgent(use_llm=use_llm, model=model)
        self.planner_agent = PlannerAgent(use_llm=use_llm, model=model)
        self.architect_agent = ArchitectAgent(use_llm=use_llm, model=model)
        self.code_agent = CodeAgent(use_llm=use_llm, model=model)
        self.test_agent = TestAgent(use_llm=use_llm, model=model)
        self.review_agent = ReviewAgent(use_llm=use_llm, model=model)
        self.ledger_agent = LedgerAgent(use_llm=use_llm, model=model)
        self.final_agent = FinalAgent(use_llm=use_llm, model=model)

    def run_real(self, task: str, *, max_steps: int | None = None) -> dict[str, Any]:
        """
        Run the real LLM/tool company pipeline.

        The deterministic v0.5 chain is a contract smoke. This method delegates
        to the LangGraph implementation, which is the current real company
        runtime with BaseAgent roles, JsonGate, MCP tools, repair routing, and
        finish gates.
        """
        from orchestration.langgraph_orchestrator import run_langgraph_orchestrator

        final_message = run_langgraph_orchestrator(task, max_steps=max_steps)
        ok = _has_required_success_marker(task, final_message)
        return {
            "ok": ok,
            "status": "completed" if ok else "blocked_or_incomplete",
            "version": self.version,
            "mode": "real_langgraph",
            "final_message": final_message,
            "final_route": {
                "next_agent": "done" if ok else "inspect_logs",
                "reason": (
                    "Required success marker was found in the final message."
                    if ok
                    else "Required success marker was not found; inspect event logs."
                ),
            },
        }

    def _append(self, history: list[dict[str, Any]], agent: str, result: dict[str, Any], cycle: int = 0) -> None:
        history.append({"cycle": cycle, "agent": agent, "result": result})

    def _blocked(self, status: str, history: list[dict[str, Any]], route: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": False,
            "status": status,
            "version": self.version,
            "history": history,
            "final_route": route,
        }

    def run(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        history: list[dict[str, Any]] = []

        research_result = self.research_agent.run(task, context={**context, "history": history})
        self._append(history, "research_agent", research_result)
        if research_result.get("route", {}).get("next_agent") != "business_analyst_agent":
            return self._blocked("blocked_after_research", history, research_result.get("route", {}))

        ba_result = self.business_analyst_agent.run(
            task,
            research_result=research_result,
            context={**context, "history": history},
        )
        self._append(history, "business_analyst_agent", ba_result)
        if ba_result.get("route", {}).get("next_agent") != "planner_agent":
            return self._blocked("blocked_after_business_analysis", history, ba_result.get("route", {}))

        planner_result = self.planner_agent.run(
            task,
            research_result=research_result,
            ba_result=ba_result,
            context={**context, "history": history},
        )
        self._append(history, "planner_agent", planner_result)
        if planner_result.get("route", {}).get("next_agent") != "architect_agent":
            return self._blocked("blocked_after_planner", history, planner_result.get("route", {}))

        architect_result = self.architect_agent.run(
            task,
            planner_result=planner_result,
            context={**context, "history": history},
        )
        self._append(history, "architect_agent", architect_result)
        if architect_result.get("route", {}).get("next_agent") != "code_agent":
            return self._blocked("blocked_after_architect", history, architect_result.get("route", {}))

        current_task = task
        code_result: dict[str, Any] = {}
        test_result: dict[str, Any] = {}

        for cycle in range(1, self.max_cycles + 1):
            code_result = self.code_agent.run(
                current_task,
                context={
                    **context,
                    "cycle": cycle,
                    "history": history,
                    "research_result": research_result,
                    "business_analysis_result": ba_result,
                    "planner_result": planner_result,
                    "architect_result": architect_result,
                },
            )
            self._append(history, "code_agent", code_result, cycle)
            code_route = code_result.get("route", {})
            if code_route.get("next_agent") != "test_agent":
                return self._blocked("blocked_after_code", history, code_route)

            test_result = self.test_agent.run(
                current_task,
                code_result=code_result,
                context={**context, "cycle": cycle, "history": history},
            )
            self._append(history, "test_agent", test_result, cycle)
            test_route = test_result.get("route", {})
            next_agent = test_route.get("next_agent")
            if next_agent == "review_agent":
                break
            if next_agent == "planner_agent":
                return self._blocked("blocked_needs_planning", history, test_route)

            current_task = (
                task
                + "\n\nPrevious QA evidence requires a Code Agent repair:\n"
                + str(test_result.get("execution", {}))
            )
        else:
            return self._blocked(
                "max_cycles_reached",
                history,
                {"next_agent": "code_agent", "reason": "Max Code/Test cycles reached."},
            )

        review_result = self.review_agent.run(
            task,
            code_result=code_result,
            test_result=test_result,
            context={**context, "history": history},
        )
        self._append(history, "review_agent", review_result)
        review_route = review_result.get("route", {})
        if review_route.get("next_agent") != "ledger_agent":
            return self._blocked("review_requested_changes", history, review_route)

        ledger_result = self.ledger_agent.run(
            task,
            history=history,
            context={**context, "review_result": review_result},
        )
        self._append(history, "ledger_agent", ledger_result)
        ledger_route = ledger_result.get("route", {})
        if ledger_route.get("next_agent") != "final_agent":
            return self._blocked("blocked_after_ledger", history, ledger_route)

        final_result = self.final_agent.run(
            task,
            history=history,
            context={
                **context,
                "ledger_result": ledger_result,
                "changed_files": changed_files_from_code_result(code_result),
                "tests_run": test_commands_from_test_result(test_result),
            },
        )
        self._append(history, "final_agent", final_result)

        final_route = final_result.get("route", {})
        ok = final_route.get("next_agent") == "done" and final_result.get("synthesis", {}).get("decision") == "success"
        return {
            "ok": ok,
            "status": "completed" if ok else "blocked_after_final",
            "version": self.version,
            "cycles": len([item for item in history if item.get("agent") == "code_agent"]),
            "history": history,
            "final_message": final_result.get("synthesis", {}).get("final_message", ""),
            "final_route": final_route,
        }
