from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.final_synthesis_agent import FinalSynthesisAgent
from agents.knowledge import GeneralKnowledgeAgent, PhilosophyAgent
from agents.research_department import ResearchDepartment
from agents.safety import SafetyDepartment
from orchestration.intent_router import IntentRouter, IntentType, RouteDecision


CODE_INTENTS = {
    IntentType.CODE_TASK,
    IntentType.REPO_TASK,
    IntentType.DEBUG_TASK,
}

KNOWLEDGE_INTENTS = {
    IntentType.GENERAL_KNOWLEDGE,
    IntentType.NEUROSCIENCE_TASK,
    IntentType.PHILOSOPHY_TASK,
}

FACTORY_INTENTS = {
    IntentType.PRODUCT_BUILD_TASK,
}


@dataclass
class GlobalSupervisor:
    """
    Top-level supervisor for general multi-agent routing.

    The default mode is deterministic and side-effect-light. Code tasks are
    recognized and packaged for delegation; callers can opt into the existing
    coding runtime with run_coding=True.
    """

    run_coding: bool = False
    research_use_tools: bool = False

    def __post_init__(self) -> None:
        self.router = IntentRouter()
        self.final_synthesis = FinalSynthesisAgent()

    def run(self, user_request: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        decision = self.router.classify(user_request)
        execution_plan = list(decision.steps)
        department_outputs: dict[str, Any] = {}
        validation_evidence: list[dict[str, Any]] = []
        citations: list[dict[str, Any]] = []
        limits: list[str] = []

        safety_report = self._run_safety_if_needed(user_request, decision, execution_plan)
        if safety_report:
            department_outputs["safety"] = safety_report
            if safety_report.get("status") == "blocked":
                limits.extend(safety_report.get("notes", []))
                final = self.final_synthesis.run(
                    user_request=user_request,
                    route_decision=decision.to_dict(),
                    execution_plan=execution_plan,
                    department_outputs=department_outputs,
                    validation_evidence=validation_evidence,
                    citations=citations,
                    limits=limits,
                )
                return {
                    "ok": False,
                    "status": "blocked_by_safety",
                    "route_decision": decision.to_dict(),
                    "execution_plan": execution_plan,
                    "safety_report": safety_report,
                    "department_outputs": department_outputs,
                    "final": final,
                    "final_answer": final["final_answer"],
                }

        if decision.intent == IntentType.MIXED_TASK or decision.intent in FACTORY_INTENTS:
            self._run_execution_plan(
                user_request=user_request,
                context=context,
                decision=decision,
                execution_plan=execution_plan,
                department_outputs=department_outputs,
                validation_evidence=validation_evidence,
                citations=citations,
            )
        elif decision.intent in KNOWLEDGE_INTENTS:
            department_outputs["knowledge"] = self._run_knowledge(user_request, decision, context)
        elif decision.intent == IntentType.RESEARCH_REQUIRED:
            research_output = ResearchDepartment(use_tools=self.research_use_tools).run(user_request, context)
            department_outputs["research"] = research_output
            citations.extend(research_output.get("sources", []))
        elif decision.intent in CODE_INTENTS:
            coding_output = self._run_coding(user_request, context)
            department_outputs["coding"] = coding_output
            validation_evidence.extend(coding_output.get("validation_evidence", []))
        elif decision.intent == IntentType.AGENT_CREATION:
            department_outputs["agent_factory"] = self._run_agent_factory_placeholder(user_request, context)
        else:
            limits.append(f"Unhandled intent: {decision.intent.value}")

        final = self.final_synthesis.run(
            user_request=user_request,
            route_decision=decision.to_dict(),
            execution_plan=execution_plan,
            department_outputs=department_outputs,
            validation_evidence=validation_evidence,
            citations=citations,
            limits=limits,
        )
        return {
            "ok": True,
            "status": "completed",
            "route_decision": decision.to_dict(),
            "execution_plan": execution_plan,
            "safety_report": safety_report,
            "department_outputs": department_outputs,
            "final": final,
            "final_answer": final["final_answer"],
        }

    def _run_safety_if_needed(
        self,
        user_request: str,
        decision: RouteDecision,
        execution_plan: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        needs_safety = (
            decision.intent in {IntentType.MIXED_TASK, IntentType.AGENT_CREATION, IntentType.RESEARCH_REQUIRED}
            or decision.intent in CODE_INTENTS
            or decision.needs_repo
            or decision.needs_code
            or decision.needs_web
        )
        if not needs_safety:
            return None
        return SafetyDepartment(
            run_coding=self.run_coding,
            research_use_tools=self.research_use_tools,
        ).run(
            user_request=user_request,
            route_decision=decision.to_dict(),
            execution_plan=execution_plan,
        )

    def _run_execution_plan(
        self,
        *,
        user_request: str,
        context: dict[str, Any],
        decision: RouteDecision,
        execution_plan: list[dict[str, Any]],
        department_outputs: dict[str, Any],
        validation_evidence: list[dict[str, Any]],
        citations: list[dict[str, Any]],
    ) -> None:
        for step in execution_plan:
            department = step.get("department")
            if department == "final_synthesis":
                continue
            step_context = {**context, "department_outputs": department_outputs, "current_step": step}
            if department == "research":
                research_output = ResearchDepartment(use_tools=self.research_use_tools).run(user_request, step_context)
                department_outputs["research"] = research_output
                citations.extend(research_output.get("sources", []))
            elif department == "software_factory":
                factory_output = self._run_software_factory(user_request, step_context)
                department_outputs["software_factory"] = factory_output
                validation_evidence.append(
                    {
                        "name": "software_factory",
                        "status": factory_output.get("status"),
                        "artifact_dir": factory_output.get("artifact_dir"),
                        "implementation_spec": (
                            factory_output.get("implementation_spec") or {}
                        ).get("path"),
                    }
                )
            elif department == "knowledge":
                department_outputs["knowledge"] = self._run_knowledge(user_request, decision, step_context)
            elif department == "planning":
                department_outputs["planning"] = self._run_planning_placeholder(user_request, step_context)
            elif department == "agent_factory":
                department_outputs["agent_factory"] = self._run_agent_factory_placeholder(user_request, step_context)
            elif department == "coding":
                coding_output = self._run_coding(user_request, step_context)
                department_outputs["coding"] = coding_output
                validation_evidence.extend(coding_output.get("validation_evidence", []))
            elif department == "writing":
                department_outputs["writing"] = self._run_writing_placeholder(user_request, step_context)

    def _run_knowledge(
        self,
        user_request: str,
        decision: RouteDecision,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        if "PHILOSOPHY_TASK" in decision.sub_intents:
            return PhilosophyAgent().run(user_request, context)
        return GeneralKnowledgeAgent().run(user_request, context)

    def _run_software_factory(self, user_request: str, context: dict[str, Any]) -> dict[str, Any]:
        from pathlib import Path

        from orchestration.software_factory_orchestrator import (
            SoftwareFactoryOrchestrator,
            infer_project_export_dir,
        )

        run_id = context.get("run_id")
        artifact_root = context.get("artifact_root") or Path("workspace") / "factory_runs"
        export_project_dir = context.get("export_project_dir") or infer_project_export_dir(user_request)
        result = SoftwareFactoryOrchestrator(artifact_root=artifact_root).run(
            user_request,
            run_id=run_id,
            export_project_dir=export_project_dir,
        )
        stages = [
            {
                "agent": stage.get("agent"),
                "department": stage.get("department"),
                "decision": stage.get("decision"),
                "next_agent": stage.get("route", {}).get("next_agent"),
                "ok": stage.get("ok"),
            }
            for stage in result.get("stage_results", [])
        ]
        return {
            "department": "software_factory",
            "agent": "software_factory_orchestrator",
            "ok": result.get("ok") is True,
            "status": result.get("status"),
            "version": result.get("version"),
            "run_id": result.get("run_id"),
            "artifact_dir": result.get("artifact_dir"),
            "implementation_spec": result.get("implementation_spec"),
            "code_handoff_packet": result.get("code_handoff_packet"),
            "summary_artifact": result.get("summary_artifact"),
            "exported_docs": result.get("exported_docs"),
            "next_recommended_command": result.get("next_recommended_command"),
            "stage_count": result.get("stage_count"),
            "agent_count": result.get("agent_count"),
            "stages": stages,
            "summary": (
                "Software Factory produced product, business-logic, architecture, "
                "implementation, docs, and code-handoff artifacts."
                if result.get("ok") is True
                else "Software Factory did not complete successfully."
            ),
            "limits": [
                "Software Factory prepares artifacts and a code handoff; it does not execute the real coding runtime.",
            ],
        }

    def _run_planning_placeholder(self, user_request: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "department": "planning",
            "agent": "planning_placeholder",
            "summary": "Planning step acknowledged. Full Planning Department integration is deferred.",
            "requested": user_request,
            "limits": ["Planning Department is a placeholder in phase 5."],
        }

    def _run_writing_placeholder(self, user_request: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "department": "writing",
            "agent": "writing_placeholder",
            "summary": "Writing step acknowledged. Final Synthesis owns the actual final wording.",
            "requested": user_request,
            "limits": ["Writing Department is a placeholder in phase 5."],
        }

    def _run_coding(self, user_request: str, context: dict[str, Any]) -> dict[str, Any]:
        if not self.run_coding:
            return {
                "department": "coding",
                "agent": "coding_department_delegate",
                "final_message": (
                    "The request was classified as a code task. In deterministic global-supervisor "
                    "mode, it is delegated to the existing Company/LangGraph coding path rather than run."
                ),
                "delegated": True,
                "target_runtime": "CompanyOrchestratorV05 or LangGraph coding path",
                "validation_evidence": [],
                "limits": ["Coding runtime was not executed because run_coding=False."],
            }

        from orchestration.company_orchestrator import CompanyOrchestratorV05

        result = CompanyOrchestratorV05().run(user_request, context=context)
        return {
            "department": "coding",
            "agent": "company_orchestrator_v05",
            "final_message": result.get("final_message", ""),
            "delegated": False,
            "raw_result": result,
            "validation_evidence": result.get("tests_run", []),
            "limits": [] if result.get("ok") else ["Coding runtime did not complete successfully."],
        }

    def _run_agent_factory_placeholder(self, user_request: str, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "department": "agent_factory",
            "agent": "agent_factory_placeholder",
            "summary": (
                "The request was classified as agent creation. The global supervisor can route it, "
                "but a dedicated Agent Factory implementation is still a placeholder."
            ),
            "requested": user_request,
            "limits": ["Agent Factory Department is a placeholder."],
        }


def run_global_supervisor(
    user_request: str,
    context: dict[str, Any] | None = None,
    *,
    run_coding: bool = False,
    research_use_tools: bool = False,
) -> dict[str, Any]:
    return GlobalSupervisor(run_coding=run_coding, research_use_tools=research_use_tools).run(
        user_request,
        context=context,
    )
