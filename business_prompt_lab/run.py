from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


LAB_DIR = Path(__file__).resolve().parent
ROOT_DIR = LAB_DIR.parent
PROMPT_DIR = LAB_DIR / "prompts"
CASE_DIR = LAB_DIR / "cases"
DEFAULT_OUT_DIR = ROOT_DIR / "var" / "business_prompt_lab"

EXPECTED_TOP_LEVEL_KEYS = [
    "executive_summary",
    "decision",
    "business_model",
    "market",
    "risks",
    "assumptions",
    "unknowns",
    "next_steps",
]
BUSINESS_MODEL_KEYS = [
    "customer_segments",
    "value_proposition",
    "revenue_streams",
    "cost_drivers",
    "unit_economics_signals",
]
MARKET_KEYS = [
    "target_market",
    "competition",
    "demand_drivers",
    "adoption_constraints",
]
VALID_RECOMMENDATIONS = {"go", "no_go", "defer"}
VALID_SEVERITIES = {"low", "medium", "high"}
BANNED_PHRASES = [
    "as an ai",
    "i cannot provide",
    "it depends on various factors",
    "various factors",
]
TEMPLATE_ECHO_PHRASES = [
    "string, 1-2 concrete sentences",
    "go | no_go | defer",
    "number from 0.0 to 1.0",
    "2-4 short reasons",
    "specific customer segments",
    "specific value propositions",
    "likely revenue streams",
    "main cost drivers",
    "signals to validate",
    "target market slices",
    "direct or substitute competitors",
    "why customers would buy now",
    "why customers may not buy",
    "specific business risk",
    "low | medium | high",
    "practical mitigation",
    "assumptions the analysis relies on",
    "missing facts that could change",
    "specific validation action",
    "role or team",
    "what evidence proves or disproves it",
]

OUTPUT_SCHEMA = json.dumps(
    {
        "executive_summary": "string, 1-2 concrete sentences",
        "decision": {
            "recommendation": "go | no_go | defer",
            "confidence": "number from 0.0 to 1.0",
            "rationale": ["2-4 short reasons tied to facts or assumptions"],
        },
        "business_model": {
            "customer_segments": ["specific customer segments"],
            "value_proposition": ["specific value propositions"],
            "revenue_streams": ["likely revenue streams"],
            "cost_drivers": ["main cost drivers"],
            "unit_economics_signals": ["signals to validate pricing/margin/payback"],
        },
        "market": {
            "target_market": ["target market slices"],
            "competition": ["direct or substitute competitors"],
            "demand_drivers": ["why customers would buy now"],
            "adoption_constraints": ["why customers may not buy"],
        },
        "risks": [
            {
                "risk": "specific business risk",
                "severity": "low | medium | high",
                "mitigation": "practical mitigation",
            }
        ],
        "assumptions": ["assumptions the analysis relies on"],
        "unknowns": ["missing facts that could change the recommendation"],
        "next_steps": [
            {
                "action": "specific validation action",
                "owner": "role or team",
                "evidence_needed": "what evidence proves or disproves it",
            }
        ],
    },
    indent=2,
)


@dataclass(frozen=True)
class PromptSpec:
    id: str
    path: Path
    text: str


@dataclass(frozen=True)
class CaseSpec:
    id: str
    path: Path
    data: dict[str, Any]


@dataclass
class Evaluation:
    score: int
    verdict: str
    checks: dict[str, bool]
    missing_keys: list[str]
    extra_keys: list[str]
    parse_note: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def available_prompts() -> list[PromptSpec]:
    prompts = []
    for path in sorted(PROMPT_DIR.glob("*.md")):
        prompts.append(PromptSpec(id=path.stem, path=path, text=read_text(path)))
    return prompts


def available_cases() -> list[CaseSpec]:
    cases = []
    for path in sorted(CASE_DIR.glob("*.json")):
        data = read_json(path)
        cases.append(CaseSpec(id=str(data.get("id") or path.stem), path=path, data=data))
    return cases


def select_specs(specs: list[Any], selector: str, label: str) -> list[Any]:
    if selector == "all":
        return specs

    selected = []
    for token in [item.strip() for item in selector.split(",") if item.strip()]:
        matches = [spec for spec in specs if spec.id == token or spec.id.startswith(token)]
        if len(matches) != 1:
            known = ", ".join(spec.id for spec in specs)
            raise SystemExit(f"Cannot resolve {label} {token!r}. Known {label}s: {known}")
        selected.append(matches[0])
    return selected


