from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parent
ROOT_DIR = LAB_DIR.parent
DEFAULT_OUT_DIR = ROOT_DIR / "var" / "business_prompt_lab" / "agent_room"

NO_CODE_POLICY = """
No-code room policy:
- Agents must not generate source code, pseudocode, shell commands, diffs, file trees, or implementation snippets.
- If the user asks for code, translate the request into requirements, decisions, operating steps, acceptance criteria, or a business/process plan.
- Do not use markdown code fences.
- Do not invent external facts. Mark missing evidence as assumptions or unknowns.
- Keep all advice useful for business, product, prompt, research, or operating decisions.
""".strip()

AGENT_ROSTER: dict[str, dict[str, str]] = {
    "context_analyst": {
        "title": "Context Analyst",
        "focus": "Clarify the user question, decision target, constraints, assumptions, and unknowns.",
    },
    "market_analyst": {
        "title": "Market Analyst",
        "focus": "Assess customer segments, demand signals, positioning, alternatives, and adoption friction.",
    },
    "finance_strategist": {
        "title": "Finance Strategist",
        "focus": "Assess pricing, ROI logic, unit economics signals, resource tradeoffs, and success metrics.",
    },
    "operator": {
        "title": "Operator",
        "focus": "Turn analysis into practical workflow, owners, milestones, validation actions, and operating cadence.",
    },
    "risk_reviewer": {
        "title": "Risk Reviewer",
        "focus": "Challenge weak assumptions, identify blind spots, name risks, and propose mitigations.",
    },
    "customer_voice": {
        "title": "Customer Voice",
        "focus": "Represent end-user pain, buying triggers, objections, required proof, and support burden.",
    },
}

PLANNER_SCHEMA = {
    "intent": "short description of the user's decision or question",
    "success_criteria": ["what a useful answer must cover"],
    "tasks": [
        {
            "id": "T1",
            "assignee": "one key from the roster",
            "task": "specific task for that agent",
            "expected_output": "what the agent should return",
            "depends_on": ["optional task ids"],
        }
    ],
}

SPECIALIST_SCHEMA = {
    "agent": "agent key",
    "task_id": "task id",
    "answer": "short direct answer to the assigned task",
    "key_points": ["specific points"],
    "assumptions": ["explicit assumptions"],
    "risks_or_limits": ["risks, limits, or missing evidence"],
    "handoff_questions": ["questions another agent or final synthesizer should resolve"],
}

REVIEWER_SCHEMA = {
    "review": "short review of the team's evidence quality",
    "must_fix": ["issues that would mislead the final answer"],
    "gaps": ["important gaps or unknowns"],
    "followup_tasks": [
        {
            "id": "F1",
            "assignee": "one key from the roster",
            "task": "specific follow-up task",
            "expected_output": "what the agent should return",
            "depends_on": ["optional task ids"],
        }
    ],
    "confidence": 0.0,
}

CODE_SIGNAL_PATTERNS = [
    re.compile(r"```"),
    re.compile(r"^\s*(def|class|import|from)\s+\w+", re.MULTILINE),
    re.compile(r"^\s*(function|const|let|var)\s+\w+", re.MULTILINE),
    re.compile(r"^\s*(npm|pip|python|node|git|docker)\s+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE)\s+.+\s+(FROM|INTO|SET)\s+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*<\?(php)?", re.MULTILINE | re.IGNORECASE),
]


@dataclass(frozen=True)
class Task:
    id: str
    assignee: str
    task: str
    expected_output: str
    depends_on: list[str] = field(default_factory=list)
    source: str = "planner"


@dataclass
class AgentTurn:
    speaker: str
    recipient: str
    summary: str
    payload: dict[str, Any] | str


@dataclass
class RoomResult:
    question: str
    run_dir: Path
    plan: dict[str, Any]
    tasks: list[Task]
    agent_outputs: list[dict[str, Any]]
    review: dict[str, Any]
    final_answer: str
    transcript: list[AgentTurn]
    warnings: list[str]


