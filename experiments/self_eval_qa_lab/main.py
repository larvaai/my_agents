from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parent
ROOT_DIR = LAB_DIR.parent.parent
PROMPT_DIR = LAB_DIR / "agents"
LENS_DIR = LAB_DIR / "lenses"
RUBRIC_DIR = LAB_DIR / "rubrics"
QUESTION_DIR = LAB_DIR / "questions"
ROUTING_POLICY_PATH = LAB_DIR / "routing_policy.yaml"
DEFAULT_OUT_DIR = ROOT_DIR / "var" / "self_eval_qa_lab"
DEFAULT_SERVER_API_KEY = "server"

DEFAULT_LENSES = ["architecture", "critic", "practical", "clarity", "no_leap"]
WORKFLOW_CHOICES = ["direct", "assisted", "deep", "repo_debug"]
JSON_AGENTS = {
    "question_classifier",
    "blind_evaluator",
    "error_analyzer",
    "flow_observer",
    "lesson_extractor",
    "critical_auditor",
    "evolution_decider",
}
ANSWER_CRITERIA = ["accuracy", "completeness", "clarity", "actionability", "constraint_following"]
FLOW_CRITERIA = ["flow_necessity", "routing_correctness", "step_efficiency", "error_visibility", "output_improvement"]


@dataclass(frozen=True)
class LabConfig:
    name: str = "self_eval_qa_lab"
    version: str = "0.3"
    default_lenses: list[str] = field(default_factory=lambda: list(DEFAULT_LENSES))
    default_llm_provider: str = "local"
    default_baseline_mode: str = "auto"
    self_update_enabled: bool = False
    proposal_only: bool = True


@dataclass(frozen=True)
class LLMOptions:
    provider: str = "local"
    model: str | None = None
    server_url: str | None = None
    server_api_key: str | None = None
    timeout: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class AnswerItem:
    source: str
    title: str
    answer: str


@dataclass(frozen=True)
class WorkflowDecision:
    question_type: str
    difficulty: str
    selected_workflow: str
    needs_baseline: bool
    needs_evaluation: bool
    max_steps: int
    reason: str


@dataclass
class LabResult:
    run_id: str
    run_dir: Path
    question: str
    run_plan: dict[str, Any]
    classification: dict[str, Any]
    workflow_decision: dict[str, Any]
    workflow_trace: list[dict[str, Any]]
    simple_answer: str
    our_answer: str
    chatgpt_answer: str | None
    chatgpt_comparison: dict[str, Any]
    baseline_answer: str | None
    lens_trace: list[dict[str, Any]]
    blind_pack: dict[str, Any]
    evaluation: dict[str, Any]
    revealed_evaluation: dict[str, Any]
    error_report: dict[str, Any]
    flow_observation: dict[str, Any]
    lesson_report: dict[str, Any]
    critical_audit: dict[str, Any]
    evolution_decision: dict[str, Any]
    trace_health: dict[str, Any]
    trace_events: list[dict[str, Any]]
    agent_calls: list[dict[str, Any]]
    update_proposal: dict[str, Any] | None
    warnings: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip().lower())
    return slug.strip("_") or "item"


def load_yaml(path: Path) -> dict[str, Any]:
    import yaml

    data = yaml.safe_load(read_text(path))
    return data if isinstance(data, dict) else {}


def load_config() -> LabConfig:
    path = LAB_DIR / "config.yaml"
    if not path.exists():
        return LabConfig()
    data = load_yaml(path)
    lab = data.get("lab") if isinstance(data.get("lab"), dict) else {}
    llm = data.get("llm") if isinstance(data.get("llm"), dict) else {}
    baseline = data.get("baseline") if isinstance(data.get("baseline"), dict) else {}
    self_update = data.get("self_update") if isinstance(data.get("self_update"), dict) else {}
    lenses = data.get("lenses") if isinstance(data.get("lenses"), dict) else {}
    default_lenses = lenses.get("default")
    if not isinstance(default_lenses, list):
        default_lenses = list(DEFAULT_LENSES)
    return LabConfig(
        name=str(lab.get("name") or "self_eval_qa_lab"),
        version=str(lab.get("version") or "0.3"),
        default_lenses=[str(item) for item in default_lenses],
        default_llm_provider=str(llm.get("default_provider") or "local"),
        default_baseline_mode=str(baseline.get("default_mode") or "auto"),
        self_update_enabled=bool(self_update.get("enabled", False)),
        proposal_only=bool(self_update.get("proposal_only", True)),
    )


def load_routing_policy() -> dict[str, Any]:
    if not ROUTING_POLICY_PATH.exists():
        return {}
    return load_yaml(ROUTING_POLICY_PATH)


