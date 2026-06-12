from __future__ import annotations

import argparse
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
ANSWER_CRITERIA = ["accuracy", "completeness", "clarity", "actionability", "constraint_following"]
FLOW_CRITERIA = ["flow_necessity", "routing_correctness", "step_efficiency", "error_visibility", "output_improvement"]


@dataclass(frozen=True)
class LabConfig:
    name: str = "self_eval_qa_lab"
    version: str = "0.2"
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
    classification: dict[str, Any]
    workflow_decision: dict[str, Any]
    workflow_trace: list[dict[str, Any]]
    simple_answer: str
    our_answer: str
    baseline_answer: str | None
    lens_trace: list[dict[str, Any]]
    blind_pack: dict[str, Any]
    evaluation: dict[str, Any]
    revealed_evaluation: dict[str, Any]
    error_report: dict[str, Any]
    flow_observation: dict[str, Any]
    lesson_report: dict[str, Any]
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
        version=str(lab.get("version") or "0.2"),
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


def heuristic_answer(question: str, title: str, lenses: list[str] | None = None) -> str:
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
    simple = scores.get("simple", {})
    baseline = scores.get("baseline", {})
    where_lost = []
    where_won = []
    for key in ANSWER_CRITERIA + ["total"]:
        our_value = int(ours.get(key, 0)) if isinstance(ours, dict) else 0
        best_other = max(
            int(simple.get(key, 0)) if isinstance(simple, dict) else 0,
            int(baseline.get(key, 0)) if isinstance(baseline, dict) else 0,
        )
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
        "reason": "v0.2 records lessons and router proposals; it does not mutate prompts, lenses, or code.",
    }


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
    print(f"- workflow: {workflow_decision['selected_workflow']}")
    print(f"- selected_lenses: {', '.join(selected_lenses) if selected_lenses else '(none)'}")
    print("\nFlow")
    print("1. Question Classifier")
    print("2. Workflow Router")
    print("3. Direct / Assisted / Deep / Repo Debug Answer Path")
    print("4. Auto Baseline when route requests it")
    print("5. Blind Evaluator")
    print("6. Error Analyzer")
    print("7. Flow Observer")
    print("8. Lesson Extractor")
    print("9. Ledger")
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
        self.out_dir = out_dir
        self.warnings: list[str] = []
        self.answer_rubric = load_yaml(RUBRIC_DIR / "answer_quality_rubric.yaml")
        self.routing_policy = load_routing_policy()

    def run(self) -> LabResult:
        run_id = build_run_id()
        run_dir = self.out_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        classification = self.classify()
        workflow_decision = self.route_workflow(classification)
        simple_answer = self.simple_answer()
        our_answer, lens_trace, workflow_trace = self.workflow_answer(classification, workflow_decision, simple_answer)
        effective_baseline_mode = self.effective_baseline_mode(workflow_decision)
        baseline_answer = self.baseline_answer(effective_baseline_mode)
        answers = [
            AnswerItem("simple", "Simple single-agent answer", simple_answer),
            AnswerItem("ours", f"{workflow_decision.get('selected_workflow', 'workflow')} answer", our_answer),
        ]
        if baseline_answer is not None:
            answers.append(AnswerItem("baseline", "External/local baseline answer", baseline_answer))
        blind_pack = blind_shuffle(answers, seed=stable_seed(run_id, self.question))
        evaluation = self.evaluate(blind_pack["visible_answers"])
        revealed = reveal_evaluation(evaluation, blind_pack["hidden_mapping"])
        error_report = self.error_analysis(classification, simple_answer, our_answer, baseline_answer, revealed)
        flow_observation = self.observe_flow(classification, workflow_decision, workflow_trace, lens_trace, revealed, error_report, effective_baseline_mode)
        lesson_report = self.extract_lessons(workflow_decision, flow_observation, error_report)
        update_proposal = self.update_proposal(error_report, flow_observation)
        result = LabResult(
            run_id=run_id,
            run_dir=run_dir,
            question=self.question,
            classification=classification,
            workflow_decision=workflow_decision,
            workflow_trace=workflow_trace,
            simple_answer=simple_answer,
            our_answer=our_answer,
            baseline_answer=baseline_answer,
            lens_trace=lens_trace,
            blind_pack=blind_pack,
            evaluation=evaluation,
            revealed_evaluation=revealed,
            error_report=error_report,
            flow_observation=flow_observation,
            lesson_report=lesson_report,
            update_proposal=update_proposal,
            warnings=self.warnings,
        )
        self.write_outputs(result)
        return result

    def classify(self) -> dict[str, Any]:
        fallback = classify_question_deterministic(self.question, self.config.default_lenses)
        if self.mock:
            return fallback
        system_prompt = render_template(
            load_prompt("question_classifier"),
            {"AVAILABLE_LENSES": ", ".join(self.config.default_lenses)},
        )
        return call_json_model(
            system_prompt,
            self.question,
            fallback=fallback,
            llm_options=self.llm_options,
            temperature=0.0,
            warnings=self.warnings,
            label="question_classifier",
        )

    def route_workflow(self, classification: dict[str, Any]) -> dict[str, Any]:
        forced_workflow = self.forced_workflow
        if self.force_lenses and forced_workflow is None:
            forced_workflow = "deep"
        return route_workflow_deterministic(
            self.question,
            classification,
            policy=self.routing_policy,
            forced_workflow=forced_workflow,
        )

    def simple_answer(self) -> str:
        if self.mock:
            return heuristic_answer(self.question, "Simple answer")
        system_prompt = load_prompt("simple_answer")
        _, output = call_model(system_prompt, self.question, llm_options=self.llm_options, temperature=self.temperature)
        return output.strip()

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
        if self.mock:
            answer = "\n".join(
                [
                    "Assisted answer:",
                    "",
                    draft_answer,
                    "",
                    "Critic pass:",
                    "- Keep the answer compact, but name the trade-off and a concrete next step.",
                    "- Do not spawn specialist agents unless the question needs architecture-level reasoning.",
                    "",
                    "Rewrite note: this answer was improved by a lightweight draft-review-rewrite flow.",
                ]
            )
            return answer, trace
        system_prompt = load_prompt("simple_answer")
        user_prompt = "\n\n".join(
            [
                self.question,
                "Draft answer:",
                draft_answer,
                "Revise the draft after a critic pass. Do not write code.",
            ]
        )
        _, output = call_model(system_prompt, user_prompt, llm_options=self.llm_options, temperature=self.temperature)
        return output.strip(), trace

    def repo_debug_answer(self, draft_answer: str) -> tuple[str, list[dict[str, Any]]]:
        trace = [
            trace_step("scope", "repo_context_router", "Treated the question as local repo/debug reasoning."),
            trace_step("reason", "debug_reasoner", "Preferred local-context reasoning over an external baseline."),
            trace_step("synthesize", "answer_synthesizer", "Produced a no-code diagnostic answer."),
        ]
        if self.mock:
            answer = "\n".join(
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
            return answer, trace
        system_prompt = load_prompt("simple_answer")
        user_prompt = "\n\n".join(
            [
                self.question,
                "Answer as a repo/debug coordinator. Do not write code.",
            ]
        )
        _, output = call_model(system_prompt, user_prompt, llm_options=self.llm_options, temperature=self.temperature)
        return output.strip(), trace

    def lens_answer(self, lenses: list[str]) -> tuple[str, list[dict[str, Any]]]:
        selected = [lens for lens in lenses if lens in available_lenses()]
        if not selected:
            selected = self.config.default_lenses[:3]
        lens_trace = [{"lens": lens, "summary": f"Applied {lens} lens to the answer."} for lens in selected]
        if self.mock:
            return heuristic_answer(self.question, "Lens-based answer", selected), lens_trace
        system_prompt = render_template(
            load_prompt("answer_generator"),
            {
                "LENS_DOCS": selected_lens_docs(selected),
                "SELECTED_LENSES": ", ".join(selected),
            },
        )
        _, output = call_model(system_prompt, self.question, llm_options=self.llm_options, temperature=self.temperature)
        return output.strip(), lens_trace

    def effective_baseline_mode(self, workflow_decision: dict[str, Any]) -> str:
        if self.baseline_mode == "auto":
            return "local" if workflow_decision.get("needs_baseline") else "auto_skipped"
        return self.baseline_mode

    def baseline_answer(self, effective_baseline_mode: str) -> str | None:
        if effective_baseline_mode in {"none", "auto_skipped"}:
            return None
        if self.mock:
            return heuristic_answer(self.question, "Baseline answer", ["clarity", "practical"])
        if effective_baseline_mode == "local":
            system_prompt = load_prompt("baseline_answer")
            _, output = call_model(system_prompt, self.question, llm_options=self.llm_options, temperature=self.temperature)
            return output.strip()
        self.warnings.append(f"Unsupported baseline mode {effective_baseline_mode!r}; skipped baseline.")
        return None

    def evaluate(self, visible_answers: dict[str, str]) -> dict[str, Any]:
        fallback = deterministic_evaluation(self.question, visible_answers, self.answer_rubric)
        if self.mock:
            return fallback
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
        return call_json_model(
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            llm_options=self.llm_options,
            temperature=0.0,
            warnings=self.warnings,
            label="blind_evaluator",
        )

    def error_analysis(
        self,
        classification: dict[str, Any],
        simple_answer: str,
        our_answer: str,
        baseline_answer: str | None,
        revealed_evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        fallback = deterministic_error_report(revealed_evaluation)
        if self.mock:
            return fallback
        system_prompt = load_prompt("error_analyzer")
        payload = {
            "question": self.question,
            "classification": classification,
            "answers": {
                "simple": simple_answer,
                "ours": our_answer,
                "baseline": baseline_answer,
            },
            "evaluation": revealed_evaluation,
        }
        return call_json_model(
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            llm_options=self.llm_options,
            temperature=0.0,
            warnings=self.warnings,
            label="error_analyzer",
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
        if self.mock:
            return fallback
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
        return call_json_model(
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            llm_options=self.llm_options,
            temperature=0.0,
            warnings=self.warnings,
            label="flow_observer",
        )

    def extract_lessons(
        self,
        workflow_decision: dict[str, Any],
        flow_observation: dict[str, Any],
        error_report: dict[str, Any],
    ) -> dict[str, Any]:
        return deterministic_lesson_report(workflow_decision, flow_observation, error_report)

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
        payload = {
            "run_id": result.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": result.question,
            "classification": result.classification,
            "workflow_decision": result.workflow_decision,
            "workflow_trace": result.workflow_trace,
            "simple_answer": result.simple_answer,
            "our_answer": result.our_answer,
            "baseline_answer": result.baseline_answer,
            "lens_trace": result.lens_trace,
            "blind_pack": result.blind_pack,
            "evaluation": result.evaluation,
            "revealed_evaluation": result.revealed_evaluation,
            "error_report": result.error_report,
            "flow_observation": result.flow_observation,
            "lesson_report": result.lesson_report,
            "update_proposal": result.update_proposal,
            "warnings": result.warnings,
        }
        write_text(result.run_dir / "run.json", pretty_json(payload) + "\n")
        write_text(result.run_dir / "summary.md", render_summary(result))
        write_text(result.run_dir / "answers" / "simple.md", result.simple_answer + "\n")
        write_text(result.run_dir / "answers" / "ours.md", result.our_answer + "\n")
        if result.baseline_answer is not None:
            write_text(result.run_dir / "answers" / "baseline.md", result.baseline_answer + "\n")
        ledger_dir = self.out_dir / "ledger"
        append_jsonl(ledger_dir / "runs.jsonl", payload)
        append_jsonl(ledger_dir / "evaluations.jsonl", {"run_id": result.run_id, "evaluation": result.revealed_evaluation})
        append_jsonl(ledger_dir / "flow_observations.jsonl", {"run_id": result.run_id, "flow_observation": result.flow_observation})
        append_jsonl(ledger_dir / "lessons.jsonl", {"run_id": result.run_id, "lesson_report": result.lesson_report})
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
        f"- Flow verdict: `{result.flow_observation.get('workflow_verdict', result.flow_observation.get('routing_verdict', 'unknown'))}`",
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
            "## Lessons",
            "",
            pretty_json(result.lesson_report),
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
    print(f"- flow_verdict: {result.flow_observation.get('workflow_verdict', result.flow_observation.get('routing_verdict', 'unknown'))}")
    print(f"- run_dir: {result.run_dir}")
    print(f"- summary: {result.run_dir / 'summary.md'}")
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
        dry_run(question, config, baseline_mode, args.force_lenses, forced_workflow, llm_options)
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
        out_dir=args.out_dir,
    )
    result = lab.run()
    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