def bullet_list(items: Any) -> str:
    if not items:
        return "- Not provided"
    if isinstance(items, str):
        return f"- {items}"
    return "\n".join(f"- {item}" for item in items)


def case_user_message(case: CaseSpec) -> str:
    data = case.data
    return "\n".join(
        [
            "Business analysis case",
            f"Case id: {case.id}",
            f"Title: {data.get('title', case.id)}",
            "",
            "Business task:",
            str(data.get("business_task", "")).strip(),
            "",
            "Company context:",
            str(data.get("company_context", "")).strip(),
            "",
            "Known facts:",
            bullet_list(data.get("available_facts")),
            "",
            "Constraints:",
            bullet_list(data.get("constraints")),
            "",
            "Requested focus:",
            bullet_list(data.get("requested_focus")),
        ]
    )


def render_prompt(prompt: PromptSpec, case: CaseSpec) -> str:
    replacements = {
        "{{OUTPUT_SCHEMA}}": OUTPUT_SCHEMA,
        "{{CASE_ID}}": case.id,
        "{{TODAY}}": datetime.now().date().isoformat(),
    }
    rendered = prompt.text
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    return rendered


def decode_json_candidate(candidate: str) -> tuple[dict[str, Any] | None, bool]:
    decoder = json.JSONDecoder()
    try:
        parsed, index = decoder.raw_decode(candidate)
    except json.JSONDecodeError:
        return None, False
    if not isinstance(parsed, dict):
        return None, False
    return parsed, candidate[index:].strip() == ""


