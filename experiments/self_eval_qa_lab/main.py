from __future__ import annotations

import argparse
import hashlib
import json
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
DEFAULT_OUT_DIR = ROOT_DIR / "var" / "self_eval_qa_lab"

DEFAULT_LENSES = ["architecture", "critic", "practical", "clarity", "no_leap"]
ANSWER_CRITERIA = ["accuracy", "completeness", "clarity", "actionability", "constraint_following"]
FLOW_CRITERIA = ["flow_necessity", "routing_correctness", "step_efficiency", "error_visibility", "output_improvement"]


@dataclass(frozen=True)
class LabConfig:
    name: str = "self_eval_qa_lab"
    version: str = "0.1"
    default_lenses: list[str] = field(default_factory=lambda: list(DEFAULT_LENSES))
    default_baseline_mode: str = "none"
    self_update_enabled: bool = False
    proposal_only: bool = True


@dataclass(frozen=True)
class AnswerItem:
    source: str
    title: str
    answer: str


@dataclass
class LabResult:
    run_id: str
    run_dir: Path
    question: str
    classification: dict[str, Any]
    simple_answer: str
    our_answer: str
    baseline_answer: str | None
    lens_trace: list[dict[str, Any]]
    blind_pack: dict[str, Any]
    evaluation: dict[str, Any]
    revealed_evaluation: dict[str, Any]
    error_report: dict[str, Any]
    flow_observation: dict[str, Any]
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
    baseline = data.get("baseline") if isinstance(data.get("baseline"), dict) else {}
    self_update = data.get("self_update") if isinstance(data.get("self_update"), dict) else {}
    lenses = data.get("lenses") if isinstance(data.get("lenses"), dict) else {}
    default_lenses = lenses.get("default")
    if not isinstance(default_lenses, list):
        default_lenses = list(DEFAULT_LENSES)
    return LabConfig(
        name=str(lab.get("name") or "self_eval_qa_lab"),
        version=str(lab.get("version") or "0.1"),
        default_lenses=[str(item) for item in default_lenses],
        default_baseline_mode=str(baseline.get("default_mode") or "none"),
        self_update_enabled=bool(self_update.get("enabled", False)),
        proposal_only=bool(self_update.get("proposal_only", True)),
    )


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


def call_model(system_prompt: str, user_prompt: str, model: str | None, temperature: float) -> tuple[str, str]:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from llm import MODEL, call_llm

    selected_model = model or MODEL
    output = call_llm(system_prompt, user_prompt, model=selected_model, temperature=temperature)
    return selected_model, output


def call_json_model(
    system_prompt: str,
    user_prompt: str,
    fallback: dict[str, Any],
    model: str | None,
    temperature: float,
    warnings: list[str],
    label: str,
) -> dict[str, Any]:
    _, raw = call_model(system_prompt, user_prompt, model=model, temperature=temperature)
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
    return {
        "task_type": "technical_design" if "agent" in lower or "architecture" in lower or "thiết kế" in lower or "thiet ke" in lower else "general_qa",
        "complexity": complexity,
        "needs_lens_flow": complexity in {"medium", "high"},
        "suggested_lenses": suggested[:4],
        "reason": "Deterministic classifier uses question length and trade-off keywords.",
        "constraints": [],
        "unknowns": ["No external research was performed by the classifier."],
    }


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


