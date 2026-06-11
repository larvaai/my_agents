from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    NEUROSCIENCE_TASK = "NEUROSCIENCE_TASK"
    PHILOSOPHY_TASK = "PHILOSOPHY_TASK"
    PRODUCT_BUILD_TASK = "PRODUCT_BUILD_TASK"
    CODE_TASK = "CODE_TASK"
    REPO_TASK = "REPO_TASK"
    DEBUG_TASK = "DEBUG_TASK"
    AGENT_CREATION = "AGENT_CREATION"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"
    WRITING_TASK = "WRITING_TASK"
    PLANNING_TASK = "PLANNING_TASK"
    MIXED_TASK = "MIXED_TASK"


@dataclass(frozen=True)
class RouteDecision:
    intent: IntentType
    confidence: float
    needs_repo: bool
    needs_code: bool
    needs_web: bool
    needs_memory: bool
    target_department: str
    reason: str
    sub_intents: tuple[str, ...] = ()
    execution_mode: str = "single"
    steps: tuple[dict[str, str], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "needs_repo": self.needs_repo,
            "needs_code": self.needs_code,
            "needs_web": self.needs_web,
            "needs_memory": self.needs_memory,
            "target_department": self.target_department,
            "reason": self.reason,
            "sub_intents": list(self.sub_intents),
            "execution_mode": self.execution_mode,
            "steps": list(self.steps),
        }


CODE_TERMS = (
    "code",
    "repo",
    "file",
    "bug",
    "debug",
    "test",
    "pytest",
    "compile",
    "refactor",
    "implement",
    "sua",
    "sửa",
    "tao file",
    "tạo file",
    ".py",
    ".md",
    "orchestrator",
    "mcp",
)

REPO_TERMS = (
    "repo",
    "repository",
    "project",
    "workspace",
    "file",
    "module",
    "orchestrator",
    "mcp",
)

DEBUG_TERMS = (
    "bug",
    "debug",
    "traceback",
    "error",
    "failing",
    "fix",
    "sua loi",
    "loi",
)

AGENT_CREATION_TERMS = (
    "create agent",
    "create a new",
    "create new",
    "new agent",
    "tao agent",
    "tạo agent",
    "them agent",
    "thêm agent",
    "agent moi",
    "agent mới",
    "skill builder",
    "prompt builder",
    "tool binder",
)

RESEARCH_TERMS = (
    "latest",
    "newest",
    "most recent",
    "today",
    "current",
    "paper",
    "arxiv",
    "citation",
    "source",
    "pdf",
    "web",
    "search",
    "fetch",
    "mới nhất",
    "hien tai",
    "hiện tại",
    "nguồn",
    "trích dẫn",
)

PHILOSOPHY_TERMS = (
    "philosophy",
    "triết",
    "agency",
    "autonomy",
    "free will",
    "consciousness",
    "ethics",
)

NEUROSCIENCE_TERMS = (
    "amygdala",
    "dopamine",
    "basal ganglia",
    "hippocampus",
    "prefrontal",
    "neuroscience",
    "brain",
    "goal-gradient",
    "goal gradient",
)

WRITING_TERMS = (
    "write docs",
    "documentation",
    "readme",
    "draft",
    "essay",
    "report",
    "viet tai lieu",
    "viet docs",
)

PLANNING_TERMS = (
    "plan",
    "roadmap",
    "milestone",
    "strategy",
    "timeline",
    "ke hoach",
)

PRODUCT_BUILD_TERMS = (
    "mini-project",
    "simulation engine",
    "business logic",
    "acceptance criteria",
    "acceptance markers",
    "quality gates",
    "product",
    "prd",
    "brd",
    "software factory",
    "save/load",
    "cli_demo",
    "test runner",
    "project phai",
    "cau truc file",
    "required files",
)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(_contains_term(text, term) for term in terms)


def _score(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if _contains_term(text, term))


def _contains_term(text: str, term: str) -> bool:
    if term.startswith("."):
        return term in text
    return re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", text) is not None


def _has_code_file_reference(text: str) -> bool:
    return re.search(r"(?<![\w.-])[\w./\\-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml)(?![\w.-])", text) is not None


def _file_reference_count(text: str) -> int:
    return len(
        set(
            re.findall(
                r"(?<![\w.-])[\w./\\-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml)(?![\w.-])",
                text,
            )
        )
    )


def _strip_file_references(text: str) -> str:
    return re.sub(
        r"(?<![\w.-])[\w./\\-]+\.(?:py|ts|tsx|js|jsx|md|json|yaml|yml)(?![\w.-])",
        " ",
        text,
    )