def render_template(template: str, values: dict[str, Any]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def load_prompt(name: str) -> str:
    return read_text(PROMPT_DIR / f"{name}.md").strip()


def available_lenses() -> list[str]:
    return sorted(path.stem.replace("_lens", "") for path in LENS_DIR.glob("*_lens.md"))


def load_lens(name: str) -> str:
    safe_name = name.replace("-", "_")
    path = LENS_DIR / f"{safe_name}_lens.md"
    if not path.exists():
        raise KeyError(f"Unknown lens {name!r}. Known lenses: {', '.join(available_lenses())}")
    return read_text(path).strip()


def selected_lens_docs(lenses: list[str]) -> str:
    blocks = []
    for lens in lenses:
        try:
            blocks.append(f"## {lens}\n{load_lens(lens)}")
        except KeyError:
            continue
    return "\n\n".join(blocks)


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


def validate_json_agent_output(agent: str, parsed: dict[str, Any]) -> tuple[bool, str]:
    required_by_agent = {
        "question_classifier": ["task_type", "complexity", "needs_lens_flow", "suggested_lenses"],
        "blind_evaluator": ["scores", "winner"],
        "error_analyzer": ["summary", "where_ours_won", "where_ours_lost", "recommended_update_proposal"],
        "flow_observer": ["flow_quality_score", "routing_verdict"],
        "lesson_extractor": ["lessons", "apply_updates"],
        "critical_auditor": ["logic_score", "recommendation"],
        "evolution_decider": ["decision", "changes", "apply_updates"],
    }
    required = required_by_agent.get(agent, [])
    missing = [key for key in required if key not in parsed]
    if missing:
        return False, f"schema missing keys: {', '.join(missing)}"
    if agent == "blind_evaluator" and not isinstance(parsed.get("scores"), dict):
        return False, "schema invalid: scores must be an object"
    if agent == "blind_evaluator" and not parsed.get("scores"):
        return False, "schema invalid: scores is empty"
    if agent == "lesson_extractor" and not isinstance(parsed.get("lessons"), list):
        return False, "schema invalid: lessons must be a list"
    if agent == "evolution_decider" and not isinstance(parsed.get("changes"), list):
        return False, "schema invalid: changes must be a list"
    return True, "schema valid"


def env_first(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def build_llm_options(args: argparse.Namespace, config: LabConfig) -> LLMOptions:
    provider = str(args.llm_provider or config.default_llm_provider or "local").strip().lower()
    if provider not in {"local", "server"}:
        raise SystemExit(f"Unsupported --llm-provider {provider!r}; use local or server.")

    server_url = args.server_url or env_first("SELF_EVAL_SERVER_URL", "LLM_SERVER_URL")
    server_api_key = args.server_api_key or env_first("SELF_EVAL_SERVER_API_KEY", "LLM_SERVER_API_KEY")
    server_model = args.server_model or env_first("SELF_EVAL_SERVER_MODEL", "LLM_SERVER_MODEL")
    model = server_model if provider == "server" and server_model else args.model

    return LLMOptions(
        provider=provider,
        model=model,
        server_url=server_url,
        server_api_key=server_api_key,
        timeout=args.llm_timeout,
        max_tokens=args.max_tokens,
    )


def call_model(system_prompt: str, user_prompt: str, llm_options: LLMOptions, temperature: float) -> tuple[str, str]:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from llm import MODEL, call_llm

    if llm_options.provider == "server" and not llm_options.server_url:
        raise RuntimeError("Server LLM provider selected but no URL was provided. Set --server-url, SELF_EVAL_SERVER_URL, or LLM_SERVER_URL.")

    selected_model = llm_options.model or MODEL
    output = call_llm(
        system_prompt,
        user_prompt,
        model=selected_model,
        temperature=temperature,
        base_url=llm_options.server_url if llm_options.provider == "server" else None,
        api_key=(llm_options.server_api_key or DEFAULT_SERVER_API_KEY) if llm_options.provider == "server" else None,
        timeout=llm_options.timeout,
        max_tokens=llm_options.max_tokens,
    )
    return selected_model, output


def call_json_model(
    system_prompt: str,
    user_prompt: str,
    fallback: dict[str, Any],
    llm_options: LLMOptions,
    temperature: float,
    warnings: list[str],
    label: str,
) -> dict[str, Any]:
    _, raw = call_model(system_prompt, user_prompt, llm_options=llm_options, temperature=temperature)
    parsed, note = parse_json_object(raw)
    if parsed is None:
        warnings.append(f"{label}: JSON parse failed ({note}); used deterministic fallback.")
        return dict(fallback)
    return parsed


def estimate_complexity(question: str) -> str:
    lower = question.lower()
    tradeoff_tokens = [
        "architecture",
        "design",
        "trade-off",
        "tradeoff",
        "risk",
        "plan",
        "compare",
        "evaluate",
        "multi-agent",
        "agent",
        "strategy",
        "thiết kế",
        "thiet ke",
        "so sánh",
        "so sanh",
        "rủi ro",
        "rui ro",
        "kế hoạch",
        "ke hoach",
    ]
    hits = sum(1 for token in tradeoff_tokens if token in lower)
    if len(question) > 500 or hits >= 4:
        return "high"
    if len(question) > 160 or hits >= 2:
        return "medium"
    return "low"


def classify_question_deterministic(question: str, lenses: list[str]) -> dict[str, Any]:
    complexity = estimate_complexity(question)
    lower = question.lower()
    if is_benchmark_multiple_choice(question):
        return {
            "task_type": "benchmark_mcq",
            "complexity": "medium",
            "needs_lens_flow": False,
            "suggested_lenses": ["clarity"] if "clarity" in lenses else list(lenses[:1]),
            "reason": "Benchmark multiple-choice task should use a compact answer flow with strict final-answer contract.",
            "constraints": ["last non-empty line must be Answer: <letter>"],
            "unknowns": [],
        }
    suggested = []
    if any(token in lower for token in ["architecture", "design", "system", "module", "flow", "kiến trúc", "kien truc", "luồng", "luong"]):
        suggested.append("architecture")
    if any(token in lower for token in ["risk", "fail", "weak", "critic", "rủi ro", "rui ro", "sai", "ngu", "phức tạp", "phuc tap"]):
        suggested.append("critic")
    if any(token in lower for token in ["plan", "step", "implement", "roadmap", "triển khai", "trien khai", "bước", "buoc"]):
        suggested.append("practical")
    if any(token in lower for token in ["clear", "concise", "explain", "rõ", "ro", "dễ hiểu", "de hieu"]):
        suggested.append("clarity")
    if any(token in lower for token in ["assumption", "unknown", "evidence", "jump", "giả định", "gia dinh", "bằng chứng", "bang chung"]):
        suggested.append("no_leap")
    if not suggested:
        suggested = ["clarity"] if complexity == "low" else ["architecture", "critic", "practical"]
    suggested = [lens for lens in suggested if lens in lenses]
    if not suggested:
        suggested = list(lenses[:3])
    if any(token in lower for token in ["repo", "traceback", "test fail", "file", "bug", "error", "langgraph", "loi"]):
        task_type = "repo_debug"
    elif "agent" in lower or "architecture" in lower or "thiet ke" in lower:
        task_type = "technical_design"
    else:
        task_type = "general_qa"
    return {
        "task_type": task_type,
        "complexity": complexity,
        "needs_lens_flow": complexity in {"medium", "high"},
        "suggested_lenses": suggested[:4],
        "reason": "Deterministic classifier uses question length and trade-off keywords.",
        "constraints": [],
        "unknowns": ["No external research was performed by the classifier."],
    }


def _workflow_policy(policy: dict[str, Any], workflow: str) -> dict[str, Any]:
    workflows = policy.get("workflows") if isinstance(policy.get("workflows"), dict) else {}
    data = workflows.get(workflow) if isinstance(workflows.get(workflow), dict) else {}
    return data


def _keyword_rule_workflow(question: str, policy: dict[str, Any]) -> tuple[str | None, str | None]:
    lower = question.lower()
    rules = policy.get("rules") if isinstance(policy.get("rules"), dict) else {}
    for rule_name, rule in rules.items():
        if not isinstance(rule, dict):
            continue
        workflow = str(rule.get("workflow") or "")
        matches = rule.get("match") if isinstance(rule.get("match"), list) else []
        for token in matches:
            token_text = str(token).lower()
            if token_text and token_text in lower:
                return workflow, f"Matched routing rule {rule_name!r} on token {token_text!r}."
    return None, None


def route_workflow_deterministic(
    question: str,
    classification: dict[str, Any],
    policy: dict[str, Any] | None = None,
    forced_workflow: str | None = None,
) -> dict[str, Any]:
    policy = policy or {}
    complexity = str(classification.get("complexity") or estimate_complexity(question))
    selected = forced_workflow if forced_workflow in WORKFLOW_CHOICES else None
    reason = f"Forced workflow {selected!r} from CLI." if selected else ""
    question_type = str(classification.get("task_type") or "general_qa")

    if not selected and question_type == "benchmark_mcq":
        selected = "assisted"
        reason = "Benchmark multiple-choice route: use assisted answer flow; avoid deep/repo_debug paths that hurt parse reliability."

    if not selected:
        rule_workflow, rule_reason = _keyword_rule_workflow(question, policy)
        if rule_workflow in WORKFLOW_CHOICES:
            selected = rule_workflow
            reason = rule_reason or "Matched routing policy."

    if not selected:
        lower = question.lower()
        if any(token in lower for token in ["repo", "traceback", "test fail", "file", "bug", "error", "langgraph"]):
            selected = "repo_debug"
            reason = "Repo/debug keyword route."
        elif complexity == "high":
            selected = "deep"
            reason = "High-complexity question needs a deeper answer flow."
        elif complexity == "medium" or bool(classification.get("needs_lens_flow")):
            selected = "assisted"
            reason = "Medium-complexity question benefits from draft-review-rewrite."
        else:
            selected = "direct"
            reason = "Low-complexity question should stay direct."

    workflow_data = _workflow_policy(policy, selected)
    needs_baseline = bool(workflow_data.get("needs_baseline", selected == "deep"))
    needs_evaluation = bool(workflow_data.get("needs_evaluation", selected != "direct"))
    max_steps = int(workflow_data.get("max_steps") or {"direct": 2, "assisted": 4, "deep": 6, "repo_debug": 5}[selected])
    difficulty = str(workflow_data.get("difficulty") or complexity)
    return {
        "question_type": question_type,
        "difficulty": difficulty,
        "selected_workflow": selected,
        "needs_baseline": needs_baseline,
        "needs_evaluation": needs_evaluation,
        "max_steps": max_steps,
        "reason": reason,
    }


def trace_step(step: str, agent: str, summary: str, useful: bool = True, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    item = {
        "step": step,
        "agent": agent,
        "summary": summary,
        "useful": useful,
    }
    if metadata:
        item["metadata"] = metadata
    return item


class RunRecorder:
    def __init__(self, run_id: str, run_dir: Path) -> None:
        self.run_id = run_id
        self.run_dir = run_dir
        self.sequence = 0
        self.events: list[dict[str, Any]] = []
        self.agent_calls: list[dict[str, Any]] = []
        self.handoffs: list[dict[str, Any]] = []

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.run_dir).as_posix()

    def write_artifact(self, folder: str, name: str, content: str) -> str:
        path = self.run_dir / folder / name
        write_text(path, content)
        return self._relative(path)

    def record_event(
        self,
        event_type: str,
        agent: str,
        step: str,
        *,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        output: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        public_rationale: str | None = None,
        handoff_to: str | None = None,
        handoff_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.sequence += 1
        event_id = f"evt_{self.sequence:04d}"
        slug = f"{self.sequence:04d}_{safe_slug(agent)}_{safe_slug(step)}"
        prompt_refs: dict[str, str] = {}
        output_ref = None
        if system_prompt is not None:
            prompt_refs["system"] = self.write_artifact("prompts", f"{slug}.system.md", system_prompt)
        if user_prompt is not None:
            prompt_refs["user"] = self.write_artifact("prompts", f"{slug}.user.md", user_prompt)
        if output is not None:
            output_ref = self.write_artifact("outputs", f"{slug}.md", output)
        event = {
            "event_id": event_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "timestamp": utc_timestamp(),
            "event_type": event_type,
            "agent": agent,
            "step": step,
            "model": model,
            "provider": provider,
            "prompt_refs": prompt_refs,
            "output_ref": output_ref,
            "char_counts": {
                "system_prompt": len(system_prompt or ""),
                "user_prompt": len(user_prompt or ""),
                "output": len(output or ""),
            },
            "public_rationale": public_rationale,
            "handoff_to": handoff_to,
            "handoff_reason": handoff_reason,
            "metadata": metadata or {},
        }
        full_call = dict(event)
        full_call["system_prompt"] = system_prompt
        full_call["user_prompt"] = user_prompt
        full_call["output"] = output
        self.events.append(event)
        append_jsonl(self.run_dir / "traces" / "events.jsonl", event)
        if event_type in {"agent_call", "agent_output", "agent_skipped"}:
            self.agent_calls.append(full_call)
            append_jsonl(self.run_dir / "traces" / "agent_calls.jsonl", event)
        if handoff_to:
            handoff = {
                "event_id": event_id,
                "from": agent,
                "to": handoff_to,
                "reason": handoff_reason,
                "timestamp": event["timestamp"],
            }
            self.handoffs.append(handoff)
            append_jsonl(self.run_dir / "traces" / "handoffs.jsonl", handoff)
        return event

    def flush_admin_trace(self) -> None:
        payload = {
            "run_id": self.run_id,
            "generated_at": utc_timestamp(),
            "policy_note": (
                "This admin trace stores prompts, inputs, raw model outputs, public rationales, and handoffs without truncation. "
                "It does not expose hidden internal chain-of-thought that the model did not emit."
            ),
            "events": self.events,
            "agent_calls_full": self.agent_calls,
            "handoffs": self.handoffs,
        }
        write_text(self.run_dir / "admin" / "full_trace.json", pretty_json(payload) + "\n")


def normalize_output_for_compare(value: str) -> str:
    text = re.sub(r"\s+", " ", value.strip().lower())
    text = re.sub(r"[`*_#>\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def output_similarity(left: str, right: str) -> float:
    a = normalize_output_for_compare(left)
    b = normalize_output_for_compare(right)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def text_contains_code_block(value: str) -> bool:
    return bool(re.search(r"```|^\s*(def|class|import|npm|pip|git)\s+", value, re.MULTILINE))


def prompt_allows_code(system_prompt: str, user_prompt: str) -> bool:
    text = f"{system_prompt}\n{user_prompt}".lower()
    no_code_markers = ["do not write code", "do not generate code", "khong viet code", "không viết code", "no code"]
    if any(marker in text for marker in no_code_markers):
        return False
    ask_code_markers = ["write code", "generate code", "viet code", "viết code", "show code"]
    return any(marker in text for marker in ask_code_markers)


def analyze_trace_health(
    agent_calls: list[dict[str, Any]],
    handoffs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    handoffs = handoffs or []
    repeated_outputs: list[dict[str, Any]] = []
    empty_or_tiny_outputs: list[dict[str, Any]] = []
    json_fallbacks: list[dict[str, Any]] = []
    code_violations: list[dict[str, Any]] = []
    duplicate_agent_steps: list[dict[str, Any]] = []
    handoff_loops: list[dict[str, Any]] = []
    seen_agent_steps: set[tuple[str, str]] = set()

    comparable = []
    for call in agent_calls:
        agent = str(call.get("agent") or "")
        step = str(call.get("step") or "")
        event_type = str(call.get("event_type") or "")
        output = str(call.get("output") or "")
        provider = str(call.get("provider") or "")
        metadata = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        if metadata.get("superseded_by_repair"):
            continue
        if event_type != "agent_skipped" and len(output.strip()) < 20:
            empty_or_tiny_outputs.append({"agent": agent, "step": step, "chars": len(output.strip())})
        if metadata.get("used_fallback"):
            json_fallbacks.append({"agent": agent, "step": step, "parse_status": metadata.get("json_parse_status")})
        if agent not in JSON_AGENTS and text_contains_code_block(output):
            code_violations.append({"agent": agent, "step": step, "reason": "Output appears to include code or shell/code block."})
        key = (agent, step)
        if key in seen_agent_steps and event_type != "agent_skipped":
            duplicate_agent_steps.append({"agent": agent, "step": step})
        seen_agent_steps.add(key)
        if metadata.get("pass_through") or metadata.get("mock_baseline"):
            continue
        if event_type != "agent_skipped" and not agent.endswith("_sanitizer") and len(output.strip()) >= 80:
            comparable.append((agent, step, output))

    for index, (agent_a, step_a, output_a) in enumerate(comparable):
        for agent_b, step_b, output_b in comparable[index + 1 :]:
            if agent_a == agent_b:
                continue
            ratio = output_similarity(output_a, output_b)
            if ratio >= 0.92:
                repeated_outputs.append(
                    {
                        "left": f"{agent_a}.{step_a}",
                        "right": f"{agent_b}.{step_b}",
                        "similarity": round(ratio, 3),
                    }
                )

    seen_edges: set[tuple[str, str]] = set()
    for handoff in handoffs:
        source = str(handoff.get("from") or "")
        target = str(handoff.get("to") or "")
        if source == target and source:
            handoff_loops.append({"from": source, "to": target, "reason": "Self-handoff."})
        if (target, source) in seen_edges:
            handoff_loops.append({"from": source, "to": target, "reason": "Back-and-forth handoff edge."})
        seen_edges.add((source, target))

    severe_count = len(json_fallbacks) + len(handoff_loops) + len(code_violations)
    concern_count = severe_count + len(repeated_outputs) + len(empty_or_tiny_outputs) + len(duplicate_agent_steps)
    looping_detected = bool(repeated_outputs or handoff_loops or duplicate_agent_steps)
    return {
        "status": "clean" if concern_count == 0 else "needs_review",
        "looping_detected": looping_detected,
        "severe_count": severe_count,
        "concern_count": concern_count,
        "repeated_outputs": repeated_outputs[:10],
        "empty_or_tiny_outputs": empty_or_tiny_outputs[:10],
        "json_fallbacks": json_fallbacks[:10],
        "code_violations": code_violations[:10],
        "duplicate_agent_steps": duplicate_agent_steps[:10],
        "handoff_loops": handoff_loops[:10],
        "policy": {
            "max_repeated_outputs": 0,
            "max_json_fallbacks_for_real_llm": 0,
            "max_code_violations": 0,
            "max_handoff_loops": 0,
        },
    }


def critique_requests_material_rewrite(critique: str) -> bool:
    lower = normalize_output_for_compare(critique)
    material_markers = [
        "missing",
        "lacks",
        "needs",
        "should add",
        "should mention",
        "overclaim",
        "incorrect",
        "weakness",
        "risk",
        "not answer",
        "thieu",
        "can them",
        "sai",
        "rui ro",
    ]
    no_material_markers = [
        "no material",
        "no major",
        "already",
        "sufficient",
        "solid",
        "good enough",
        "khong can",
    ]
    has_material = any(marker in lower for marker in material_markers)
    has_no_material = any(marker in lower for marker in no_material_markers)
    return has_material and not has_no_material


def is_benchmark_multiple_choice(question: str) -> bool:
    lower = question.lower()
    return (
        "benchmark task: multiple-choice reasoning" in lower
        and "options:" in lower
        and "answer: <letter>" in lower
    )


def benchmark_answer_contract(question: str) -> str:
    if not is_benchmark_multiple_choice(question):
        return ""
    return (
        "Benchmark multiple-choice contract: choose exactly one option. "
        "The last non-empty line must be exactly `Answer: <letter>` with one valid option letter. "
        "Do not end with prose after that final answer line."
    )


def has_benchmark_final_answer(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    return bool(re.match(r"(?i)^answer\s*:\s*[A-Z]\.?$", lines[-1]))


def heuristic_answer(question: str, title: str, lenses: list[str] | None = None) -> str:
    if is_benchmark_multiple_choice(question):
        return "\n".join(
            [
                f"{title}:",
                "",
                "I could not obtain a reliable model answer for this benchmark case.",
                "This deterministic fallback is intentionally unparseable so scoring does not treat it as model evidence.",
                "",
                "Answer: UNKNOWN",
            ]
        )
    lens_text = ", ".join(lenses or [])
    lines = [
        f"{title}:",
        "",
        "Short answer: start with the smallest answer flow that can be measured, then add complexity only when it beats a simpler baseline.",
        "",
        "Reasoning:",
        "- Keep a simple answer baseline so the lab can detect when lens or agent flow is not helping.",
        "- Use lens-based review before specialist agents because lenses are cheaper, easier to trace, and easier to remove.",
        "- Separate answer evaluation from flow observation so quality and process cost do not get mixed.",
        "- Store every run in a ledger with the question, answers, scores, errors, and flow verdict.",
    ]
    if lenses:
        lines.extend(
            [
                "",
                f"Applied lenses: {lens_text}.",
                "Next move: run 20 to 30 sample questions and remove any lens that does not improve score or error visibility.",
            ]
        )
    lines.extend(["", f"Question: {question}"])
    return "\n".join(lines)


def score_answer_text(answer: str, question: str) -> dict[str, int]:
    lower = answer.lower()
    length = len(answer.strip())
    scores = {
        "accuracy": 7,
        "completeness": 5,
        "clarity": 6,
        "actionability": 5,
        "constraint_following": 7,
    }
    if 300 <= length <= 2500:
        scores["clarity"] += 1
        scores["completeness"] += 1
    if any(token in lower for token in ["next", "step", "action", "buoc", "bước", "plan"]):
        scores["actionability"] += 2
    if any(token in lower for token in ["risk", "unknown", "assumption", "rui ro", "giả định", "gia dinh"]):
        scores["completeness"] += 1
        scores["constraint_following"] += 1
    if "```" in answer or re.search(r"^\s*(def|class|import|npm|pip|git)\s+", answer, re.MULTILINE):
        scores["constraint_following"] -= 2
        scores["clarity"] -= 1
    if len(question) > 200 and length < 350:
        scores["completeness"] -= 1
    return {key: max(0, min(10, value)) for key, value in scores.items()}


def weighted_total(scores: dict[str, int], rubric: dict[str, Any]) -> int:
    criteria = rubric.get("criteria") if isinstance(rubric.get("criteria"), dict) else {}
    total = 0
    max_total = 0
    for key in ANSWER_CRITERIA:
        weight = 1
        if isinstance(criteria.get(key), dict):
            weight = int(criteria[key].get("weight") or 1)
        total += int(scores.get(key, 0)) * weight
        max_total += 10 * weight
    if max_total == 0:
        return 0
    return round((total / max_total) * 100)


def deterministic_evaluation(question: str, visible_answers: dict[str, str], rubric: dict[str, Any]) -> dict[str, Any]:
    scores: dict[str, Any] = {}
    for label, answer in visible_answers.items():
        base_scores = score_answer_text(answer, question)
        base_scores["total"] = weighted_total(base_scores, rubric)
        scores[label] = base_scores
    best_total = max(item["total"] for item in scores.values()) if scores else 0
    winners = [label for label, item in scores.items() if item["total"] == best_total]
    winner = "tie" if len(winners) != 1 else winners[0]
    notes = {
        label: {
            "strengths": ["Structured enough for deterministic evaluation."],
            "weaknesses": ["Heuristic scoring cannot verify factual accuracy."],
        }
        for label in visible_answers
    }
    return {
        "scores": scores,
        "winner": winner,
        "reason": "Deterministic evaluator uses answer length, actionability, risk handling, and constraint signals.",
        "answer_notes": notes,
    }


def reveal_evaluation(evaluation: dict[str, Any], hidden_mapping: dict[str, str]) -> dict[str, Any]:
    scores = evaluation.get("scores") if isinstance(evaluation.get("scores"), dict) else {}
    scores_by_source = {}
    for label, source in hidden_mapping.items():
        if label in scores:
            scores_by_source[source] = scores[label]
    winner = str(evaluation.get("winner") or "tie")
    winner_source = "tie" if winner == "tie" else hidden_mapping.get(winner, winner)
    revealed = dict(evaluation)
    revealed["scores_by_source"] = scores_by_source
    revealed["winner_source"] = winner_source
    revealed["hidden_mapping"] = hidden_mapping
    return revealed


def deterministic_error_report(revealed_evaluation: dict[str, Any]) -> dict[str, Any]:
    scores = revealed_evaluation.get("scores_by_source") if isinstance(revealed_evaluation.get("scores_by_source"), dict) else {}
    ours = scores.get("ours", {})
    where_lost = []
    where_won = []
    for key in ANSWER_CRITERIA + ["total"]:
        our_value = int(ours.get(key, 0)) if isinstance(ours, dict) else 0
        other_values = [
            int(item.get(key, 0))
            for source, item in scores.items()
            if source != "ours" and isinstance(item, dict)
        ]
        best_other = max(other_values) if other_values else 0
        if our_value < best_other:
            where_lost.append(f"ours lower on {key}: {our_value} vs {best_other}")
        elif our_value > best_other:
            where_won.append(f"ours higher on {key}: {our_value} vs {best_other}")
    return {
        "summary": "Deterministic error report compares revealed scores by source.",
        "where_ours_won": where_won[:5],
        "where_ours_lost": where_lost[:5],
        "repeated_error_candidates": ["needs more examples"] if where_lost else [],
        "rubric_mismatch": [],
        "recommended_update_proposal": {
            "enabled": False,
            "reason": "Phase 1 records evidence only; no automatic skill or lens update.",
            "requires_human_approval": True,
        },
    }


def expected_workflow_for_question(classification: dict[str, Any]) -> str:
    task_type = str(classification.get("task_type") or "")
    complexity = str(classification.get("complexity") or "low")
    suggested_lenses = {str(item) for item in classification.get("suggested_lenses") or []}
    if task_type == "repo_debug":
        return "repo_debug"
    if task_type == "technical_design" and complexity in {"medium", "high"} and "architecture" in suggested_lenses:
        return "deep"
    if complexity == "high":
        return "deep"
    if complexity == "medium" or bool(classification.get("needs_lens_flow")):
        return "assisted"
    return "direct"


def deterministic_flow_observation(
    classification: dict[str, Any],
    lens_trace: list[dict[str, Any]],
    revealed_evaluation: dict[str, Any],
    baseline_mode: str,
    workflow_decision: dict[str, Any] | None = None,
    workflow_trace: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    complexity = str(classification.get("complexity") or "low")
    needs_lens_flow = bool(classification.get("needs_lens_flow"))
    lens_count = len(lens_trace)
    winner_source = revealed_evaluation.get("winner_source")
    workflow_decision = workflow_decision or {}
    workflow_trace = workflow_trace or []
    selected_workflow = str(workflow_decision.get("selected_workflow") or ("deep" if lens_count else "direct"))
    expected_workflow = expected_workflow_for_question(classification)
    router_reason = str(workflow_decision.get("reason") or "")
    route_difficulty = str(workflow_decision.get("difficulty") or "")
    if not router_reason.startswith("Forced workflow") and selected_workflow in WORKFLOW_CHOICES:
        if selected_workflow == "repo_debug":
            expected_workflow = "repo_debug"
        elif selected_workflow == "deep" and route_difficulty == "high":
            expected_workflow = "deep"
        elif selected_workflow == "assisted" and route_difficulty == "medium":
            expected_workflow = "assisted"
        elif selected_workflow == "direct" and route_difficulty == "low":
            expected_workflow = "direct"
    needs_baseline = bool(workflow_decision.get("needs_baseline", selected_workflow == "deep"))

    wasted: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    unnecessary_agents: list[str] = []
    missing_agents: list[str] = []
    role_violations: list[str] = []
    handoff_issues: list[str] = []

    if complexity == "low" and (
        lens_count > 0 or selected_workflow == "deep" or (selected_workflow == "assisted" and expected_workflow != "assisted")
    ):
        wasted.append({"step": "lens_flow", "reason": "Low-complexity question probably did not need a lens or multi-agent flow."})
        if selected_workflow == "assisted":
            unnecessary_agents.extend(["critic", "answer_synthesizer"])
        else:
            unnecessary_agents.extend(["critic", "lens_answer"])
    if selected_workflow == "deep" and expected_workflow != "deep":
        wasted.append({"step": "deep_workflow", "reason": "Deep workflow was selected when the expected workflow was smaller."})
    if selected_workflow == "direct" and needs_lens_flow:
        missing.append({"step": "review_or_lens_flow", "reason": "Classifier marked the question as complex enough for review."})
        missing_agents.extend(["critic", "practical"])
    if lens_count == 0 and selected_workflow == "deep":
        missing.append({"step": "lens_flow", "reason": "Deep workflow needs explicit lenses in the trace."})
        missing_agents.append("lens_answer")
    if selected_workflow == "repo_debug" and baseline_mode == "local":
        wasted.append({"step": "baseline_answer", "reason": "Repo/debug questions should not default to an external baseline."})
        unnecessary_agents.append("baseline")
    if needs_baseline and baseline_mode in {"none", "auto_skipped"}:
        missing.append({"step": "baseline_answer", "reason": "Selected workflow requested a baseline but no baseline was run."})
        missing_agents.append("baseline")
    if not workflow_trace:
        handoff_issues.append("No workflow trace was recorded.")
    if selected_workflow not in WORKFLOW_CHOICES:
        role_violations.append(f"Unknown workflow {selected_workflow!r}.")

    workflow_score = 8
    if winner_source == "ours":
        workflow_score += 1
    if selected_workflow == expected_workflow:
        workflow_score += 1
    if wasted:
        workflow_score -= 3
    if missing:
        workflow_score -= 3
    if role_violations:
        workflow_score -= 2
    if handoff_issues:
        workflow_score -= 1
    workflow_score = max(0, min(10, workflow_score))

    if selected_workflow != expected_workflow:
        workflow_verdict = "OVER_ROUTED" if selected_workflow in {"assisted", "deep"} and expected_workflow == "direct" else "UNDER_ROUTED"
    elif missing:
        workflow_verdict = "UNDER_ROUTED"
    elif wasted:
        workflow_verdict = "OVER_ROUTED"
    elif workflow_score >= 8:
        workflow_verdict = "GOOD"
    else:
        workflow_verdict = "PARTIAL"

    if workflow_verdict == "GOOD":
        routing_verdict = "good"
    elif workflow_verdict == "PARTIAL":
        routing_verdict = "partially_good"
    else:
        routing_verdict = "weak"

    recommended_next_flow = ["question_classifier", "workflow_router"]
    if expected_workflow == "direct":
        recommended_next_flow.append("direct_answer")
    elif expected_workflow == "assisted":
        recommended_next_flow.extend(["draft_answer", "critic", "rewrite"])
    elif expected_workflow == "deep":
        recommended_next_flow.extend(["lens_answer", "blind_evaluator", "flow_observer"])
    else:
        recommended_next_flow.extend(["repo_context_reader", "debug_reasoner", "answer_synthesizer"])

    anti_patterns = []
    if selected_workflow == "deep" and expected_workflow == "direct":
        anti_patterns.append("multi_agent_theater")
    if needs_baseline and baseline_mode in {"none", "auto_skipped"}:
        anti_patterns.append("missing_requested_baseline")

    return {
        "flow_quality_score": workflow_score,
        "workflow_score": workflow_score,
        "selected_workflow": selected_workflow,
        "recommended_workflow": expected_workflow,
        "workflow_verdict": workflow_verdict,
        "was_lens_flow_justified": selected_workflow == "deep" and needs_lens_flow and not wasted,
        "wasted_steps": wasted,
        "missing_steps": missing,
        "unnecessary_agents": sorted(set(unnecessary_agents)),
        "missing_agents": sorted(set(missing_agents)),
        "role_violations": role_violations,
        "handoff_issues": handoff_issues,
        "routing_verdict": routing_verdict,
        "recommended_next_flow": recommended_next_flow,
        "router_update_candidate": workflow_verdict in {"OVER_ROUTED", "UNDER_ROUTED"},
        "anti_patterns_detected": anti_patterns,
    }


def deterministic_lesson_report(
    workflow_decision: dict[str, Any],
    flow_observation: dict[str, Any],
    error_report: dict[str, Any],
) -> dict[str, Any]:
    lessons: list[dict[str, Any]] = []
    workflow_verdict = str(flow_observation.get("workflow_verdict") or "")
    selected = str(workflow_decision.get("selected_workflow") or "")
    recommended = str(flow_observation.get("recommended_workflow") or "")
    if workflow_verdict in {"OVER_ROUTED", "UNDER_ROUTED"}:
        lessons.append(
            {
                "lesson_type": "routing",
                "selected_workflow": selected,
                "recommended_workflow": recommended,
                "signal": workflow_verdict,
                "proposal": "Tune routing_policy.yaml before changing prompts or lenses.",
            }
        )
    if error_report.get("where_ours_lost"):
        lessons.append(
            {
                "lesson_type": "answer_quality",
                "selected_workflow": selected,
                "signal": "ours_lost_score_dimension",
                "proposal": "Collect more runs before proposing a prompt or lens update.",
            }
        )
    if not lessons:
        lessons.append(
            {
                "lesson_type": "keep",
                "selected_workflow": selected,
                "signal": "no_material_process_issue",
                "proposal": "Record evidence only.",
            }
        )
    return {
        "lessons": lessons,
        "update_policy": "proposal_only",
        "apply_updates": False,
        "reason": "v0.3 records lessons and router proposals; it does not mutate prompts, lenses, skills, tools, or code.",
    }


def deterministic_chatgpt_comparison(
    revealed_evaluation: dict[str, Any],
    chatgpt_answer: str | None,
) -> dict[str, Any]:
    if not chatgpt_answer:
        return {
            "status": "pending_manual_chatgpt_answer",
            "winner": "unknown",
            "reason": "ChatGPT prompt was saved, but no ChatGPT answer was available for scoring.",
            "score_delta_ours_minus_chatgpt": None,
        }
    scores = revealed_evaluation.get("scores_by_source") if isinstance(revealed_evaluation.get("scores_by_source"), dict) else {}
    ours = scores.get("ours") if isinstance(scores.get("ours"), dict) else {}
    chatgpt = scores.get("chatgpt") if isinstance(scores.get("chatgpt"), dict) else {}
    ours_total = int(ours.get("total", 0)) if isinstance(ours, dict) else 0
    chatgpt_total = int(chatgpt.get("total", 0)) if isinstance(chatgpt, dict) else 0
    if ours_total > chatgpt_total:
        winner = "ours"
    elif chatgpt_total > ours_total:
        winner = "chatgpt"
    else:
        winner = "tie"
    return {
        "status": "compared",
        "winner": winner,
        "ours_total": ours_total,
        "chatgpt_total": chatgpt_total,
        "score_delta_ours_minus_chatgpt": ours_total - chatgpt_total,
        "reason": "Deterministic comparison uses revealed blind-evaluation totals.",
    }


def deterministic_critical_audit(
    workflow_decision: dict[str, Any],
    workflow_trace: list[dict[str, Any]],
    agent_calls: list[dict[str, Any]],
    flow_observation: dict[str, Any],
    chatgpt_comparison: dict[str, Any],
    trace_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trace_health = trace_health or analyze_trace_health(agent_calls)
    wasted_agents = list(flow_observation.get("unnecessary_agents") or [])
    missing_agents = list(flow_observation.get("missing_agents") or [])
    bad_handoffs = list(flow_observation.get("handoff_issues") or [])
    role_violations = list(flow_observation.get("role_violations") or [])
    stupid_steps = []
    for item in workflow_trace:
        if isinstance(item, dict) and item.get("useful") is False:
            stupid_steps.append({"step": item.get("step"), "reason": item.get("summary", "Marked not useful.")})
    for call in agent_calls:
        if not call.get("output_ref") and call.get("event_type") != "agent_skipped":
            stupid_steps.append({"step": call.get("step"), "reason": f"{call.get('agent')} produced no recorded output."})
    for issue in trace_health.get("repeated_outputs") or []:
        stupid_steps.append({"step": issue.get("right"), "reason": f"Output too similar to {issue.get('left')} (similarity={issue.get('similarity')})."})
    for issue in trace_health.get("json_fallbacks") or []:
        stupid_steps.append({"step": f"{issue.get('agent')}.{issue.get('step')}", "reason": "Agent returned invalid JSON and fallback was used."})
    for issue in trace_health.get("handoff_loops") or []:
        bad_handoffs.append(f"{issue.get('from')} -> {issue.get('to')}: {issue.get('reason')}")

    score = int(flow_observation.get("workflow_score") or flow_observation.get("flow_quality_score") or 7)
    if chatgpt_comparison.get("winner") == "chatgpt":
        score -= 2
    if trace_health.get("severe_count", 0):
        score -= 2
    if trace_health.get("looping_detected"):
        score -= 2
    if stupid_steps:
        score -= 1
    score = max(0, min(10, score))

    if trace_health.get("looping_detected"):
        recommendation = "change_router"
    elif wasted_agents or flow_observation.get("workflow_verdict") == "OVER_ROUTED":
        recommendation = "simplify_flow"
    elif missing_agents or flow_observation.get("workflow_verdict") == "UNDER_ROUTED":
        recommendation = "deepen_flow"
    elif chatgpt_comparison.get("winner") == "chatgpt":
        recommendation = "improve_answer_flow"
    else:
        recommendation = "keep_flow"

    return {
        "logic_score": score,
        "selected_workflow": workflow_decision.get("selected_workflow"),
        "wasted_agents": wasted_agents,
        "missing_agents": missing_agents,
        "bad_handoffs": bad_handoffs,
        "role_violations": role_violations,
        "stupid_or_unhelpful_steps": stupid_steps[:10],
        "trace_health": trace_health,
        "chatgpt_signal": chatgpt_comparison,
        "recommendation": recommendation,
        "notes": "Critical audit uses recorded prompts, outputs, public rationales, handoffs, flow verdict, and ChatGPT comparison.",
    }


def deterministic_evolution_decision(
    critical_audit: dict[str, Any],
    flow_observation: dict[str, Any],
    lesson_report: dict[str, Any],
    chatgpt_comparison: dict[str, Any],
) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    for agent in critical_audit.get("wasted_agents") or []:
        changes.append(
            {
                "type": "remove_or_gate_agent",
                "target": agent,
                "reason": "Critical audit marked this agent as unnecessary for the selected workflow.",
                "proposal": "Gate this agent behind a stricter routing rule before deleting it.",
            }
        )
    for agent in critical_audit.get("missing_agents") or []:
        changes.append(
            {
                "type": "add_or_restore_agent",
                "target": agent,
                "reason": "Critical audit marked this agent as missing.",
                "proposal": "Add this agent only for workflows where repeated runs show the same gap.",
            }
        )
    if flow_observation.get("router_update_candidate"):
        changes.append(
            {
                "type": "modify_routing_policy",
                "target": "routing_policy.yaml",
                "reason": f"Workflow verdict was {flow_observation.get('workflow_verdict')}.",
                "proposal": "Adjust keyword or difficulty rules before changing prompts.",
            }
        )
    trace_health = critical_audit.get("trace_health") if isinstance(critical_audit.get("trace_health"), dict) else {}
    if trace_health.get("json_fallbacks"):
        changes.append(
            {
                "type": "modify_output_schema",
                "target": "json_agents",
                "reason": "One or more JSON agents returned invalid JSON and required fallback.",
                "proposal": "Tighten JSON-only prompts and add stricter repair or retry before fallback.",
            }
        )
    if trace_health.get("looping_detected"):
        changes.append(
            {
                "type": "modify_routing_policy",
                "target": "routing_policy.yaml",
                "reason": "Trace health detected repeated outputs, duplicate agent steps, or handoff loops.",
                "proposal": "Gate repeated agent calls and require each handoff to name a new signal it adds.",
            }
        )
    if chatgpt_comparison.get("winner") == "chatgpt":
        changes.append(
            {
                "type": "modify_agent_prompt",
                "target": "final_synthesizer",
                "reason": "ChatGPT baseline scored higher than our final answer.",
                "proposal": "Improve synthesis prompt with sharper answer structure and explicit constraints.",
            }
        )
    if not changes:
        changes.append(
            {
                "type": "keep",
                "target": "current_flow",
                "reason": "No material routing or answer-quality issue was detected.",
                "proposal": "Keep collecting runs.",
            }
        )
    return {
        "decision": "proposal_only",
        "should_change_flow": any(change["type"] != "keep" for change in changes),
        "changes": changes,
        "do_not_change": ["core runtime", "tools", "skills"] if not lesson_report.get("apply_updates") else [],
        "skills_tools_proposal": [],
        "apply_updates": False,
        "requires_human_approval": True,
        "reason": "v0.3 can propose flow, agent, prompt, skill, or tool changes, but never applies them automatically.",
    }


def sanitize_critical_audit(
    audit: dict[str, Any],
    workflow_decision: dict[str, Any],
    agent_calls: list[dict[str, Any]],
    flow_observation: dict[str, Any],
    chatgpt_comparison: dict[str, Any],
    trace_health: dict[str, Any],
) -> dict[str, Any]:
    sanitized = dict(audit)
    notes: list[str] = []
    selected_workflow = str(workflow_decision.get("selected_workflow") or "unknown")
    if sanitized.get("selected_workflow") != selected_workflow:
        sanitized["selected_workflow"] = selected_workflow
        notes.append("Corrected selected_workflow to match workflow_decision.")

    try:
        logic_score = int(sanitized.get("logic_score", 0))
    except (TypeError, ValueError):
        logic_score = 0
    if logic_score > 10:
        logic_score = round(logic_score / 10)
        notes.append("Normalized logic_score to 0-10 scale.")
    sanitized["logic_score"] = max(0, min(10, logic_score))

    active_agents = {
        str(call.get("agent"))
        for call in agent_calls
        if call.get("event_type") != "agent_skipped" and call.get("agent")
    }
    skipped_agents = {
        str(call.get("agent"))
        for call in agent_calls
        if call.get("event_type") == "agent_skipped" and call.get("agent")
    }
    wasted = []
    for agent in sanitized.get("wasted_agents") or []:
        agent_name = str(agent)
        if agent_name in skipped_agents:
            notes.append(f"Removed skipped agent {agent_name!r} from wasted_agents.")
            continue
        if agent_name not in active_agents and agent_name not in flow_observation.get("unnecessary_agents", []):
            notes.append(f"Removed unobserved agent {agent_name!r} from wasted_agents.")
            continue
        wasted.append(agent_name)
    sanitized["wasted_agents"] = sorted(set(wasted))

    backed_missing = set(str(item) for item in flow_observation.get("missing_agents") or [])
    missing = []
    for agent in sanitized.get("missing_agents") or []:
        agent_name = str(agent)
        if backed_missing and agent_name not in backed_missing:
            notes.append(f"Removed unbacked missing agent {agent_name!r}.")
            continue
        if not backed_missing and trace_health.get("status") == "clean" and chatgpt_comparison.get("winner") in {"ours", "tie"}:
            notes.append(f"Removed unbacked missing agent {agent_name!r} because trace is clean and answer did not lose to ChatGPT.")
            continue
        missing.append(agent_name)
    sanitized["missing_agents"] = sorted(set(missing))

    if (
        trace_health.get("status") == "clean"
        and flow_observation.get("workflow_verdict") in {"GOOD", "PARTIAL", None}
        and chatgpt_comparison.get("winner") in {"ours", "tie"}
        and not sanitized["wasted_agents"]
        and not sanitized["missing_agents"]
        and not sanitized.get("bad_handoffs")
        and not sanitized.get("role_violations")
    ):
        if sanitized.get("recommendation") != "keep_flow":
            sanitized["recommendation"] = "keep_flow"
            notes.append("Set recommendation to keep_flow because trace is clean and ChatGPT did not win.")

    if notes:
        sanitized["sanitizer_notes"] = notes
    return sanitized


def sanitize_flow_observation(
    observation: dict[str, Any],
    workflow_decision: dict[str, Any],
    lens_trace: list[dict[str, Any]],
) -> dict[str, Any]:
    sanitized = dict(observation)
    notes: list[str] = []
    selected_workflow = str(workflow_decision.get("selected_workflow") or sanitized.get("selected_workflow") or "direct")
    if sanitized.get("selected_workflow") != selected_workflow:
        sanitized["selected_workflow"] = selected_workflow
        notes.append("Corrected selected_workflow to match workflow_decision.")

    for key in ["flow_quality_score", "workflow_score"]:
        try:
            score = int(sanitized.get(key, 0))
        except (TypeError, ValueError):
            continue
        if score > 10:
            sanitized[key] = max(0, min(10, round(score / 10)))
            notes.append(f"Normalized {key} to 0-10 scale.")

    if selected_workflow != "deep":
        def _not_lens_issue(item: Any) -> bool:
            if not isinstance(item, dict):
                return True
            text = f"{item.get('step', '')} {item.get('reason', '')}".lower()
            return "lens" not in text

        old_wasted = list(sanitized.get("wasted_steps") or [])
        old_missing = list(sanitized.get("missing_steps") or [])
        sanitized["wasted_steps"] = [item for item in old_wasted if _not_lens_issue(item)]
        sanitized["missing_steps"] = [item for item in old_missing if _not_lens_issue(item)]
        sanitized["missing_agents"] = [
            agent for agent in sanitized.get("missing_agents") or [] if "lens" not in str(agent).lower()
        ]
        if len(sanitized["wasted_steps"]) != len(old_wasted) or len(sanitized["missing_steps"]) != len(old_missing):
            notes.append("Removed lens-missing/lens-wasted findings because selected workflow is not deep.")
        sanitized["was_lens_flow_justified"] = bool(lens_trace)

    if not sanitized.get("wasted_steps") and not sanitized.get("missing_steps") and sanitized.get("workflow_verdict") not in {"GOOD", "PARTIAL"}:
        sanitized["workflow_verdict"] = "GOOD"
        sanitized["routing_verdict"] = "good"
        notes.append("Set workflow_verdict to GOOD because no missing or wasted steps remain.")

    if notes:
        sanitized["sanitizer_notes"] = list(sanitized.get("sanitizer_notes") or []) + notes
    return sanitized


def blind_shuffle(answers: list[AnswerItem], seed: int) -> dict[str, Any]:
    labels = [f"answer_{chr(ord('a') + index)}" for index in range(len(answers))]
    items = list(answers)
    rng = random.Random(seed)
    rng.shuffle(items)
    visible_answers: dict[str, str] = {}
    hidden_mapping: dict[str, str] = {}
    visible_titles: dict[str, str] = {}
    for label, item in zip(labels, items):
        visible_answers[label] = item.answer
        hidden_mapping[label] = item.source
        visible_titles[label] = item.title
    return {
        "visible_answers": visible_answers,
        "hidden_mapping": hidden_mapping,
        "visible_titles": visible_titles,
    }


def stable_seed(run_id: str, question: str) -> int:
    digest = hashlib.sha256(f"{run_id}\n{question}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def build_run_id() -> str:
    return "run_" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def read_question(args: argparse.Namespace) -> str:
    parts = []
    if args.question_file:
        parts.append(read_text(args.question_file).strip())
    if args.question:
        parts.append(" ".join(args.question).strip())
    question = "\n\n".join(part for part in parts if part)
    if not question:
        raise SystemExit("Provide a question or --question-file.")
    return question


def list_assets() -> None:
    print("Self Eval QA Lab assets")
    print("\nRouting:")
    if ROUTING_POLICY_PATH.exists():
        print(f"- routing_policy: {ROUTING_POLICY_PATH.relative_to(ROOT_DIR)}")
    print("\nPrompts:")
    for path in sorted(PROMPT_DIR.glob("*.md")):
        print(f"- {path.stem}: {path.relative_to(ROOT_DIR)}")
    print("\nLenses:")
    for path in sorted(LENS_DIR.glob("*_lens.md")):
        print(f"- {path.stem.replace('_lens', '')}: {path.relative_to(ROOT_DIR)}")
    print("\nRubrics:")
    for path in sorted(RUBRIC_DIR.glob("*.yaml")):
        print(f"- {path.stem}: {path.relative_to(ROOT_DIR)}")
    print("\nQuestions:")
    for path in sorted(QUESTION_DIR.glob("*")):
        if path.is_file():
            print(f"- {path.stem}: {path.relative_to(ROOT_DIR)}")


def dry_run(
    question: str,
    config: LabConfig,
    baseline_mode: str,
    force_lenses: bool,
    forced_workflow: str | None,
    chatgpt_mode: str,
    llm_options: LLMOptions,
) -> None:
    classification = classify_question_deterministic(question, config.default_lenses)
    if force_lenses and forced_workflow is None:
        forced_workflow = "deep"
    workflow_decision = route_workflow_deterministic(question, classification, load_routing_policy(), forced_workflow=forced_workflow)
    selected_lenses = classification["suggested_lenses"] if workflow_decision["selected_workflow"] == "deep" else []
    print("Self Eval QA Lab dry run")
    print(f"- lab: {config.name} v{config.version}")
    print(f"- llm_provider: {llm_options.provider}")
    if llm_options.provider == "server":
        print(f"- server_url: {llm_options.server_url or '(not set)'}")
        print(f"- server_model: {llm_options.model or '(llm.py default if server accepts it)'}")
    print(f"- baseline_mode: {baseline_mode}")
    print(f"- chatgpt_mode: {chatgpt_mode}")
    print(f"- workflow: {workflow_decision['selected_workflow']}")
    print(f"- selected_lenses: {', '.join(selected_lenses) if selected_lenses else '(none)'}")
    print("\nFlow")
    print("1. Question Classifier")
    print("2. Workflow Router")
    print("3. Direct / Assisted / Deep / Repo Debug Answer Path")
    print("4. Auto Baseline when route requests it")
    print("5. ChatGPT Baseline Prompt/Answer")
    print("6. Blind Evaluator")
    print("7. Error Analyzer")
    print("8. Flow Observer")
    print("9. Lesson Extractor")
    print("10. Critical Auditor")
    print("11. Evolution Decider")
    print("12. Ledger + Admin Full Trace")
    print("\nDeterministic classification")
    print(pretty_json(classification))
    print("\nWorkflow decision")
    print(pretty_json(workflow_decision))


class SelfEvalLab:
    def __init__(
        self,
        question: str,
        config: LabConfig,
        baseline_mode: str,
        force_lenses: bool,
        forced_workflow: str | None,
        llm_options: LLMOptions,
        temperature: float,
        mock: bool,
        propose_updates: bool,
        chatgpt_mode: str,
        chatgpt_answer_file: Path | None,
        out_dir: Path,
    ) -> None:
        self.question = question
        self.config = config
        self.baseline_mode = baseline_mode
        self.force_lenses = force_lenses
        self.forced_workflow = forced_workflow
        self.llm_options = llm_options
        self.temperature = temperature
        self.mock = mock
        self.propose_updates = propose_updates
        self.chatgpt_mode = chatgpt_mode
        self.chatgpt_answer_file = chatgpt_answer_file
        self.out_dir = out_dir
        self.warnings: list[str] = []
        self.answer_rubric = load_yaml(RUBRIC_DIR / "answer_quality_rubric.yaml")
        self.routing_policy = load_routing_policy()
        self.recorder: RunRecorder | None = None

    def run(self) -> LabResult:
        run_id = build_run_id()
        run_dir = self.out_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        self.recorder = RunRecorder(run_id, run_dir)
        self.recorder.write_artifact("prompts", "user_prompt.md", self.question + "\n")
        run_plan = self.plan_run()
        classification = self.classify()
        workflow_decision = self.route_workflow(classification)
        simple_answer = self.simple_answer()
        our_answer, lens_trace, workflow_trace = self.workflow_answer(classification, workflow_decision, simple_answer)
        effective_baseline_mode = self.effective_baseline_mode(workflow_decision)
        baseline_answer = self.baseline_answer(effective_baseline_mode)
        chatgpt_answer = self.chatgpt_baseline()
        answers = [
            AnswerItem("simple", "Simple single-agent answer", simple_answer),
            AnswerItem("ours", f"{workflow_decision.get('selected_workflow', 'workflow')} answer", our_answer),
        ]
        if baseline_answer is not None:
            answers.append(AnswerItem("baseline", "External/local baseline answer", baseline_answer))
        if chatgpt_answer is not None:
            answers.append(AnswerItem("chatgpt", "ChatGPT baseline answer", chatgpt_answer))
        blind_pack = blind_shuffle(answers, seed=stable_seed(run_id, self.question))
        evaluation = self.evaluate(blind_pack["visible_answers"])
        revealed = reveal_evaluation(evaluation, blind_pack["hidden_mapping"])
        chatgpt_comparison = deterministic_chatgpt_comparison(revealed, chatgpt_answer)
        error_report = self.error_analysis(classification, simple_answer, our_answer, baseline_answer, chatgpt_answer, revealed)
        flow_observation = self.observe_flow(classification, workflow_decision, workflow_trace, lens_trace, revealed, error_report, effective_baseline_mode)
        lesson_report = self.extract_lessons(workflow_decision, flow_observation, error_report)
        pre_audit_trace_health = analyze_trace_health(
            self.recorder.agent_calls if self.recorder else [],
            self.recorder.handoffs if self.recorder else [],
        )
        critical_audit = self.critical_audit(workflow_decision, workflow_trace, flow_observation, chatgpt_comparison, pre_audit_trace_health)
        evolution_decision = self.evolution_decision(critical_audit, flow_observation, lesson_report, chatgpt_comparison)
        trace_health = analyze_trace_health(
            self.recorder.agent_calls if self.recorder else [],
            self.recorder.handoffs if self.recorder else [],
        )
        update_proposal = self.update_proposal(error_report, flow_observation)
        trace_events = list(self.recorder.events if self.recorder else [])
        agent_calls = list(self.recorder.agent_calls if self.recorder else [])
        result = LabResult(
            run_id=run_id,
            run_dir=run_dir,
            question=self.question,
            run_plan=run_plan,
            classification=classification,
            workflow_decision=workflow_decision,
            workflow_trace=workflow_trace,
            simple_answer=simple_answer,
            our_answer=our_answer,
            chatgpt_answer=chatgpt_answer,
            chatgpt_comparison=chatgpt_comparison,
            baseline_answer=baseline_answer,
            lens_trace=lens_trace,
            blind_pack=blind_pack,
            evaluation=evaluation,
            revealed_evaluation=revealed,
            error_report=error_report,
            flow_observation=flow_observation,
            lesson_report=lesson_report,
            critical_audit=critical_audit,
            evolution_decision=evolution_decision,
            trace_health=trace_health,
            trace_events=trace_events,
            agent_calls=agent_calls,
            update_proposal=update_proposal,
            warnings=self.warnings,
        )
        self.write_outputs(result)
        return result

    def record_agent_event(
        self,
        event_type: str,
        agent: str,
        step: str,
        *,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        output: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        public_rationale: str | None = None,
        handoff_to: str | None = None,
        handoff_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self.recorder is None:
            return
        self.recorder.record_event(
            event_type,
            agent,
            step,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output=output,
            model=model,
            provider=provider,
            public_rationale=public_rationale,
            handoff_to=handoff_to,
            handoff_reason=handoff_reason,
            metadata=metadata,
        )

    def repair_benchmark_answer_contract(
        self,
        agent: str,
        step: str,
        system_prompt: str,
        user_prompt: str,
        output: str,
        *,
        model: str | None,
        provider: str | None,
        text_options: LLMOptions,
        public_rationale: str | None,
        handoff_to: str | None,
        handoff_reason: str | None,
        metadata: dict[str, Any] | None,
    ) -> str | None:
        if not is_benchmark_multiple_choice(user_prompt) or has_benchmark_final_answer(output):
            return None
        self.record_agent_event(
            "agent_call",
            agent,
            step,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output=output,
            model=model,
            provider=provider,
            public_rationale=public_rationale,
            handoff_to=None,
            handoff_reason=None,
            metadata={**(metadata or {}), "benchmark_contract_repair_needed": True, "superseded_by_repair": True},
        )
        repair_system_prompt = (
            "Repair the previous answer so it satisfies the benchmark multiple-choice contract. "
            "Use the original passage, question, and options. Choose exactly one valid option letter. "
            "Return a concise visible rationale, and make the last non-empty line exactly: Answer: <letter>. "
            "Do not add prose after the final answer line."
        )
        repair_user_prompt = "\n\n".join(
            [
                "Original system instructions:",
                system_prompt,
                "Original user prompt:",
                user_prompt,
                "Previous answer that missed the final-answer contract:",
                output if output.strip() else "(empty)",
                "Return only the repaired benchmark answer.",
            ]
        )
        repair_model, repair_output = call_model(
            repair_system_prompt,
            repair_user_prompt,
            llm_options=text_options,
            temperature=0.0,
        )
        self.record_agent_event(
            "agent_call",
            agent,
            f"{step}_benchmark_contract_repair",
            system_prompt=repair_system_prompt,
            user_prompt=repair_user_prompt,
            output=repair_output,
            model=repair_model,
            provider=provider,
            public_rationale=f"Repair benchmark final-answer contract from {agent}.{step}.",
            handoff_to=handoff_to if repair_output.strip() else None,
            handoff_reason=handoff_reason if repair_output.strip() else None,
            metadata={**(metadata or {}), "benchmark_contract_repair": True},
        )
        if repair_output.strip():
            return repair_output.strip()
        self.warnings.append(f"{agent}: benchmark final-answer contract repair returned empty output.")
        return output.strip()

    def call_text_agent(
        self,
        agent: str,
        step: str,
        system_prompt: str,
        user_prompt: str,
        fallback: str,
        *,
        temperature: float | None = None,
        public_rationale: str | None = None,
        handoff_to: str | None = None,
        handoff_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
        llm_options: LLMOptions | None = None,
        enforce_benchmark_answer: bool = False,
    ) -> str:
        options = llm_options or self.llm_options
        if self.mock:
            model = "mock"
            output = fallback
            provider = "mock"
        else:
            text_options = LLMOptions(
                provider=options.provider,
                model=options.model,
                server_url=options.server_url,
                server_api_key=options.server_api_key,
                timeout=options.timeout,
                max_tokens=max(int(options.max_tokens or 0), 1024),
            )
            model, output = call_model(
                system_prompt,
                user_prompt,
                llm_options=text_options,
                temperature=self.temperature if temperature is None else temperature,
            )
            provider = text_options.provider
            if not output.strip():
                self.record_agent_event(
                    "agent_call",
                    agent,
                    step,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    output=output,
                    model=model,
                    provider=provider,
                    public_rationale=public_rationale,
                    handoff_to=None,
                    handoff_reason=None,
                    metadata={**(metadata or {}), "empty_output": True, "superseded_by_repair": True},
                )
                repair_system_prompt = (
                    "The previous model call returned an empty answer. Answer the user directly now. "
                    "Do not write code unless explicitly requested. Keep the answer concise. "
                    "If the user asks for a multiple-choice answer, include a final line exactly like: Answer: <letter>."
                )
                repair_user_prompt = "\n\n".join(
                    [
                        "Original system instructions:",
                        system_prompt,
                        "Original user prompt:",
                        user_prompt,
                        "Return only the repaired answer.",
                    ]
                )
                repair_model, repair_output = call_model(
                    repair_system_prompt,
                    repair_user_prompt,
                    llm_options=text_options,
                    temperature=0.0,
                )
                if repair_output.strip():
                    self.record_agent_event(
                        "agent_call",
                        agent,
                        f"{step}_empty_repair",
                        system_prompt=repair_system_prompt,
                        user_prompt=repair_user_prompt,
                        output=repair_output,
                        model=repair_model,
                        provider=provider,
                        public_rationale=f"Repair empty output from {agent}.{step}.",
                        handoff_to=handoff_to,
                        handoff_reason=handoff_reason,
                        metadata={**(metadata or {}), "empty_output_repair": True},
                    )
                    if enforce_benchmark_answer:
                        contract_repair = self.repair_benchmark_answer_contract(
                            agent,
                            f"{step}_empty_repair",
                            repair_system_prompt,
                            repair_user_prompt,
                            repair_output,
                            model=repair_model,
                            provider=provider,
                            text_options=text_options,
                            public_rationale=f"Repair empty output from {agent}.{step}.",
                            handoff_to=handoff_to,
                            handoff_reason=handoff_reason,
                            metadata={**(metadata or {}), "empty_output_repair": True},
                        )
                        if contract_repair is not None:
                            return contract_repair
                    return repair_output.strip()
                self.warnings.append(f"{agent}: empty output; used deterministic fallback after failed repair.")
                self.record_agent_event(
                    "agent_output",
                    agent,
                    f"{step}_empty_fallback",
                    system_prompt="Use deterministic fallback after empty model output and empty repair.",
                    user_prompt=user_prompt,
                    output=fallback,
                    model="deterministic",
                    provider="local",
                    public_rationale=f"Fallback prevents {agent}.{step} from returning an empty answer.",
                    handoff_to=handoff_to,
                    handoff_reason=handoff_reason,
                    metadata={**(metadata or {}), "empty_output_fallback": True},
                )
                return fallback.strip()
        if not self.mock and text_contains_code_block(output) and not prompt_allows_code(system_prompt, user_prompt):
            self.record_agent_event(
                "agent_call",
                agent,
                step,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output=output,
                model=model,
                provider=provider,
                public_rationale=public_rationale,
                handoff_to=None,
                handoff_reason=None,
                metadata={**(metadata or {}), "text_repair_needed": True, "superseded_by_repair": True},
            )
            repair_system_prompt = (
                "Rewrite the previous answer without code fences, JSON blocks, schema examples, shell commands, or source code. "
                "Preserve the useful content, answer in the same language, and keep it concise."
            )
            repair_user_prompt = "\n\n".join(
                [
                    "Original user prompt:",
                    user_prompt,
                    "Previous answer that violated no-code constraints:",
                    output,
                    "Return only the repaired answer.",
                ]
            )
            repair_model, repair_output = call_model(
                repair_system_prompt,
                repair_user_prompt,
                llm_options=text_options,
                temperature=0.0,
            )
            self.record_agent_event(
                "agent_call",
                agent,
                f"{step}_repair",
                system_prompt=repair_system_prompt,
                user_prompt=repair_user_prompt,
                output=repair_output,
                model=repair_model,
                provider=provider,
                public_rationale=f"Repair no-code constraint violation from {agent}.{step}.",
                handoff_to=handoff_to,
                handoff_reason=handoff_reason,
                metadata={**(metadata or {}), "text_repair_attempt": True},
            )
            if enforce_benchmark_answer:
                contract_repair = self.repair_benchmark_answer_contract(
                    agent,
                    f"{step}_repair",
                    repair_system_prompt,
                    repair_user_prompt,
                    repair_output,
                    model=repair_model,
                    provider=provider,
                    text_options=text_options,
                    public_rationale=f"Repair no-code constraint violation from {agent}.{step}.",
                    handoff_to=handoff_to,
                    handoff_reason=handoff_reason,
                    metadata={**(metadata or {}), "text_repair_attempt": True},
                )
                if contract_repair is not None:
                    return contract_repair
            return repair_output.strip()
        if not self.mock and enforce_benchmark_answer:
            contract_repair = self.repair_benchmark_answer_contract(
                agent,
                step,
                system_prompt,
                user_prompt,
                output,
                model=model,
                provider=provider,
                text_options=text_options,
                public_rationale=public_rationale,
                handoff_to=handoff_to,
                handoff_reason=handoff_reason,
                metadata=metadata,
            )
            if contract_repair is not None:
                return contract_repair
        self.record_agent_event(
            "agent_call",
            agent,
            step,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output=output,
            model=model,
            provider=provider,
            public_rationale=public_rationale,
            handoff_to=handoff_to,
            handoff_reason=handoff_reason,
            metadata=metadata,
        )
        return output.strip()

    def call_json_agent(
        self,
        agent: str,
        step: str,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any],
        *,
        temperature: float = 0.0,
        public_rationale: str | None = None,
        handoff_to: str | None = None,
        handoff_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = dict(metadata or {})
        if self.mock:
            model = "mock"
            raw = pretty_json(fallback)
            provider = "mock"
            parsed: dict[str, Any] | None = dict(fallback)
            parse_status = "mock_fallback"
            used_fallback = False
            metadata["json_parse_status"] = parse_status
            metadata["used_fallback"] = used_fallback
            self.record_agent_event(
                "agent_call",
                agent,
                step,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output=raw,
                model=model,
                provider=provider,
                public_rationale=public_rationale,
                handoff_to=handoff_to,
                handoff_reason=handoff_reason,
                metadata=metadata,
            )
            return parsed
        else:
            json_options = LLMOptions(
                provider=self.llm_options.provider,
                model=self.llm_options.model,
                server_url=self.llm_options.server_url,
                server_api_key=self.llm_options.server_api_key,
                timeout=self.llm_options.timeout,
                max_tokens=max(int(self.llm_options.max_tokens or 0), 1536),
            )
            model, raw = call_model(system_prompt, user_prompt, llm_options=json_options, temperature=temperature)
            provider = self.llm_options.provider
            parsed, parse_status = parse_json_object(raw)
        if parsed is not None:
            schema_ok, schema_note = validate_json_agent_output(agent, parsed)
        else:
            schema_ok, schema_note = False, parse_status
        if parsed is not None and schema_ok:
            metadata["json_parse_status"] = parse_status
            metadata["json_schema_status"] = schema_note
            metadata["used_fallback"] = False
            self.record_agent_event(
                "agent_call",
                agent,
                step,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output=raw,
                model=model,
                provider=provider,
                public_rationale=public_rationale,
                handoff_to=handoff_to,
                handoff_reason=handoff_reason,
                metadata=metadata,
            )
            return parsed

        failed_metadata = dict(metadata)
        failed_metadata["json_parse_status"] = parse_status if parsed is None else schema_note
        failed_metadata["json_schema_status"] = schema_note
        failed_metadata["repair_needed"] = True
        failed_metadata["used_fallback"] = False
        failed_metadata["superseded_by_repair"] = True
        self.record_agent_event(
            "agent_call",
            agent,
            step,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output=raw,
            model=model,
            provider=provider,
            public_rationale=public_rationale,
            handoff_to=None,
            handoff_reason=None,
            metadata=failed_metadata,
        )

        repair_system_prompt = (
            "You repair malformed model output into exactly one strict raw JSON object. "
            "No markdown fences, no prose, no comments. If the previous output is empty or incomplete, "
            "return a valid object with the same top-level keys as the expected object."
        )
        repair_user_prompt = "\n\n".join(
            [
                f"Agent: {agent}",
                f"Step: {step}",
                f"Failure: {failed_metadata['json_parse_status']}",
                "Expected JSON object shape and safe fallback values:",
                pretty_json(fallback),
                "Previous malformed output:",
                raw if raw.strip() else "(empty)",
                "Return only one corrected JSON object with the expected top-level keys.",
            ]
        )
        repair_options = LLMOptions(
            provider=self.llm_options.provider,
            model=self.llm_options.model,
            server_url=self.llm_options.server_url,
            server_api_key=self.llm_options.server_api_key,
            timeout=self.llm_options.timeout,
            max_tokens=max(int(self.llm_options.max_tokens or 0), 1536),
        )
        repair_model, repair_raw = call_model(
            repair_system_prompt,
            repair_user_prompt,
            llm_options=repair_options,
            temperature=0.0,
        )
        repair_parsed, repair_status = parse_json_object(repair_raw)
        if repair_parsed is not None:
            repair_schema_ok, repair_schema_note = validate_json_agent_output(agent, repair_parsed)
        else:
            repair_schema_ok, repair_schema_note = False, repair_status
        repair_metadata = dict(metadata)
        repair_metadata["json_parse_status"] = repair_status if repair_parsed is None else repair_schema_note
        repair_metadata["json_schema_status"] = repair_schema_note
        repair_metadata["repair_attempt"] = True
        repair_metadata["repair_failed"] = repair_parsed is None or not repair_schema_ok
        repair_metadata["used_fallback"] = False
        self.record_agent_event(
            "agent_call",
            agent,
            f"{step}_repair",
            system_prompt=repair_system_prompt,
            user_prompt=repair_user_prompt,
            output=repair_raw,
            model=repair_model,
            provider=provider,
            public_rationale=f"Repair invalid JSON from {agent}.{step}.",
            handoff_to=handoff_to if repair_parsed is not None and repair_schema_ok else None,
            handoff_reason=handoff_reason if repair_parsed is not None and repair_schema_ok else None,
            metadata=repair_metadata,
        )
        if repair_parsed is None or not repair_schema_ok:
            self.warnings.append(
                f"{agent}: JSON parse/schema failed ({failed_metadata['json_parse_status']}); "
                f"repair failed ({repair_metadata['json_parse_status']}); used deterministic fallback."
            )
            self.record_agent_event(
                "agent_output",
                agent,
                f"{step}_fallback",
                system_prompt="Use deterministic JSON fallback after model output and repair both failed.",
                user_prompt=pretty_json(
                    {
                        "agent": agent,
                        "step": step,
                        "initial_failure": failed_metadata["json_parse_status"],
                        "repair_failure": repair_metadata["json_parse_status"],
                    }
                ),
                output=pretty_json(fallback),
                model="deterministic",
                provider="local",
                public_rationale=f"Fallback keeps {agent}.{step} auditable after malformed JSON and failed repair.",
                handoff_to=handoff_to,
                handoff_reason=handoff_reason,
                metadata={
                    **(metadata or {}),
                    "used_fallback": True,
                    "fallback_after_repair": True,
                    "json_parse_status": repair_metadata["json_parse_status"],
                    "json_schema_status": "deterministic fallback",
                },
            )
            return dict(fallback)
        self.warnings.append(f"{agent}: JSON parse/schema failed ({failed_metadata['json_parse_status']}); repair succeeded ({repair_metadata['json_parse_status']}).")
        return repair_parsed

    def plan_run(self) -> dict[str, Any]:
        plan = {
            "version": "0.3",
            "goal": "Answer the user question, compare against ChatGPT, audit the process, and propose only safe future changes.",
            "steps": [
                "question_classifier",
                "workflow_router",
                "selected_answer_path",
                "chatgpt_baseline",
                "blind_evaluator",
                "error_analyzer",
                "flow_observer",
                "lesson_extractor",
                "critical_auditor",
                "evolution_decider",
            ],
            "trace_policy": "Store full prompts, inputs, raw outputs, public rationales, handoffs, and admin trace without truncation.",
        }
        self.record_agent_event(
            "agent_output",
            "run_planner",
            "plan",
            system_prompt="Create a no-code auditable answer-flow run plan.",
            user_prompt=self.question,
            output=pretty_json(plan),
            model="deterministic",
            provider="local",
            public_rationale="The run needs answer generation, ChatGPT comparison, self-audit, and proposal-only evolution.",
            handoff_to="question_classifier",
            handoff_reason="The classifier needs the question before routing.",
        )
        return plan

    def classify(self) -> dict[str, Any]:
        fallback = classify_question_deterministic(self.question, self.config.default_lenses)
        if is_benchmark_multiple_choice(self.question):
            self.record_agent_event(
                "agent_output",
                "question_classifier",
                "classify",
                system_prompt="Use deterministic benchmark classification for multiple-choice dataset tasks.",
                user_prompt=self.question,
                output=pretty_json(fallback),
                model="deterministic",
                provider="local",
                public_rationale="Benchmark MCQ tasks need stable routing; model classifier drift caused deep/repo_debug misroutes in batch evidence.",
                handoff_to="workflow_router",
                handoff_reason="Router needs task type, complexity, and suggested lenses.",
            )
            return fallback
        system_prompt = render_template(
            load_prompt("question_classifier"),
            {"AVAILABLE_LENSES": ", ".join(self.config.default_lenses)},
        )
        return self.call_json_agent(
            "question_classifier",
            "classify",
            system_prompt,
            self.question,
            fallback=fallback,
            temperature=0.0,
            public_rationale="Classify task type and complexity before routing.",
            handoff_to="workflow_router",
            handoff_reason="Router needs task type, complexity, and suggested lenses.",
        )

    def route_workflow(self, classification: dict[str, Any]) -> dict[str, Any]:
        forced_workflow = self.forced_workflow
        if self.force_lenses and forced_workflow is None:
            forced_workflow = "deep"
        decision = route_workflow_deterministic(
            self.question,
            classification,
            policy=self.routing_policy,
            forced_workflow=forced_workflow,
        )
        self.record_agent_event(
            "agent_output",
            "workflow_router",
            "route",
            system_prompt="Route to direct, assisted, deep, or repo_debug using routing_policy.yaml.",
            user_prompt=pretty_json({"question": self.question, "classification": classification}),
            output=pretty_json(decision),
            model="deterministic",
            provider="local",
            public_rationale=str(decision.get("reason") or "Selected workflow from deterministic policy."),
            handoff_to=f"{decision.get('selected_workflow')}_answer_path",
            handoff_reason="The selected workflow determines which agents run next.",
        )
        return decision

    def simple_answer(self) -> str:
        system_prompt = "\n\n".join(part for part in [load_prompt("simple_answer"), benchmark_answer_contract(self.question)] if part)
        return self.call_text_agent(
            "simple_answer",
            "draft",
            system_prompt,
            self.question,
            fallback=heuristic_answer(self.question, "Simple answer"),
            temperature=self.temperature,
            public_rationale="Always create a simple answer baseline before using extra agents.",
            handoff_to="workflow_router",
            handoff_reason="The selected workflow may use this draft directly or refine it.",
            enforce_benchmark_answer=True,
        )

    def workflow_answer(
        self,
        classification: dict[str, Any],
        workflow_decision: dict[str, Any],
        simple_answer: str,
    ) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
        selected_workflow = str(workflow_decision.get("selected_workflow") or "direct")
        trace = [
            trace_step(
                "route",
                "workflow_router",
                f"Selected {selected_workflow}: {workflow_decision.get('reason', '')}",
                metadata={"max_steps": workflow_decision.get("max_steps")},
            )
        ]
        if selected_workflow == "direct":
            trace.append(trace_step("answer", "direct_answer", "Returned the simple answer without extra agents."))
            self.record_agent_event(
                "agent_output",
                "direct_answer",
                "finalize",
                system_prompt="Use the simple answer as the final answer for direct workflow.",
                user_prompt=simple_answer,
                output=simple_answer,
                model="deterministic",
                provider="local",
                public_rationale="Direct workflow avoids extra agents for simple questions.",
                handoff_to="chatgpt_baseline",
                handoff_reason="The final answer must be compared with ChatGPT.",
                metadata={"pass_through": True},
            )
            return simple_answer, [], trace
        if selected_workflow == "assisted":
            answer, assisted_trace = self.assisted_answer(simple_answer)
            trace.extend(assisted_trace)
            return answer, [], trace
        if selected_workflow == "repo_debug":
            answer, repo_trace = self.repo_debug_answer(simple_answer)
            trace.extend(repo_trace)
            return answer, [], trace

        selected_lenses = [str(item) for item in classification.get("suggested_lenses") or []]
        answer, lens_trace = self.lens_answer(selected_lenses)
        trace.append(
            trace_step(
                "answer",
                "lens_answer",
                "Generated an answer through selected lenses.",
                metadata={"lenses": selected_lenses, "lens_count": len(lens_trace)},
            )
        )
        return answer, lens_trace, trace

    def assisted_answer(self, draft_answer: str) -> tuple[str, list[dict[str, Any]]]:
        trace = [
            trace_step("draft", "simple_answer", "Used the simple answer as the draft."),
            trace_step("review", "critic", "Checked the draft for missing risks, assumptions, and next steps."),
            trace_step("rewrite", "answer_synthesizer", "Rewrote the draft into the final assisted answer."),
        ]
        critic_prompt = (
            "You are the Critic Agent. Return public critique only. Do not write code. "
            "Check for overconfident claims, missing caveats, missing validation/fallback advice, and whether the draft answers the exact question."
        )
        contract = benchmark_answer_contract(self.question)
        if contract:
            critic_prompt = f"{critic_prompt} Also check whether the draft satisfies this contract: {contract}"
        critic_input = "\n\n".join(["Question:", self.question, "Draft answer:", draft_answer])
        critique = self.call_text_agent(
            "critic",
            "review",
            critic_prompt,
            critic_input,
            fallback="- Keep the answer compact, but name the trade-off and a concrete next step.\n- Do not spawn specialist agents unless the question needs architecture-level reasoning.",
            temperature=0.0,
            public_rationale="Critic checks whether the draft needs risk, assumption, or actionability improvements.",
            handoff_to="answer_synthesizer",
            handoff_reason="Synthesizer needs the critique to revise the draft.",
        )
        benchmark_missing_final = is_benchmark_multiple_choice(self.question) and not has_benchmark_final_answer(draft_answer)
        if benchmark_missing_final:
            critique = "\n".join(
                [
                    critique,
                    "- Material rewrite required: the draft does not satisfy the benchmark final-answer line contract.",
                ]
            ).strip()
        if not critique_requests_material_rewrite(critique) and not benchmark_missing_final:
            self.record_agent_event(
                "agent_skipped",
                "answer_synthesizer",
                "rewrite_skip",
                system_prompt="Skip rewrite when the critic does not identify material changes.",
                user_prompt="\n\n".join(["Question:", self.question, "Draft answer:", draft_answer, "Critique:", critique]),
                output="Skipped rewrite: critic did not identify a material change. Final answer reuses the draft.",
                model="deterministic",
                provider="local",
                public_rationale="Avoid a redundant rewrite that would repeat the draft and create multi-agent theater.",
                handoff_to="chatgpt_baseline",
                handoff_reason="The final answer must be compared with ChatGPT.",
            )
            return draft_answer, trace
        system_prompt = (
            "You are the Answer Synthesizer. Rewrite the draft using the critique. Do not write code. "
            "Do not use markdown code fences, JSON blocks, or schema examples unless the user explicitly asks for an example. "
            "Keep important caveats; prefer accurate uncertainty over confident overclaiming."
        )
        if contract:
            system_prompt = f"{system_prompt} {contract}"
        user_prompt = "\n\n".join(
            [
                "Question:",
                self.question,
                "Draft answer:",
                draft_answer,
                "Critique:",
                critique,
            ]
        )
        fallback = "\n".join(
            [
                "Assisted answer:",
                "",
                draft_answer,
                "",
                "Critic pass:",
                critique,
                "",
                "Rewrite note: this answer was improved by a lightweight draft-review-rewrite flow.",
            ]
        )
        answer = self.call_text_agent(
            "answer_synthesizer",
            "rewrite",
            system_prompt,
            user_prompt,
            fallback=fallback,
            temperature=self.temperature,
            public_rationale="Synthesizer produces the assisted final answer from draft plus critique.",
            handoff_to="chatgpt_baseline",
            handoff_reason="The final answer must be compared with ChatGPT.",
            enforce_benchmark_answer=True,
        )
        return answer, trace

    def repo_debug_answer(self, draft_answer: str) -> tuple[str, list[dict[str, Any]]]:
        trace = [
            trace_step("scope", "repo_context_router", "Treated the question as local repo/debug reasoning."),
            trace_step("reason", "debug_reasoner", "Preferred local-context reasoning over an external baseline."),
            trace_step("synthesize", "answer_synthesizer", "Produced a no-code diagnostic answer."),
        ]
        self.record_agent_event(
            "agent_output",
            "repo_context_router",
            "scope",
            system_prompt="Decide how repo/debug context should be handled without editing code.",
            user_prompt=self.question,
            output=pretty_json({"scope": "repo_debug", "external_baseline_default": False}),
            model="deterministic",
            provider="local",
            public_rationale="Repo/debug questions should prefer local evidence and avoid external baseline by default.",
            handoff_to="debug_reasoner",
            handoff_reason="Debug reasoner needs the local-context scope.",
        )
        system_prompt = (
            "You are the Debug Reasoner. Explain repo/debug next checks. Do not write or edit code. "
            "Do not use markdown code fences, JSON blocks, or schema examples unless the user explicitly asks for an example."
        )
        contract = benchmark_answer_contract(self.question)
        if contract:
            system_prompt = f"{system_prompt} {contract}"
        user_prompt = "\n\n".join(
            [
                "Question:",
                self.question,
                "Draft answer:",
                draft_answer,
            ]
        )
        fallback = "\n".join(
            [
                "Repo/debug answer:",
                "",
                draft_answer,
                "",
                "Debug routing note:",
                "- Use local traces, failing tests, and nearby files as evidence.",
                "- Avoid external baseline unless the user asks for outside comparison.",
                "- Return explanation and next checks only; this lab does not edit or generate code.",
            ]
        )
        answer = self.call_text_agent(
            "debug_reasoner",
            "reason",
            system_prompt,
            user_prompt,
            fallback=fallback,
            temperature=self.temperature,
            public_rationale="Debug reasoner turns the direct draft into a repo/debug answer without code generation.",
            handoff_to="chatgpt_baseline",
            handoff_reason="The final answer must be compared with ChatGPT.",
            enforce_benchmark_answer=True,
        )
        return answer, trace

    def lens_answer(self, lenses: list[str]) -> tuple[str, list[dict[str, Any]]]:
        selected = [lens for lens in lenses if lens in available_lenses()]
        if not selected:
            selected = self.config.default_lenses[:3]
        lens_trace = [{"lens": lens, "summary": f"Applied {lens} lens to the answer."} for lens in selected]
        system_prompt = render_template(
            load_prompt("answer_generator"),
            {
                "LENS_DOCS": selected_lens_docs(selected),
                "SELECTED_LENSES": ", ".join(selected),
            },
        )
        contract = benchmark_answer_contract(self.question)
        if contract:
            system_prompt = f"{system_prompt}\n\n{contract}"
        output = self.call_text_agent(
            "lens_answer",
            "deep_answer",
            system_prompt,
            self.question,
            fallback=heuristic_answer(self.question, "Lens-based answer", selected),
            temperature=self.temperature,
            public_rationale="Deep workflow uses selected lenses for architecture/risk/practical synthesis.",
            handoff_to="chatgpt_baseline",
            handoff_reason="The final answer must be compared with ChatGPT.",
            metadata={"lenses": selected},
            enforce_benchmark_answer=True,
        )
        return output, lens_trace

    def effective_baseline_mode(self, workflow_decision: dict[str, Any]) -> str:
        if self.baseline_mode == "auto":
            return "local" if workflow_decision.get("needs_baseline") else "auto_skipped"
        return self.baseline_mode

    def baseline_answer(self, effective_baseline_mode: str) -> str | None:
        if effective_baseline_mode in {"none", "auto_skipped"}:
            self.record_agent_event(
                "agent_skipped",
                "external_baseline",
                "skip",
                system_prompt="Run external/local baseline only when selected workflow asks for it.",
                user_prompt=self.question,
                output=f"Skipped baseline because effective mode is {effective_baseline_mode}.",
                model="deterministic",
                provider="local",
                public_rationale="Auto baseline avoids unnecessary comparison cost for smaller workflows.",
            )
            return None
        if effective_baseline_mode == "local":
            system_prompt = load_prompt("baseline_answer")
            return self.call_text_agent(
                "external_baseline",
                "answer",
                system_prompt,
                self.question,
                fallback=heuristic_answer(self.question, "Baseline answer", ["clarity", "practical"]),
                temperature=self.temperature,
                public_rationale="Deep workflow requested a non-ours baseline for comparison.",
                handoff_to="blind_evaluator",
                handoff_reason="Baseline answer participates in blind scoring.",
            )
        self.warnings.append(f"Unsupported baseline mode {effective_baseline_mode!r}; skipped baseline.")
        return None

    def effective_chatgpt_mode(self) -> str:
        if self.chatgpt_mode != "auto":
            return self.chatgpt_mode
        if self.mock:
            return "mock"
        if self.llm_options.provider == "server" and self.llm_options.server_url:
            return "server"
        return "manual"

    def chatgpt_baseline(self) -> str | None:
        mode = self.effective_chatgpt_mode()
        system_prompt = load_prompt("chatgpt_baseline")
        user_prompt = self.question
        if self.recorder is not None:
            self.recorder.write_artifact(
                "prompts",
                "chatgpt_prompt.md",
                "\n\n".join(["# System", system_prompt, "# User", user_prompt]) + "\n",
            )
        if self.chatgpt_answer_file is not None:
            answer = read_text(self.chatgpt_answer_file).strip()
            self.record_agent_event(
                "agent_call",
                "chatgpt_baseline",
                "manual_answer",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output=answer,
                model="manual_chatgpt",
                provider="manual",
                public_rationale="Admin/user supplied a ChatGPT answer file for comparison.",
                handoff_to="blind_evaluator",
                handoff_reason="ChatGPT answer participates in blind scoring.",
            )
            return answer
        if mode == "manual":
            self.record_agent_event(
                "agent_skipped",
                "chatgpt_baseline",
                "manual_pending",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output="PENDING: paste prompts/chatgpt_prompt.md into ChatGPT and rerun with --chatgpt-answer-file.",
                model="manual_chatgpt",
                provider="manual",
                public_rationale="ChatGPT prompt was saved, but no answer file was provided.",
            )
            self.warnings.append("ChatGPT baseline is pending. Use --chatgpt-answer-file or --chatgpt-mode server/local for automatic comparison.")
            return None
        if mode == "mock":
            answer = heuristic_answer(self.question, "ChatGPT baseline answer", ["clarity", "practical"])
            self.record_agent_event(
                "agent_output",
                "chatgpt_baseline",
                "answer",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output=answer,
                model="mock",
                provider="mock",
                public_rationale="Mock ChatGPT baseline keeps deterministic tests comparable.",
                handoff_to="blind_evaluator",
                handoff_reason="ChatGPT answer participates in blind scoring.",
                metadata={"chatgpt_mode": mode, "mock_baseline": True},
            )
            return answer
        if mode == "local":
            return self.call_text_agent(
                "chatgpt_baseline",
                "answer",
                system_prompt,
                user_prompt,
                fallback=heuristic_answer(self.question, "ChatGPT baseline answer", ["clarity", "practical"]),
                temperature=self.temperature,
                public_rationale="Local model is used as a ChatGPT-style baseline because mode=local.",
                handoff_to="blind_evaluator",
                handoff_reason="ChatGPT-style answer participates in blind scoring.",
                metadata={"chatgpt_mode": mode},
            )
        if mode == "server":
            if not self.llm_options.server_url:
                self.warnings.append("ChatGPT server mode selected but no server URL is configured; comparison is pending.")
                return None
            chatgpt_options = LLMOptions(
                provider="server",
                model=self.llm_options.model,
                server_url=self.llm_options.server_url,
                server_api_key=self.llm_options.server_api_key,
                timeout=self.llm_options.timeout,
                max_tokens=self.llm_options.max_tokens,
            )
            return self.call_text_agent(
                "chatgpt_baseline",
                "answer",
                system_prompt,
                user_prompt,
                fallback=heuristic_answer(self.question, "ChatGPT baseline answer", ["clarity", "practical"]),
                temperature=self.temperature,
                public_rationale="Server mode is used as the ChatGPT/OpenAI-compatible baseline.",
                handoff_to="blind_evaluator",
                handoff_reason="ChatGPT answer participates in blind scoring.",
                metadata={"chatgpt_mode": mode},
                llm_options=chatgpt_options,
            )
        self.warnings.append(f"Unsupported ChatGPT mode {mode!r}; comparison is pending.")
        return None

    def evaluate(self, visible_answers: dict[str, str]) -> dict[str, Any]:
        fallback = deterministic_evaluation(self.question, visible_answers, self.answer_rubric)
        system_prompt = render_template(
            load_prompt("blind_evaluator"),
            {
                "RUBRIC": pretty_json(self.answer_rubric),
                "ANSWER_LABELS": ", ".join(visible_answers),
            },
        )
        payload = {
            "question": self.question,
            "answers": visible_answers,
        }
        return self.call_json_agent(
            "blind_evaluator",
            "score_answers",
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            temperature=0.0,
            public_rationale="Blind evaluator scores answers without knowing which source produced each answer.",
            handoff_to="error_analyzer",
            handoff_reason="Error analyzer needs revealed scores after scoring is complete.",
        )

    def error_analysis(
        self,
        classification: dict[str, Any],
        simple_answer: str,
        our_answer: str,
        baseline_answer: str | None,
        chatgpt_answer: str | None,
        revealed_evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        fallback = deterministic_error_report(revealed_evaluation)
        system_prompt = load_prompt("error_analyzer")
        payload = {
            "question": self.question,
            "classification": classification,
            "answers": {
                "simple": simple_answer,
                "ours": our_answer,
                "baseline": baseline_answer,
                "chatgpt": chatgpt_answer,
            },
            "evaluation": revealed_evaluation,
        }
        return self.call_json_agent(
            "error_analyzer",
            "analyze_errors",
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            temperature=0.0,
            public_rationale="Error analyzer compares revealed scores and identifies where our answer won or lost.",
            handoff_to="flow_observer",
            handoff_reason="Flow observer needs answer errors plus workflow trace.",
        )

    def observe_flow(
        self,
        classification: dict[str, Any],
        workflow_decision: dict[str, Any],
        workflow_trace: list[dict[str, Any]],
        lens_trace: list[dict[str, Any]],
        revealed_evaluation: dict[str, Any],
        error_report: dict[str, Any],
        effective_baseline_mode: str,
    ) -> dict[str, Any]:
        fallback = deterministic_flow_observation(
            classification,
            lens_trace,
            revealed_evaluation,
            effective_baseline_mode,
            workflow_decision=workflow_decision,
            workflow_trace=workflow_trace,
        )
        system_prompt = render_template(load_prompt("flow_observer"), {"FLOW_RUBRIC": pretty_json(load_yaml(RUBRIC_DIR / "flow_quality_rubric.yaml"))})
        payload = {
            "question": self.question,
            "classification": classification,
            "workflow_decision": workflow_decision,
            "workflow_trace": workflow_trace,
            "lens_trace": lens_trace,
            "evaluation": revealed_evaluation,
            "error_report": error_report,
            "cost_info": {
                "baseline_mode": effective_baseline_mode,
                "num_lenses_used": len(lens_trace),
                "num_workflow_steps": len(workflow_trace),
            },
        }
        observation = self.call_json_agent(
            "flow_observer",
            "observe_flow",
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            temperature=0.0,
            public_rationale="Flow observer evaluates whether the selected process was worth using.",
            handoff_to="lesson_extractor",
            handoff_reason="Lesson extractor needs flow verdict and error report.",
        )
        sanitized = sanitize_flow_observation(observation, workflow_decision, lens_trace)
        if sanitized != observation:
            self.record_agent_event(
                "agent_output",
                "flow_observation_sanitizer",
                "reconcile",
                system_prompt="Reconcile Flow Observer JSON with selected workflow and actual lens trace.",
                user_prompt=pretty_json({"raw_flow_observation": observation, "workflow_decision": workflow_decision, "lens_trace": lens_trace}),
                output=pretty_json(sanitized),
                model="deterministic",
                provider="local",
                public_rationale="Prevent contradictory process findings from driving evolution decisions.",
                handoff_to="lesson_extractor",
                handoff_reason="Lesson extractor should consume the reconciled flow observation.",
            )
        return sanitized

    def extract_lessons(
        self,
        workflow_decision: dict[str, Any],
        flow_observation: dict[str, Any],
        error_report: dict[str, Any],
    ) -> dict[str, Any]:
        fallback = deterministic_lesson_report(workflow_decision, flow_observation, error_report)
        system_prompt = load_prompt("lesson_extractor")
        payload = {
            "workflow_decision": workflow_decision,
            "flow_observation": flow_observation,
            "error_report": error_report,
        }
        return self.call_json_agent(
            "lesson_extractor",
            "extract_lessons",
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            temperature=0.0,
            public_rationale="Lesson extractor records small proposal-only lessons before any mutation.",
            handoff_to="critical_auditor",
            handoff_reason="Critical auditor needs the recorded lessons plus full trace.",
        )

    def critical_audit(
        self,
        workflow_decision: dict[str, Any],
        workflow_trace: list[dict[str, Any]],
        flow_observation: dict[str, Any],
        chatgpt_comparison: dict[str, Any],
        trace_health: dict[str, Any],
    ) -> dict[str, Any]:
        agent_calls = list(self.recorder.agent_calls if self.recorder else [])
        fallback = deterministic_critical_audit(workflow_decision, workflow_trace, agent_calls, flow_observation, chatgpt_comparison, trace_health)
        system_prompt = load_prompt("critical_auditor")
        payload = {
            "workflow_decision": workflow_decision,
            "workflow_trace": workflow_trace,
            "flow_observation": flow_observation,
            "chatgpt_comparison": chatgpt_comparison,
            "trace_health": trace_health,
            "agent_call_events": self.recorder.events if self.recorder else [],
        }
        audit = self.call_json_agent(
            "critical_auditor",
            "self_audit",
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            temperature=0.0,
            public_rationale="Critical auditor looks for wasted agents, missing agents, role violations, and unhelpful handoffs.",
            handoff_to="evolution_decider",
            handoff_reason="Evolution decider needs audit findings before proposing changes.",
        )
        sanitized = sanitize_critical_audit(audit, workflow_decision, agent_calls, flow_observation, chatgpt_comparison, trace_health)
        if sanitized != audit:
            self.record_agent_event(
                "agent_output",
                "critical_audit_sanitizer",
                "reconcile",
                system_prompt="Reconcile Critical Auditor JSON with observed trace facts.",
                user_prompt=pretty_json({"raw_audit": audit, "trace_health": trace_health, "workflow_decision": workflow_decision}),
                output=pretty_json(sanitized),
                model="deterministic",
                provider="local",
                public_rationale="Prevent hallucinated audit findings from becoming production decisions.",
                handoff_to="evolution_decider",
                handoff_reason="Evolution decider should consume the reconciled audit.",
            )
        return sanitized

    def evolution_decision(
        self,
        critical_audit: dict[str, Any],
        flow_observation: dict[str, Any],
        lesson_report: dict[str, Any],
        chatgpt_comparison: dict[str, Any],
    ) -> dict[str, Any]:
        fallback = deterministic_evolution_decision(critical_audit, flow_observation, lesson_report, chatgpt_comparison)
        system_prompt = load_prompt("evolution_decider")
        payload = {
            "critical_audit": critical_audit,
            "flow_observation": flow_observation,
            "lesson_report": lesson_report,
            "chatgpt_comparison": chatgpt_comparison,
        }
        return self.call_json_agent(
            "evolution_decider",
            "decide_changes",
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            temperature=0.0,
            public_rationale="Evolution decider proposes whether to add, remove, or modify agents, flows, skills, tools, or outputs.",
        )

    def update_proposal(self, error_report: dict[str, Any], flow_observation: dict[str, Any]) -> dict[str, Any] | None:
        if not self.propose_updates:
            return None
        proposal = error_report.get("recommended_update_proposal")
        if not isinstance(proposal, dict) or not proposal.get("enabled"):
            return {
                "enabled": False,
                "reason": "No safe update proposal was produced for this run.",
                "requires_human_approval": True,
                "flow_verdict": flow_observation.get("routing_verdict"),
            }
        proposal = dict(proposal)
        proposal["proposal_only"] = True
        proposal["requires_human_approval"] = True
        proposal["flow_verdict"] = flow_observation.get("routing_verdict")
        return proposal

    def write_outputs(self, result: LabResult) -> None:
        if self.recorder is not None:
            self.recorder.flush_admin_trace()
        payload = {
            "run_id": result.run_id,
            "timestamp": utc_timestamp(),
            "question": result.question,
            "run_plan": result.run_plan,
            "classification": result.classification,
            "workflow_decision": result.workflow_decision,
            "workflow_trace": result.workflow_trace,
            "simple_answer": result.simple_answer,
            "our_answer": result.our_answer,
            "chatgpt_answer": result.chatgpt_answer,
            "chatgpt_comparison": result.chatgpt_comparison,
            "baseline_answer": result.baseline_answer,
            "lens_trace": result.lens_trace,
            "blind_pack": result.blind_pack,
            "evaluation": result.evaluation,
            "revealed_evaluation": result.revealed_evaluation,
            "error_report": result.error_report,
            "flow_observation": result.flow_observation,
            "lesson_report": result.lesson_report,
            "critical_audit": result.critical_audit,
            "evolution_decision": result.evolution_decision,
            "trace_health": result.trace_health,
            "trace_events": result.trace_events,
            "agent_calls": result.agent_calls,
            "update_proposal": result.update_proposal,
            "warnings": result.warnings,
        }
        write_text(result.run_dir / "run.json", pretty_json(payload) + "\n")
        write_text(result.run_dir / "summary.md", render_summary(result))
        write_text(result.run_dir / "answers" / "simple.md", result.simple_answer + "\n")
        write_text(result.run_dir / "answers" / "ours.md", result.our_answer + "\n")
        write_text(result.run_dir / "answers" / "final.md", result.our_answer + "\n")
        if result.chatgpt_answer is not None:
            write_text(result.run_dir / "answers" / "chatgpt.md", result.chatgpt_answer + "\n")
        else:
            write_text(result.run_dir / "answers" / "chatgpt_pending.md", "Paste prompts/chatgpt_prompt.md into ChatGPT, then rerun with --chatgpt-answer-file.\n")
        if result.baseline_answer is not None:
            write_text(result.run_dir / "answers" / "baseline.md", result.baseline_answer + "\n")
        write_text(result.run_dir / "audits" / "chatgpt_comparison.json", pretty_json(result.chatgpt_comparison) + "\n")
        write_text(result.run_dir / "audits" / "critical_audit.json", pretty_json(result.critical_audit) + "\n")
        write_text(result.run_dir / "audits" / "evolution_decision.json", pretty_json(result.evolution_decision) + "\n")
        write_text(result.run_dir / "audits" / "trace_health.json", pretty_json(result.trace_health) + "\n")
        write_text(result.run_dir / "proposals" / "evolution_decision.json", pretty_json(result.evolution_decision) + "\n")
        ledger_dir = self.out_dir / "ledger"
        append_jsonl(ledger_dir / "runs.jsonl", payload)
        append_jsonl(ledger_dir / "evaluations.jsonl", {"run_id": result.run_id, "evaluation": result.revealed_evaluation})
        append_jsonl(ledger_dir / "flow_observations.jsonl", {"run_id": result.run_id, "flow_observation": result.flow_observation})
        append_jsonl(ledger_dir / "lessons.jsonl", {"run_id": result.run_id, "lesson_report": result.lesson_report})
        append_jsonl(ledger_dir / "critical_audits.jsonl", {"run_id": result.run_id, "critical_audit": result.critical_audit})
        append_jsonl(ledger_dir / "evolution_decisions.jsonl", {"run_id": result.run_id, "evolution_decision": result.evolution_decision})
        append_jsonl(ledger_dir / "trace_health.jsonl", {"run_id": result.run_id, "trace_health": result.trace_health})
        if result.update_proposal is not None:
            append_jsonl(ledger_dir / "update_proposals.jsonl", {"run_id": result.run_id, "update_proposal": result.update_proposal})


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(compact_json(value) + "\n")


def render_summary(result: LabResult) -> str:
    scores = result.revealed_evaluation.get("scores_by_source", {})
    lines = [
        "# Self Eval QA Lab Summary",
        "",
        f"- Run id: `{result.run_id}`",
        f"- Question: {result.question}",
        f"- Workflow: `{result.workflow_decision.get('selected_workflow', 'unknown')}`",
        f"- Winner: `{result.revealed_evaluation.get('winner_source', 'unknown')}`",
        f"- ChatGPT comparison: `{result.chatgpt_comparison.get('winner', 'unknown')}`",
        f"- Flow verdict: `{result.flow_observation.get('workflow_verdict', result.flow_observation.get('routing_verdict', 'unknown'))}`",
        f"- Critical recommendation: `{result.critical_audit.get('recommendation', 'unknown')}`",
        f"- Trace health: `{result.trace_health.get('status', 'unknown')}`",
        f"- Evolution: `{'change proposed' if result.evolution_decision.get('should_change_flow') else 'keep/collect'}`",
        "",
        "## Run Plan",
        "",
        pretty_json(result.run_plan),
        "",
        "## Workflow",
        "",
        pretty_json(result.workflow_decision),
        "",
        "## Workflow Trace",
        "",
        pretty_json(result.workflow_trace),
        "",
        "## Scores",
        "",
        "| Source | Total | Accuracy | Completeness | Clarity | Actionability | Constraint |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    if isinstance(scores, dict):
        for source, item in scores.items():
            if isinstance(item, dict):
                lines.append(
                    f"| {source} | {item.get('total', '')} | {item.get('accuracy', '')} | "
                    f"{item.get('completeness', '')} | {item.get('clarity', '')} | "
                    f"{item.get('actionability', '')} | {item.get('constraint_following', '')} |"
                )
    lines.extend(
        [
            "",
            "## Error Report",
            "",
            pretty_json(result.error_report),
            "",
            "## Flow Observation",
            "",
            pretty_json(result.flow_observation),
            "",
            "## ChatGPT Comparison",
            "",
            pretty_json(result.chatgpt_comparison),
            "",
            "## Lessons",
            "",
            pretty_json(result.lesson_report),
            "",
            "## Critical Audit",
            "",
            pretty_json(result.critical_audit),
            "",
            "## Evolution Decision",
            "",
            pretty_json(result.evolution_decision),
            "",
            "## Trace Health",
            "",
            pretty_json(result.trace_health),
            "",
            "## Trace",
            "",
            f"- Events: `{len(result.trace_events)}`",
            f"- Agent calls: `{len(result.agent_calls)}`",
            "- Admin full trace: `admin/full_trace.json`",
            "",
            "## Warnings",
            "",
        ]
    )
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def print_result(result: LabResult) -> None:
    print("SELF_EVAL_QA_LAB_RESULT")
    print(f"- run_id: {result.run_id}")
    print(f"- workflow: {result.workflow_decision.get('selected_workflow', 'unknown')}")
    print(f"- winner: {result.revealed_evaluation.get('winner_source', 'unknown')}")
    print(f"- chatgpt_comparison: {result.chatgpt_comparison.get('winner', 'unknown')}")
    print(f"- flow_verdict: {result.flow_observation.get('workflow_verdict', result.flow_observation.get('routing_verdict', 'unknown'))}")
    print(f"- critical_recommendation: {result.critical_audit.get('recommendation', 'unknown')}")
    print(f"- trace_health: {result.trace_health.get('status', 'unknown')}")
    print(f"- run_dir: {result.run_dir}")
    print(f"- summary: {result.run_dir / 'summary.md'}")
    print(f"- admin_trace: {result.run_dir / 'admin' / 'full_trace.json'}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Self-Evaluating Answer Flow Lab.")
    parser.add_argument("question", nargs="*", help="Question to evaluate.")
    parser.add_argument("--question-file", type=Path, help="Read the question from a file.")
    parser.add_argument("--mock", action="store_true", help="Run deterministic mock flow without LLM calls.")
    parser.add_argument("--dry-run", action="store_true", help="Show selected flow without LLM calls.")
    parser.add_argument("--list", action="store_true", help="List prompts, lenses, rubrics, and sample questions.")
    parser.add_argument("--baseline-mode", choices=["auto", "none", "local"], default=None, help="Optional baseline. 'auto' runs it only when the selected workflow asks for it.")
    parser.add_argument("--llm-provider", choices=["local", "server"], default=None, help="LLM route. local uses llm.py/LM Studio defaults; server uses --server-url or env.")
    parser.add_argument("--workflow", choices=["auto", *WORKFLOW_CHOICES], default="auto", help="Force a v0.2 workflow path, or let the router decide.")
    parser.add_argument("--chatgpt-mode", choices=["auto", "manual", "mock", "local", "server"], default="auto", help="ChatGPT baseline mode. auto uses mock in --mock runs, server when configured, otherwise manual prompt artifact.")
    parser.add_argument("--chatgpt-answer-file", type=Path, default=None, help="Manual ChatGPT answer file to compare against prompts/chatgpt_prompt.md.")
    parser.add_argument("--force-lenses", action="store_true", help="Run lens-based answer even when classifier says simple answer is enough.")
    parser.add_argument("--propose-updates", action="store_true", help="Emit proposal-only update suggestions; never applies them.")
    parser.add_argument("--model", default=None, help="Override LLM_MODEL from llm.py/.env.")
    parser.add_argument("--server-url", default=None, help="OpenAI-compatible server URL for --llm-provider server. Env: SELF_EVAL_SERVER_URL or LLM_SERVER_URL.")
    parser.add_argument("--server-api-key", default=None, help="API key for --llm-provider server. Env: SELF_EVAL_SERVER_API_KEY or LLM_SERVER_API_KEY.")
    parser.add_argument("--server-model", default=None, help="Model name for --llm-provider server. Env: SELF_EVAL_SERVER_MODEL or LLM_SERVER_MODEL.")
    parser.add_argument("--llm-timeout", type=float, default=None, help="Override LLM timeout in seconds.")
    parser.add_argument("--max-tokens", type=int, default=None, help="Override max tokens for LLM calls.")
    parser.add_argument("--temperature", type=float, default=0.2, help="LLM temperature. Default: 0.2.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for run outputs and ledger.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()
    baseline_mode = args.baseline_mode or config.default_baseline_mode
    forced_workflow = None if args.workflow == "auto" else args.workflow
    llm_options = build_llm_options(args, config)
    if args.list:
        list_assets()
        return 0
    question = read_question(args)
    if args.dry_run:
        dry_run(question, config, baseline_mode, args.force_lenses, forced_workflow, args.chatgpt_mode, llm_options)
        return 0
    if llm_options.provider == "server" and not llm_options.server_url and not args.mock:
        raise SystemExit(
            "Server LLM provider selected but no URL was provided. "
            "Set --server-url, SELF_EVAL_SERVER_URL, or LLM_SERVER_URL."
        )
    lab = SelfEvalLab(
        question=question,
        config=config,
        baseline_mode=baseline_mode,
        force_lenses=args.force_lenses,
        forced_workflow=forced_workflow,
        llm_options=llm_options,
        temperature=args.temperature,
        mock=args.mock,
        propose_updates=args.propose_updates,
        chatgpt_mode=args.chatgpt_mode,
        chatgpt_answer_file=args.chatgpt_answer_file,
        out_dir=args.out_dir,
    )
    result = lab.run()
    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