def deterministic_flow_observation(
    classification: dict[str, Any],
    lens_trace: list[dict[str, Any]],
    revealed_evaluation: dict[str, Any],
    baseline_mode: str,
) -> dict[str, Any]:
    complexity = classification.get("complexity")
    needs_lens_flow = bool(classification.get("needs_lens_flow"))
    lens_count = len(lens_trace)
    winner_source = revealed_evaluation.get("winner_source")
    wasted = []
    if complexity == "low" and lens_count > 0:
        wasted.append({"step": "lens_flow", "reason": "Low-complexity question probably did not need a lens flow."})
    if lens_count == 0 and needs_lens_flow:
        missing = [{"step": "lens_flow", "reason": "Classifier marked the question as complex enough for lens review."}]
    else:
        missing = []
    score = 7
    if winner_source == "ours":
        score += 1
    if wasted:
        score -= 2
    if missing:
        score -= 2
    if baseline_mode == "none":
        score -= 1
    return {
        "flow_quality_score": max(0, min(10, score)),
        "was_lens_flow_justified": needs_lens_flow and not wasted,
        "wasted_steps": wasted,
        "missing_steps": missing,
        "routing_verdict": "good" if score >= 8 else "partially_good" if score >= 6 else "weak",
        "recommended_next_flow": ["question_classifier", *[item.get("lens", "") for item in lens_trace], "blind_evaluator", "flow_observer"],
        "anti_patterns_detected": ["no_external_baseline"] if baseline_mode == "none" else [],
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
    return "run_" + datetime.now().strftime("%Y%m%d-%H%M%S")


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


def dry_run(question: str, config: LabConfig, baseline_mode: str, force_lenses: bool) -> None:
    classification = classify_question_deterministic(question, config.default_lenses)
    selected_lenses = classification["suggested_lenses"] if (force_lenses or classification["needs_lens_flow"]) else []
    print("Self Eval QA Lab dry run")
    print(f"- lab: {config.name} v{config.version}")
    print(f"- baseline_mode: {baseline_mode}")
    print(f"- selected_lenses: {', '.join(selected_lenses) if selected_lenses else '(none)'}")
    print("\nFlow")
    print("1. Question Classifier")
    print("2. Simple Answer")
    print("3. Lens-Based Answer when justified")
    print("4. Optional Baseline Answer")
    print("5. Blind Evaluator")
    print("6. Error Analyzer")
    print("7. Flow Observer")
    print("8. Ledger")
    print("\nDeterministic classification")
    print(pretty_json(classification))


class SelfEvalLab:
    def __init__(
        self,
        question: str,
        config: LabConfig,
        baseline_mode: str,
        force_lenses: bool,
        model: str | None,
        temperature: float,
        mock: bool,
        propose_updates: bool,
        out_dir: Path,
    ) -> None:
        self.question = question
        self.config = config
        self.baseline_mode = baseline_mode
        self.force_lenses = force_lenses
        self.model = model
        self.temperature = temperature
        self.mock = mock
        self.propose_updates = propose_updates
        self.out_dir = out_dir
        self.warnings: list[str] = []
        self.answer_rubric = load_yaml(RUBRIC_DIR / "answer_quality_rubric.yaml")

    def run(self) -> LabResult:
        run_id = build_run_id()
        run_dir = self.out_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        classification = self.classify()
        simple_answer = self.simple_answer()
        selected_lenses = classification.get("suggested_lenses") or []
        needs_lenses = self.force_lenses or bool(classification.get("needs_lens_flow"))
        if needs_lenses:
            our_answer, lens_trace = self.lens_answer([str(item) for item in selected_lenses])
        else:
            our_answer = simple_answer
            lens_trace = []
        baseline_answer = self.baseline_answer()
        answers = [
            AnswerItem("simple", "Simple single-agent answer", simple_answer),
            AnswerItem("ours", "Lens-based answer", our_answer),
        ]
        if baseline_answer is not None:
            answers.append(AnswerItem("baseline", "External/local baseline answer", baseline_answer))
        blind_pack = blind_shuffle(answers, seed=stable_seed(run_id, self.question))
        evaluation = self.evaluate(blind_pack["visible_answers"])
        revealed = reveal_evaluation(evaluation, blind_pack["hidden_mapping"])
        error_report = self.error_analysis(classification, simple_answer, our_answer, baseline_answer, revealed)
        flow_observation = self.observe_flow(classification, lens_trace, revealed, error_report)
        update_proposal = self.update_proposal(error_report, flow_observation)
        result = LabResult(
            run_id=run_id,
            run_dir=run_dir,
            question=self.question,
            classification=classification,
            simple_answer=simple_answer,
            our_answer=our_answer,
            baseline_answer=baseline_answer,
            lens_trace=lens_trace,
            blind_pack=blind_pack,
            evaluation=evaluation,
            revealed_evaluation=revealed,
            error_report=error_report,
            flow_observation=flow_observation,
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
            model=self.model,
            temperature=0.0,
            warnings=self.warnings,
            label="question_classifier",
        )

    def simple_answer(self) -> str:
        if self.mock:
            return heuristic_answer(self.question, "Simple answer")
        system_prompt = load_prompt("simple_answer")
        _, output = call_model(system_prompt, self.question, model=self.model, temperature=self.temperature)
        return output.strip()

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
        _, output = call_model(system_prompt, self.question, model=self.model, temperature=self.temperature)
        return output.strip(), lens_trace

    def baseline_answer(self) -> str | None:
        if self.baseline_mode == "none":
            return None
        if self.mock:
            return heuristic_answer(self.question, "Baseline answer", ["clarity", "practical"])
        if self.baseline_mode == "local":
            system_prompt = load_prompt("baseline_answer")
            _, output = call_model(system_prompt, self.question, model=self.model, temperature=self.temperature)
            return output.strip()
        self.warnings.append(f"Unsupported baseline mode {self.baseline_mode!r}; skipped baseline.")
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
            model=self.model,
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
            model=self.model,
            temperature=0.0,
            warnings=self.warnings,
            label="error_analyzer",
        )

    def observe_flow(
        self,
        classification: dict[str, Any],
        lens_trace: list[dict[str, Any]],
        revealed_evaluation: dict[str, Any],
        error_report: dict[str, Any],
    ) -> dict[str, Any]:
        fallback = deterministic_flow_observation(classification, lens_trace, revealed_evaluation, self.baseline_mode)
        if self.mock:
            return fallback
        system_prompt = render_template(load_prompt("flow_observer"), {"FLOW_RUBRIC": pretty_json(load_yaml(RUBRIC_DIR / "flow_quality_rubric.yaml"))})
        payload = {
            "question": self.question,
            "classification": classification,
            "lens_trace": lens_trace,
            "evaluation": revealed_evaluation,
            "error_report": error_report,
            "cost_info": {
                "baseline_mode": self.baseline_mode,
                "num_lenses_used": len(lens_trace),
            },
        }
        return call_json_model(
            system_prompt,
            pretty_json(payload),
            fallback=fallback,
            model=self.model,
            temperature=0.0,
            warnings=self.warnings,
            label="flow_observer",
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
        payload = {
            "run_id": result.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": result.question,
            "classification": result.classification,
            "simple_answer": result.simple_answer,
            "our_answer": result.our_answer,
            "baseline_answer": result.baseline_answer,
            "lens_trace": result.lens_trace,
            "blind_pack": result.blind_pack,
            "evaluation": result.evaluation,
            "revealed_evaluation": result.revealed_evaluation,
            "error_report": result.error_report,
            "flow_observation": result.flow_observation,
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
        f"- Winner: `{result.revealed_evaluation.get('winner_source', 'unknown')}`",
        f"- Flow verdict: `{result.flow_observation.get('routing_verdict', 'unknown')}`",
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
    print(f"- winner: {result.revealed_evaluation.get('winner_source', 'unknown')}")
    print(f"- flow_verdict: {result.flow_observation.get('routing_verdict', 'unknown')}")
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
    parser.add_argument("--baseline-mode", choices=["none", "local"], default=None, help="Optional baseline. 'local' uses llm.py with a baseline prompt.")
    parser.add_argument("--force-lenses", action="store_true", help="Run lens-based answer even when classifier says simple answer is enough.")
    parser.add_argument("--propose-updates", action="store_true", help="Emit proposal-only update suggestions; never applies them.")
    parser.add_argument("--model", default=None, help="Override LLM_MODEL from llm.py/.env.")
    parser.add_argument("--temperature", type=float, default=0.2, help="LLM temperature. Default: 0.2.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for run outputs and ledger.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()
    baseline_mode = args.baseline_mode or config.default_baseline_mode
    if args.list:
        list_assets()
        return 0
    question = read_question(args)
    if args.dry_run:
        dry_run(question, config, baseline_mode, args.force_lenses)
        return 0
    lab = SelfEvalLab(
        question=question,
        config=config,
        baseline_mode=baseline_mode,
        force_lenses=args.force_lenses,
        model=args.model,
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