def read_question(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.question_file:
        parts.append(args.question_file.read_text(encoding="utf-8").strip())
    if args.question:
        parts.append(" ".join(args.question).strip())
    question = "\n\n".join(part for part in parts if part)
    if not question and not args.interactive:
        raise SystemExit("Provide a question, --question-file, or --interactive.")
    return question


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def decode_json_candidate(candidate: str) -> tuple[dict[str, Any] | None, bool]:
    decoder = json.JSONDecoder()
    try:
        parsed, index = decoder.raw_decode(candidate)
    except json.JSONDecodeError:
        return None, False
    if not isinstance(parsed, dict):
        return None, False
    return parsed, candidate[index:].strip() == ""


def parse_json_object(text: str) -> tuple[dict[str, Any] | None, str]:
    raw = text.strip()
    if not raw:
        return None, "empty output"

    parsed, exact = decode_json_candidate(raw)
    if parsed is not None and exact:
        return parsed, "strict JSON object"

    fence_match = re.fullmatch(r"```(?:json)?\s*(?P<body>.*?)\s*```", raw, re.IGNORECASE | re.DOTALL)
    if fence_match:
        parsed, exact = decode_json_candidate(fence_match.group("body").strip())
        if parsed is not None and exact:
            return parsed, "JSON object wrapped in markdown fence"

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", raw):
        try:
            parsed, _ = decoder.raw_decode(raw[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed, "JSON object with surrounding text"

    return None, "no JSON object found"


def has_code_signals(text: str) -> bool:
    return any(pattern.search(text) for pattern in CODE_SIGNAL_PATTERNS)


def roster_text() -> str:
    lines = []
    for key, spec in AGENT_ROSTER.items():
        lines.append(f"- {key}: {spec['title']} - {spec['focus']}")
    return "\n".join(lines)


def default_tasks(question: str) -> list[Task]:
    lower = question.lower()
    tasks = [
        Task(
            id="T1",
            assignee="context_analyst",
            task="Clarify the decision target, constraints, explicit facts, assumptions, and unknowns in the user question.",
            expected_output="A concise problem frame and evidence map.",
        ),
        Task(
            id="T2",
            assignee="market_analyst",
            task="Analyze the customer, market, alternative solutions, and adoption friction implied by the question.",
            expected_output="Market/customer perspective with evidence limits.",
            depends_on=["T1"],
        ),
        Task(
            id="T3",
            assignee="operator",
            task="Design a practical action flow with owners, validation steps, and a cadence for the next decision.",
            expected_output="Actionable operating plan.",
            depends_on=["T1"],
        ),
        Task(
            id="T4",
            assignee="risk_reviewer",
            task="Challenge the team's likely answer by naming weak assumptions, risks, missing evidence, and mitigations.",
            expected_output="Risk and blind-spot review.",
            depends_on=["T1", "T2", "T3"],
        ),
    ]
    if any(token in lower for token in ["price", "pricing", "revenue", "cost", "roi", "unit", "gia", "doanh thu"]):
        tasks.insert(
            3,
            Task(
                id="T4",
                assignee="finance_strategist",
                task="Evaluate pricing, ROI proof, resource tradeoffs, and measurable success signals.",
                expected_output="Finance and metrics perspective.",
                depends_on=["T1", "T2"],
            ),
        )
        tasks[-1] = Task(
            id="T5",
            assignee="risk_reviewer",
            task="Challenge the team's likely answer by naming weak assumptions, risks, missing evidence, and mitigations.",
            expected_output="Risk and blind-spot review.",
            depends_on=["T1", "T2", "T3", "T4"],
        )
    if any(token in lower for token in ["customer", "user", "khach", "nguoi dung", "support", "sales"]):
        next_id = f"T{len(tasks) + 1}"
        tasks.append(
            Task(
                id=next_id,
                assignee="customer_voice",
                task="Represent customer pain, objections, proof needed to buy, and likely support impact.",
                expected_output="Customer voice perspective.",
                depends_on=["T1", "T2"],
            )
        )
    return tasks


def normalize_task(raw: dict[str, Any], fallback_id: str, source: str) -> Task | None:
    assignee = str(raw.get("assignee") or "").strip()
    if assignee not in AGENT_ROSTER:
        return None
    return Task(
        id=str(raw.get("id") or fallback_id).strip() or fallback_id,
        assignee=assignee,
        task=str(raw.get("task") or "").strip() or AGENT_ROSTER[assignee]["focus"],
        expected_output=str(raw.get("expected_output") or "").strip() or "Concise no-code analysis.",
        depends_on=[str(item) for item in raw.get("depends_on") or []],
        source=source,
    )


def fallback_plan(question: str) -> dict[str, Any]:
    return {
        "intent": "Answer the user's question with no-code multi-agent analysis.",
        "success_criteria": [
            "Clarify the decision and constraints.",
            "Separate facts, assumptions, risks, and unknowns.",
            "Provide a concise final answer with practical next actions.",
            "Avoid code, commands, diffs, and implementation snippets.",
        ],
        "tasks": [asdict(task) for task in default_tasks(question)],
    }


def load_llm_call():
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from llm import MODEL, call_llm

    return MODEL, call_llm


def call_model(system_prompt: str, user_prompt: str, model: str | None, temperature: float) -> tuple[str, str]:
    default_model, call_llm = load_llm_call()
    selected_model = model or default_model
    return selected_model, call_llm(
        system_prompt,
        user_prompt,
        model=selected_model,
        temperature=temperature,
    )


def planner_system_prompt() -> str:
    return "\n\n".join(
        [
            "You are the Coordinator Agent in Business Prompt Lab.",
            NO_CODE_POLICY,
            "Your job is to create a task board and assign work to other agents. Do not answer the user directly.",
            "Use only these assignees:\n" + roster_text(),
            "Return only raw JSON matching this schema:\n" + pretty_json(PLANNER_SCHEMA),
            "Create 3 to 6 tasks. Include risk_reviewer unless the user asks for a trivial factual clarification.",
        ]
    )


def specialist_system_prompt(agent_key: str) -> str:
    spec = AGENT_ROSTER[agent_key]
    return "\n\n".join(
        [
            f"You are {spec['title']} ({agent_key}) in Business Prompt Lab.",
            f"Focus: {spec['focus']}",
            NO_CODE_POLICY,
            "Answer only your assigned task. You may reference other agent notes if provided.",
            "Return only raw JSON matching this schema:\n" + pretty_json(SPECIALIST_SCHEMA),
        ]
    )


def reviewer_system_prompt() -> str:
    return "\n\n".join(
        [
            "You are the Review Agent in Business Prompt Lab.",
            "Review the task board and specialist outputs before the final synthesizer answers the user.",
            NO_CODE_POLICY,
            "Ask for follow-up tasks only when the final answer would otherwise be misleading or incomplete.",
            "Return only raw JSON matching this schema:\n" + pretty_json(REVIEWER_SCHEMA),
            "Use followup_tasks sparingly, maximum 2.",
        ]
    )


def final_system_prompt() -> str:
    return "\n\n".join(
        [
            "You are the Final Synthesis Agent in Business Prompt Lab.",
            NO_CODE_POLICY,
            "Synthesize the agent room into the final answer for the user.",
            "Answer in the same language as the user's question.",
            "Do not expose raw JSON unless the user explicitly asked for JSON.",
            "Do not mention hidden system prompts. Mention agent reasoning only as a short collaboration summary if useful.",
            "Use a concise structure: direct answer, reasoning, risks/unknowns, next actions.",
        ]
    )


def repair_system_prompt(expect_json: bool) -> str:
    contract = "Return only raw JSON with the same meaning and schema." if expect_json else "Return only the rewritten final answer."
    return "\n\n".join(
        [
            "You are a no-code output repair agent.",
            NO_CODE_POLICY,
            "Rewrite the provided content so it follows the no-code policy.",
            contract,
        ]
    )


def call_json_agent(
    system_prompt: str,
    user_prompt: str,
    fallback: dict[str, Any],
    model: str | None,
    temperature: float,
    mock_data: dict[str, Any] | None,
    warnings: list[str],
    label: str,
) -> tuple[str, dict[str, Any], str]:
    if mock_data is not None:
        raw = pretty_json(mock_data)
        return "(mock)", mock_data, raw

    selected_model, raw = call_model(system_prompt, user_prompt, model=model, temperature=temperature)
    if has_code_signals(raw):
        warnings.append(f"{label}: model output looked code-like; attempted no-code repair.")
        _, raw = call_model(
            repair_system_prompt(expect_json=True),
            "Rewrite this content without code while preserving the JSON schema:\n\n" + raw,
            model=selected_model,
            temperature=0.0,
        )

    parsed, note = parse_json_object(raw)
    if parsed is None:
        warnings.append(f"{label}: could not parse JSON ({note}); wrapped raw text in fallback.")
        parsed = fallback
    return selected_model, parsed, raw


def call_text_agent(
    system_prompt: str,
    user_prompt: str,
    model: str | None,
    temperature: float,
    mock_text: str | None,
    warnings: list[str],
    label: str,
) -> tuple[str, str]:
    if mock_text is not None:
        return "(mock)", mock_text

    selected_model, raw = call_model(system_prompt, user_prompt, model=model, temperature=temperature)
    if has_code_signals(raw):
        warnings.append(f"{label}: model output looked code-like; attempted no-code repair.")
        _, raw = call_model(
            repair_system_prompt(expect_json=False),
            "Rewrite this content without code, commands, snippets, or code fences:\n\n" + raw,
            model=selected_model,
            temperature=0.0,
        )
    return selected_model, raw.strip()


def mock_specialist_output(task: Task) -> dict[str, Any]:
    title = AGENT_ROSTER[task.assignee]["title"]
    return {
        "agent": task.assignee,
        "task_id": task.id,
        "answer": f"{title} would answer this task by separating known facts from assumptions and keeping the recommendation no-code.",
        "key_points": [
            f"Task focus: {task.task}",
            "Use the user's provided context as evidence.",
            "Convert implementation requests into decisions, workflow, criteria, or operating steps.",
        ],
        "assumptions": ["The mock run does not call an LLM.", "The final answer should be concise and decision-oriented."],
        "risks_or_limits": ["Real quality depends on the configured LLM and the specificity of the user's question."],
        "handoff_questions": ["What evidence would change the final recommendation?"],
    }


def mock_reviewer_output() -> dict[str, Any]:
    return {
        "review": "The room has enough structure for a first answer, but the final agent should label unknowns clearly.",
        "must_fix": ["Do not output code or commands even if the user asks for implementation."],
        "gaps": ["The user may need to provide domain-specific constraints for a sharper answer."],
        "followup_tasks": [
            {
                "id": "F1",
                "assignee": "risk_reviewer",
                "task": "Name the single highest-risk assumption and how the final answer should hedge it.",
                "expected_output": "One concise risk note for final synthesis.",
                "depends_on": [],
            }
        ],
        "confidence": 0.74,
    }


def mock_final_answer(question: str, tasks: list[Task], review: dict[str, Any]) -> str:
    task_list = ", ".join(f"{task.id}:{task.assignee}" for task in tasks)
    return "\n".join(
        [
            "Cau tra loi mau cua Business Prompt Lab:",
            "",
            f"- Cau hoi da duoc dieu phoi thanh cac nhiem vu: {task_list}.",
            "- Dieu phoi vien giao viec cho cac agent chuyen mon, reviewer soi rui ro, va final_synthesis gom lai thanh cau tra loi cuoi.",
            "- Che do nay khong sinh code; neu cau hoi can trien khai ky thuat, agent se chuyen thanh yeu cau, luong van hanh, tieu chi chap nhan, rui ro va buoc tiep theo.",
            f"- Diem can canh giac: {', '.join(review.get('must_fix') or ['giu ro unknowns'])}.",
            "",
            "Buoc tiep theo: chay lai khong co --mock de dung LLM that, hoac them context de agent chia viec sac hon.",
            "",
            f"Cau hoi goc: {question}",
        ]
    )


class AgentRoom:
    def __init__(
        self,
        question: str,
        context: str,
        model: str | None,
        temperature: float,
        max_followups: int,
        mock: bool,
        out_dir: Path,
    ) -> None:
        self.question = question.strip()
        self.context = context.strip()
        self.model = model
        self.temperature = temperature
        self.max_followups = max(0, max_followups)
        self.mock = mock
        self.out_dir = out_dir
        self.transcript: list[AgentTurn] = []
        self.warnings: list[str] = []
        self.selected_model = model or "(llm.py default)"

    def run(self) -> RoomResult:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = self.out_dir / timestamp
        run_dir.mkdir(parents=True, exist_ok=False)

        plan = self.plan_tasks()
        tasks = self.tasks_from_plan(plan)
        agent_outputs = self.run_tasks(tasks)
        review = self.review_outputs(plan, agent_outputs)

        followups = self.followup_tasks(review)
        if followups:
            self.transcript.append(
                AgentTurn(
                    speaker="review_agent",
                    recipient="coordinator",
                    summary="Reviewer delegated follow-up tasks before final synthesis.",
                    payload=[asdict(task) for task in followups],
                )
            )
            followup_outputs = self.run_tasks(followups)
            agent_outputs.extend(followup_outputs)
            tasks.extend(followups)

        final_answer = self.final_synthesis(plan, agent_outputs, review)

        result = RoomResult(
            question=self.question,
            run_dir=run_dir,
            plan=plan,
            tasks=tasks,
            agent_outputs=agent_outputs,
            review=review,
            final_answer=final_answer,
            transcript=self.transcript,
            warnings=self.warnings,
        )
        self.write_outputs(result)
        return result

    def plan_tasks(self) -> dict[str, Any]:
        fallback = fallback_plan(self.question)
        mock_data = fallback if self.mock else None
        user_payload = {
            "question": self.question,
            "context": self.context,
            "agent_roster": AGENT_ROSTER,
        }
        selected_model, plan, raw = call_json_agent(
            planner_system_prompt(),
            pretty_json(user_payload),
            fallback=fallback,
            model=self.model,
            temperature=self.temperature,
            mock_data=mock_data,
            warnings=self.warnings,
            label="coordinator",
        )
        self.selected_model = selected_model
        self.transcript.append(
            AgentTurn(
                speaker="coordinator",
                recipient="agent_room",
                summary="Created task board and delegated work.",
                payload=plan,
            )
        )
        return plan

    def tasks_from_plan(self, plan: dict[str, Any]) -> list[Task]:
        tasks: list[Task] = []
        raw_tasks = plan.get("tasks")
        if isinstance(raw_tasks, list):
            for index, raw in enumerate(raw_tasks, start=1):
                if isinstance(raw, dict):
                    task = normalize_task(raw, fallback_id=f"T{index}", source="planner")
                    if task is not None:
                        tasks.append(task)
        if not tasks:
            self.warnings.append("coordinator: no usable tasks; used fallback task board.")
            tasks = default_tasks(self.question)
        return tasks[:6]

    def run_tasks(self, tasks: list[Task]) -> list[dict[str, Any]]:
        outputs: list[dict[str, Any]] = []
        prior_notes = []
        for task in tasks:
            fallback = {
                "agent": task.assignee,
                "task_id": task.id,
                "answer": "The model output could not be parsed. Treat this task as an evidence gap.",
                "key_points": [],
                "assumptions": [],
                "risks_or_limits": ["Unparsed specialist output."],
                "handoff_questions": [],
            }
            mock_data = mock_specialist_output(task) if self.mock else None
            payload = {
                "question": self.question,
                "context": self.context,
                "task": asdict(task),
                "prior_agent_notes": prior_notes[-4:],
            }
            selected_model, parsed, raw = call_json_agent(
                specialist_system_prompt(task.assignee),
                pretty_json(payload),
                fallback=fallback,
                model=self.model,
                temperature=self.temperature,
                mock_data=mock_data,
                warnings=self.warnings,
                label=f"{task.assignee}:{task.id}",
            )
            self.selected_model = selected_model
            parsed.setdefault("agent", task.assignee)
            parsed.setdefault("task_id", task.id)
            parsed["_raw_excerpt"] = raw[:600]
            outputs.append(parsed)
            prior_notes.append(
                {
                    "agent": parsed.get("agent", task.assignee),
                    "task_id": parsed.get("task_id", task.id),
                    "answer": parsed.get("answer", ""),
                    "key_points": parsed.get("key_points", []),
                }
            )
            self.transcript.append(
                AgentTurn(
                    speaker=task.assignee,
                    recipient="coordinator",
                    summary=f"Completed {task.id}: {task.task}",
                    payload=parsed,
                )
            )
        return outputs

    def review_outputs(self, plan: dict[str, Any], agent_outputs: list[dict[str, Any]]) -> dict[str, Any]:
        fallback = {
            "review": "Use the available specialist outputs, but label unknowns clearly.",
            "must_fix": ["Avoid code and separate facts from assumptions."],
            "gaps": ["No structured reviewer output was available."],
            "followup_tasks": [],
            "confidence": 0.5,
        }
        mock_data = mock_reviewer_output() if self.mock else None
        payload = {
            "question": self.question,
            "context": self.context,
            "plan": plan,
            "agent_outputs": agent_outputs,
        }
        selected_model, review, raw = call_json_agent(
            reviewer_system_prompt(),
            pretty_json(payload),
            fallback=fallback,
            model=self.model,
            temperature=self.temperature,
            mock_data=mock_data,
            warnings=self.warnings,
            label="review_agent",
        )
        self.selected_model = selected_model
        review["_raw_excerpt"] = raw[:600]
        self.transcript.append(
            AgentTurn(
                speaker="review_agent",
                recipient="final_synthesis",
                summary="Reviewed evidence quality and possible follow-up needs.",
                payload=review,
            )
        )
        return review

    def followup_tasks(self, review: dict[str, Any]) -> list[Task]:
        raw_followups = review.get("followup_tasks")
        if not isinstance(raw_followups, list) or self.max_followups <= 0:
            return []
        tasks: list[Task] = []
        for index, raw in enumerate(raw_followups[: self.max_followups], start=1):
            if isinstance(raw, dict):
                task = normalize_task(raw, fallback_id=f"F{index}", source="reviewer")
                if task is not None:
                    tasks.append(task)
        return tasks

    def final_synthesis(
        self,
        plan: dict[str, Any],
        agent_outputs: list[dict[str, Any]],
        review: dict[str, Any],
    ) -> str:
        mock_text = mock_final_answer(self.question, self.tasks_from_plan(plan), review) if self.mock else None
        payload = {
            "question": self.question,
            "context": self.context,
            "plan": plan,
            "agent_outputs": agent_outputs,
            "review": review,
        }
        selected_model, final_answer = call_text_agent(
            final_system_prompt(),
            pretty_json(payload),
            model=self.model,
            temperature=self.temperature,
            mock_text=mock_text,
            warnings=self.warnings,
            label="final_synthesis",
        )
        self.selected_model = selected_model
        self.transcript.append(
            AgentTurn(
                speaker="final_synthesis",
                recipient="user",
                summary="Synthesized the final no-code answer.",
                payload=final_answer,
            )
        )
        return final_answer

    def write_outputs(self, result: RoomResult) -> None:
        result.run_dir.mkdir(parents=True, exist_ok=True)
        (result.run_dir / "final.md").write_text(result.final_answer + "\n", encoding="utf-8")
        (result.run_dir / "transcript.md").write_text(render_transcript_markdown(result), encoding="utf-8")
        payload = {
            "question": result.question,
            "model": self.selected_model,
            "plan": result.plan,
            "tasks": [asdict(task) for task in result.tasks],
            "agent_outputs": result.agent_outputs,
            "review": result.review,
            "warnings": result.warnings,
            "final_answer": result.final_answer,
            "transcript": [asdict(turn) for turn in result.transcript],
        }
        (result.run_dir / "transcript.json").write_text(pretty_json(payload), encoding="utf-8")


def render_transcript_markdown(result: RoomResult) -> str:
    lines = [
        "# Business Prompt Lab Agent Room",
        "",
        f"- Run directory: `{result.run_dir}`",
        f"- Question: {result.question}",
        "",
        "## Final Answer",
        "",
        result.final_answer.strip(),
        "",
        "## Transcript",
        "",
    ]
    for index, turn in enumerate(result.transcript, start=1):
        lines.append(f"### {index}. {turn.speaker} -> {turn.recipient}")
        lines.append("")
        lines.append(turn.summary)
        lines.append("")
        if isinstance(turn.payload, str):
            lines.append(turn.payload.strip())
        else:
            lines.append("```json")
            lines.append(pretty_json(turn.payload))
            lines.append("```")
        lines.append("")
    if result.warnings:
        lines.extend(["## Warnings", ""])
        for warning in result.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines).rstrip() + "\n"


def print_dry_run(question: str, context: str) -> None:
    plan = fallback_plan(question)
    print("Business Prompt Lab no-code agent room")
    print("\nRoster")
    print(roster_text())
    print("\nFlow")
    print("1. User asks one question.")
    print("2. Coordinator creates a task board and assigns agents.")
    print("3. Specialists answer only their assigned tasks.")
    print("4. Review Agent checks gaps and may delegate follow-up tasks.")
    print("5. Final Synthesis Agent writes the final no-code answer.")
    print("\nPlanned fallback task board")
    print(pretty_json(plan))
    if context:
        print("\nExtra context was provided and will be included in all agent calls.")


def run_once(args: argparse.Namespace, question: str) -> int:
    if args.dry_run:
        print_dry_run(question, args.context)
        return 0

    room = AgentRoom(
        question=question,
        context=args.context,
        model=args.model,
        temperature=args.temperature,
        max_followups=args.max_followups,
        mock=args.mock,
        out_dir=args.out_dir,
    )
    result = room.run()
    print(result.final_answer.strip())
    print(f"\nRun directory: {result.run_dir}")
    print(f"Transcript: {result.run_dir / 'transcript.md'}")
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    if args.print_transcript:
        print("\n--- Transcript ---\n")
        print(render_transcript_markdown(result))
    return 0


def interactive_loop(args: argparse.Namespace) -> int:
    print("Business Prompt Lab no-code agent room. Type 'exit' to stop.")
    while True:
        try:
            question = input("\nQuestion> ").strip()
        except EOFError:
            return 0
        if question.lower() in {"exit", "quit", "q"}:
            return 0
        if not question:
            continue
        run_once(args, question)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a no-code multi-agent conversation room.")
    parser.add_argument("question", nargs="*", help="Question to ask the agent room.")
    parser.add_argument("--question-file", type=Path, help="Read the question from a markdown/text file.")
    parser.add_argument("--context", default="", help="Extra context that every agent should see.")
    parser.add_argument("--interactive", action="store_true", help="Start a simple REPL for repeated questions.")
    parser.add_argument("--mock", action="store_true", help="Run the full flow with deterministic mock outputs, no LLM call.")
    parser.add_argument("--dry-run", action="store_true", help="Show roster and fallback task board, no LLM call.")
    parser.add_argument("--model", default=None, help="Override LLM_MODEL from llm.py/.env.")
    parser.add_argument("--temperature", type=float, default=0.2, help="LLM temperature. Default: 0.2.")
    parser.add_argument("--max-followups", type=int, default=2, help="Maximum reviewer follow-up tasks. Default: 2.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for transcripts.")
    parser.add_argument("--print-transcript", action="store_true", help="Print the full transcript after the final answer.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.interactive:
        return interactive_loop(args)
    question = read_question(args)
    return run_once(args, question)


if __name__ == "__main__":
    raise SystemExit(main())