def parse_json_object(text: str) -> tuple[dict[str, Any] | None, bool, str]:
    raw = text.strip()
    if not raw:
        return None, False, "empty output"

    parsed, exact = decode_json_candidate(raw)
    if parsed is not None and exact:
        return parsed, True, "strict JSON object"

    fence_match = re.fullmatch(r"```(?:json)?\s*(?P<body>.*?)\s*```", raw, re.IGNORECASE | re.DOTALL)
    if fence_match:
        parsed, exact = decode_json_candidate(fence_match.group("body").strip())
        if parsed is not None and exact:
            return parsed, False, "JSON object wrapped in markdown fence"

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", raw):
        try:
            parsed, _ = decoder.raw_decode(raw[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed, False, "JSON object with surrounding text"

    return None, False, "no JSON object found"


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def meaningful_string(value: Any) -> bool:
    if not nonempty_string(value):
        return False
    lowered = value.lower()
    return not any(phrase in lowered for phrase in TEMPLATE_ECHO_PHRASES)


def nonempty_list(value: Any, min_len: int = 1) -> bool:
    return isinstance(value, list) and len([item for item in value if item]) >= min_len


def list_of_nonempty_strings(value: Any, min_len: int = 1) -> bool:
    return isinstance(value, list) and len([item for item in value if meaningful_string(item)]) >= min_len


def decision_valid(data: dict[str, Any]) -> bool:
    decision = data.get("decision")
    if not isinstance(decision, dict):
        return False
    confidence = decision.get("confidence")
    return (
        decision.get("recommendation") in VALID_RECOMMENDATIONS
        and isinstance(confidence, (int, float))
        and 0.0 <= float(confidence) <= 1.0
        and list_of_nonempty_strings(decision.get("rationale"), min_len=2)
    )


def nested_sections_complete(data: dict[str, Any]) -> bool:
    business_model = data.get("business_model")
    market = data.get("market")
    if not isinstance(business_model, dict) or not isinstance(market, dict):
        return False
    return (
        all(list_of_nonempty_strings(business_model.get(key)) for key in BUSINESS_MODEL_KEYS)
        and all(list_of_nonempty_strings(market.get(key)) for key in MARKET_KEYS)
        and list_of_nonempty_strings(data.get("assumptions"), min_len=2)
        and list_of_nonempty_strings(data.get("unknowns"), min_len=2)
    )


def risks_valid(data: dict[str, Any]) -> bool:
    risks = data.get("risks")
    if not nonempty_list(risks, min_len=3):
        return False
    for risk in risks:
        if not isinstance(risk, dict):
            return False
        if not meaningful_string(risk.get("risk")):
            return False
        if risk.get("severity") not in VALID_SEVERITIES:
            return False
        if not meaningful_string(risk.get("mitigation")):
            return False
    return True


def next_steps_valid(data: dict[str, Any]) -> bool:
    next_steps = data.get("next_steps")
    if not nonempty_list(next_steps, min_len=3):
        return False
    for step in next_steps:
        if not isinstance(step, dict):
            return False
        if not meaningful_string(step.get("action")):
            return False
        if not meaningful_string(step.get("owner")):
            return False
        if not meaningful_string(step.get("evidence_needed")):
            return False
    return True


def concise_summary_valid(data: dict[str, Any]) -> bool:
    summary = data.get("executive_summary")
    if not meaningful_string(summary):
        return False
    sentence_count = len([part for part in re.split(r"[.!?]+", summary) if part.strip()])
    return 40 <= len(summary.strip()) <= 500 and sentence_count <= 2


def evaluate_output(text: str) -> Evaluation:
    parsed, strict_json, parse_note = parse_json_object(text)
    checks: dict[str, bool] = {
        "json_valid": parsed is not None,
        "strict_json_only": strict_json,
        "top_level_keys_complete": False,
        "no_extra_top_level_keys": False,
        "decision_valid": False,
        "sections_complete": False,
        "risks_valid": False,
        "next_steps_valid": False,
        "concise_summary": False,
        "no_banned_phrases": not any(phrase in text.lower() for phrase in BANNED_PHRASES),
    }
    missing_keys = EXPECTED_TOP_LEVEL_KEYS.copy()
    extra_keys: list[str] = []

    if parsed is not None:
        keys = set(parsed.keys())
        expected = set(EXPECTED_TOP_LEVEL_KEYS)
        missing_keys = [key for key in EXPECTED_TOP_LEVEL_KEYS if key not in keys]
        extra_keys = sorted(keys - expected)
        checks.update(
            {
                "top_level_keys_complete": not missing_keys,
                "no_extra_top_level_keys": not extra_keys,
                "decision_valid": decision_valid(parsed),
                "sections_complete": nested_sections_complete(parsed),
                "risks_valid": risks_valid(parsed),
                "next_steps_valid": next_steps_valid(parsed),
                "concise_summary": concise_summary_valid(parsed),
            }
        )

    weights = {
        "json_valid": 20,
        "strict_json_only": 10,
        "top_level_keys_complete": 10,
        "no_extra_top_level_keys": 5,
        "decision_valid": 10,
        "sections_complete": 15,
        "risks_valid": 10,
        "next_steps_valid": 10,
        "concise_summary": 5,
        "no_banned_phrases": 5,
    }
    score = sum(weight for key, weight in weights.items() if checks[key])
    verdict = "strong" if score >= 85 else "usable" if score >= 70 else "weak" if score >= 50 else "fail"
    return Evaluation(
        score=score,
        verdict=verdict,
        checks=checks,
        missing_keys=missing_keys,
        extra_keys=extra_keys,
        parse_note=parse_note,
    )


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")


def call_model(system_prompt: str, user_prompt: str, model: str | None, temperature: float) -> tuple[str, str]:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

    from llm import MODEL, call_llm

    selected_model = model or MODEL
    output = call_llm(
        system_prompt,
        user_prompt,
        model=selected_model,
        temperature=temperature,
    )
    return selected_model, output


def write_run_inputs(run_dir: Path, file_stem: str, system_prompt: str, user_prompt: str) -> None:
    inputs_dir = run_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    (inputs_dir / f"{file_stem}.system.md").write_text(system_prompt, encoding="utf-8")
    (inputs_dir / f"{file_stem}.user.md").write_text(user_prompt, encoding="utf-8")


def print_ranking(results: list[dict[str, Any]]) -> None:
    by_prompt: dict[str, list[int]] = {}
    for result in results:
        by_prompt.setdefault(result["prompt"], []).append(int(result["evaluation"]["score"]))

    ranking = sorted(
        ((prompt, mean(scores), min(scores), max(scores), len(scores)) for prompt, scores in by_prompt.items()),
        key=lambda row: row[1],
        reverse=True,
    )
    print("\nPrompt ranking")
    print("prompt                         avg   min   max   n")
    print("-" * 55)
    for prompt, avg_score, min_score, max_score, count in ranking:
        print(f"{prompt:<30} {avg_score:>5.1f} {min_score:>5} {max_score:>5} {count:>3}")


def summary_markdown(results: list[dict[str, Any]], run_dir: Path, config: dict[str, Any]) -> str:
    lines = [
        "# Business Prompt Lab Summary",
        "",
        f"- Run directory: `{run_dir}`",
        f"- Temperature: `{config['temperature']}`",
        f"- Runs per prompt/case: `{config['runs']}`",
        f"- Model: `{config['model']}`",
        "",
        "## Ranking",
        "",
        "| Prompt | Avg | Min | Max | Runs |",
        "|---|---:|---:|---:|---:|",
    ]
    by_prompt: dict[str, list[int]] = {}
    for result in results:
        by_prompt.setdefault(result["prompt"], []).append(int(result["evaluation"]["score"]))
    for prompt, scores in sorted(by_prompt.items(), key=lambda item: mean(item[1]), reverse=True):
        lines.append(f"| {prompt} | {mean(scores):.1f} | {min(scores)} | {max(scores)} | {len(scores)} |")

    lines.extend(["", "## Runs", "", "| Case | Prompt | Run | Score | Verdict | Parse | Output |", "|---|---|---:|---:|---|---|---|"])
    for result in sorted(results, key=lambda item: item["evaluation"]["score"], reverse=True):
        evaluation = result["evaluation"]
        output_path = Path(result["output_file"]).as_posix()
        lines.append(
            f"| {result['case']} | {result['prompt']} | {result['run']} | "
            f"{evaluation['score']} | {evaluation['verdict']} | {evaluation['parse_note']} | `{output_path}` |"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run business-analysis prompt experiments through llm.py.")
    parser.add_argument("--prompt", default="all", help="Prompt id, prefix, comma list, or 'all'. Default: all.")
    parser.add_argument("--case", default="saas_market_entry", help="Case id, prefix, comma list, or 'all'.")
    parser.add_argument("--runs", type=int, default=1, help="Repetitions per prompt/case pair. Default: 1.")
    parser.add_argument("--temperature", type=float, default=0.1, help="LLM temperature. Default: 0.1.")
    parser.add_argument("--model", default=None, help="Override LLM_MODEL from llm.py/.env.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for run outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Show selected prompt/case matrix without calling LLM.")
    parser.add_argument("--list", action="store_true", help="List available prompts and cases.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    prompts = available_prompts()
    cases = available_cases()
    if not prompts:
        raise SystemExit(f"No prompt files found in {PROMPT_DIR}")
    if not cases:
        raise SystemExit(f"No case files found in {CASE_DIR}")

    if args.list:
        print("Prompts:")
        for prompt in prompts:
            print(f"- {prompt.id}: {prompt.path.relative_to(ROOT_DIR)}")
        print("\nCases:")
        for case in cases:
            print(f"- {case.id}: {case.path.relative_to(ROOT_DIR)}")
        return 0

    selected_prompts = select_specs(prompts, args.prompt, "prompt")
    selected_cases = select_specs(cases, args.case, "case")

    print("Selected matrix")
    print(f"- Prompts: {', '.join(prompt.id for prompt in selected_prompts)}")
    print(f"- Cases: {', '.join(case.id for case in selected_cases)}")
    print(f"- Runs per pair: {args.runs}")
    print(f"- Temperature: {args.temperature}")

    if args.dry_run:
        print("\nDry run only. No LLM calls were made.")
        return 0

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = args.out_dir / timestamp
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=False)

    results: list[dict[str, Any]] = []
    selected_model = args.model or "(llm.py default)"

    for case in selected_cases:
        user_prompt = case_user_message(case)
        for prompt in selected_prompts:
            system_prompt = render_prompt(prompt, case)
            for run_number in range(1, args.runs + 1):
                file_stem = safe_name(f"{case.id}__{prompt.id}__run{run_number:02d}")
                print(f"\nRunning {file_stem}")
                write_run_inputs(run_dir, file_stem, system_prompt, user_prompt)
                selected_model, output = call_model(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=args.model,
                    temperature=args.temperature,
                )
                output_file = outputs_dir / f"{file_stem}.txt"
                output_file.write_text(output, encoding="utf-8")
                evaluation = evaluate_output(output)
                print(f"Score: {evaluation.score}/100 ({evaluation.verdict}); parse: {evaluation.parse_note}")
                results.append(
                    {
                        "case": case.id,
                        "prompt": prompt.id,
                        "run": run_number,
                        "prompt_file": str(prompt.path.relative_to(ROOT_DIR)),
                        "case_file": str(case.path.relative_to(ROOT_DIR)),
                        "output_file": str(output_file.relative_to(ROOT_DIR)),
                        "evaluation": asdict(evaluation),
                    }
                )

    config = {
        "temperature": args.temperature,
        "runs": args.runs,
        "model": selected_model,
        "prompts": [prompt.id for prompt in selected_prompts],
        "cases": [case.id for case in selected_cases],
    }
    (run_dir / "summary.json").write_text(
        json.dumps({"config": config, "results": results}, indent=2),
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text(summary_markdown(results, run_dir, config), encoding="utf-8")

    print_ranking(results)
    print(f"\nWrote summary: {run_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