class IntentRouter:
    """
    Deterministic first-pass router for the global supervisor.

    This deliberately avoids LLM calls so phase 1-4 can be smoke-tested without
    network/model dependencies. A later LLM router can sit behind the same
    RouteDecision schema.
    """

    def classify(self, user_request: str) -> RouteDecision:
        text = (user_request or "").strip()
        folded = text.lower()
        semantic_text = _strip_file_references(folded)

        agent_creation_score = _score(semantic_text, AGENT_CREATION_TERMS)
        research_score = _score(semantic_text, RESEARCH_TERMS)
        code_score = _score(folded, CODE_TERMS) + (1 if _has_code_file_reference(folded) else 0)
        repo_score = _score(folded, REPO_TERMS)
        debug_score = _score(folded, DEBUG_TERMS)
        philosophy_score = _score(semantic_text, PHILOSOPHY_TERMS)
        neuroscience_score = _score(semantic_text, NEUROSCIENCE_TERMS)
        writing_score = _score(semantic_text, WRITING_TERMS)
        planning_score = _score(semantic_text, PLANNING_TERMS)
        product_build_score = _score(folded, PRODUCT_BUILD_TERMS)
        file_reference_count = _file_reference_count(folded)
        knowledge_score = philosophy_score + neuroscience_score

        if agent_creation_score:
            return RouteDecision(
                intent=IntentType.AGENT_CREATION,
                confidence=0.88,
                needs_repo=True,
                needs_code=True,
                needs_web=False,
                needs_memory=False,
                target_department="agent_factory",
                reason="Request asks to create or modify an agent capability.",
                sub_intents=("AGENT_CREATION",),
                steps=(
                    {"department": "agent_factory", "task": "Design or scaffold the requested agent capability."},
                    {"department": "final_synthesis", "task": "Summarize the proposed or completed agent work."},
                ),
            )

        if (product_build_score and code_score) or (code_score and file_reference_count >= 6 and planning_score):
            return RouteDecision(
                intent=IntentType.PRODUCT_BUILD_TASK,
                confidence=0.92,
                needs_repo=True,
                needs_code=True,
                needs_web=False,
                needs_memory=True,
                target_department="software_factory",
                reason="Request describes a multi-file product build that needs product/domain/business-logic artifacts before coding.",
                sub_intents=("PRODUCT_BUILD_TASK", "PLANNING_TASK", "CODE_TASK"),
                execution_mode="sequential",
                steps=(
                    {
                        "department": "software_factory",
                        "task": "Produce product, domain, business-logic, architecture, implementation, and handoff artifacts.",
                    },
                    {
                        "department": "coding",
                        "task": "Use the generated implementation spec with the existing coding path when coding execution is enabled.",
                    },
                    {
                        "department": "final_synthesis",
                        "task": "Report artifact locations, handoff command, safety limits, and validation status.",
                    },
                ),
            )

        mixed_reason = self._mixed_reason(
            agent_creation_score=agent_creation_score,
            research_score=research_score,
            code_score=code_score,
            knowledge_score=knowledge_score,
            writing_score=writing_score,
            planning_score=planning_score,
        )
        if mixed_reason:
            return self._mixed_decision(
                reason=mixed_reason,
                agent_creation_score=agent_creation_score,
                research_score=research_score,
                code_score=code_score,
                repo_score=repo_score,
                debug_score=debug_score,
                philosophy_score=philosophy_score,
                neuroscience_score=neuroscience_score,
                writing_score=writing_score,
                planning_score=planning_score,
            )

        if research_score and not code_score:
            return RouteDecision(
                intent=IntentType.RESEARCH_REQUIRED,
                confidence=0.82,
                needs_repo=False,
                needs_code=False,
                needs_web=True,
                needs_memory=False,
                target_department="research",
                reason="Request depends on current, external, paper, PDF, or cited information.",
                sub_intents=("RESEARCH_REQUIRED",),
                steps=(
                    {"department": "research", "task": "Collect source-backed evidence."},
                    {"department": "final_synthesis", "task": "Answer with citations and limits."},
                ),
            )

        if code_score:
            intent = IntentType.DEBUG_TASK if debug_score else IntentType.REPO_TASK if repo_score else IntentType.CODE_TASK
            return RouteDecision(
                intent=intent,
                confidence=0.86,
                needs_repo=True,
                needs_code=True,
                needs_web=bool(research_score),
                needs_memory=False,
                target_department="coding",
                reason="Request mentions code, repo files, tests, debugging, or implementation.",
                sub_intents=(intent.value,),
                steps=(
                    {"department": "coding", "task": "Use the existing coding department path."},
                    {"department": "final_synthesis", "task": "Report outcome and validation evidence."},
                ),
            )

        if neuroscience_score:
            return RouteDecision(
                intent=IntentType.NEUROSCIENCE_TASK,
                confidence=0.81,
                needs_repo=False,
                needs_code=False,
                needs_web=False,
                needs_memory=False,
                target_department="knowledge",
                reason="Request is a stable neuroscience knowledge question.",
                sub_intents=("NEUROSCIENCE_TASK",),
                steps=(
                    {"department": "knowledge", "task": "Answer with general_knowledge_agent neuroscience knowledge."},
                    {"department": "final_synthesis", "task": "Produce final user-facing answer."},
                ),
            )

        if philosophy_score:
            return RouteDecision(
                intent=IntentType.PHILOSOPHY_TASK,
                confidence=0.81,
                needs_repo=False,
                needs_code=False,
                needs_web=False,
                needs_memory=False,
                target_department="knowledge",
                reason="Request is a stable philosophy knowledge question.",
                sub_intents=("PHILOSOPHY_TASK",),
                steps=(
                    {"department": "knowledge", "task": "Answer with philosophy_agent."},
                    {"department": "final_synthesis", "task": "Produce final user-facing answer."},
                ),
            )

        return RouteDecision(
            intent=IntentType.GENERAL_KNOWLEDGE,
            confidence=0.78,
            needs_repo=False,
            needs_code=False,
            needs_web=False,
            needs_memory=False,
            target_department="knowledge",
            reason="Request can be answered as stable conceptual knowledge without repo tools.",
            sub_intents=("GENERAL_KNOWLEDGE",),
            steps=(
                {"department": "knowledge", "task": "Answer with general_knowledge_agent."},
                {"department": "final_synthesis", "task": "Produce final user-facing answer."},
            ),
        )

    def _mixed_reason(
        self,
        *,
        agent_creation_score: int,
        research_score: int,
        code_score: int,
        knowledge_score: int,
        writing_score: int,
        planning_score: int,
    ) -> str:
        active = sum(
            bool(score)
            for score in (
                agent_creation_score,
                research_score,
                code_score,
                knowledge_score,
                writing_score,
                planning_score,
            )
        )
        if active < 2:
            return ""
        if code_score and (research_score or knowledge_score or planning_score):
            return "Request combines code/repo work with research, knowledge, or planning."
        if agent_creation_score and (knowledge_score or research_score or planning_score):
            return "Request combines agent creation with knowledge, research, or planning."
        if research_score and (knowledge_score or writing_score or planning_score):
            return "Request combines research with synthesis, writing, or planning."
        return ""

    def _mixed_decision(
        self,
        *,
        reason: str,
        agent_creation_score: int,
        research_score: int,
        code_score: int,
        repo_score: int,
        debug_score: int,
        philosophy_score: int,
        neuroscience_score: int,
        writing_score: int,
        planning_score: int,
    ) -> RouteDecision:
        steps: list[dict[str, str]] = []
        sub_intents: list[str] = ["MIXED_TASK"]
        needs_repo = bool(code_score or agent_creation_score or repo_score)
        needs_code = bool(code_score or agent_creation_score)
        needs_web = bool(research_score)
        needs_memory = bool(philosophy_score or neuroscience_score)

        if research_score:
            sub_intents.append("RESEARCH_REQUIRED")
            steps.append({"department": "research", "task": "Collect source-backed evidence before synthesis or implementation."})
        if philosophy_score or neuroscience_score:
            sub_intents.append("PHILOSOPHY_TASK" if philosophy_score else "NEUROSCIENCE_TASK")
            steps.append({"department": "knowledge", "task": "Explain the domain concept needed by downstream departments."})
        if planning_score:
            sub_intents.append("PLANNING_TASK")
            steps.append({"department": "planning", "task": "Convert the request into an execution plan."})
        if agent_creation_score:
            sub_intents.append("AGENT_CREATION")
            steps.append({"department": "agent_factory", "task": "Design or scaffold the requested agent capability."})
        if code_score:
            sub_intents.append("DEBUG_TASK" if debug_score else "CODE_TASK")
            steps.append({"department": "coding", "task": "Use the existing coding department path after upstream context is prepared."})
        if writing_score:
            sub_intents.append("WRITING_TASK")
            steps.append({"department": "writing", "task": "Prepare user-facing or documentation-oriented wording."})
        steps.append({"department": "final_synthesis", "task": "Merge department outputs into the final answer."})

        return RouteDecision(
            intent=IntentType.MIXED_TASK,
            confidence=0.9,
            needs_repo=needs_repo,
            needs_code=needs_code,
            needs_web=needs_web,
            needs_memory=needs_memory,
            target_department="mixed",
            reason=reason,
            sub_intents=tuple(dict.fromkeys(sub_intents)),
            execution_mode="sequential",
            steps=tuple(steps),
        )


def classify_intent(user_request: str) -> dict[str, Any]:
    return IntentRouter().classify(user_request).to_dict()
