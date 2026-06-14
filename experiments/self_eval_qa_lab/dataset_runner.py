from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parent
ROOT_DIR = LAB_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from experiments.self_eval_qa_lab import dataset_loader
from experiments.self_eval_qa_lab import main as lab


DEFAULT_DATASET_RUN_DIR = lab.DEFAULT_OUT_DIR / "dataset_runs"


@dataclass(frozen=True)
class RuntimePolicy:
    revision: int = 0
    prompt_style: str = "standard"
    forced_workflow: str | None = None
    force_lenses: bool = False
    notes: list[str] = field(default_factory=list)


def now_id(prefix: str) -> str:
    return prefix + "_" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def should_review_case(completed_count: int, review_every: int) -> bool:
    if review_every <= 0:
        raise ValueError("--review-every must be greater than zero")
    return completed_count > 0 and completed_count % review_every == 0


def case_reference(case: dataset_loader.DatasetCase) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "dataset_id": case.dataset_id,
        "subset": case.subset,
        "split": case.split,
        "source_path": case.source_path,
        "answer_letter": case.answer_letter,
        "answer_text": case.answer_text,
        "row_index": case.metadata.get("row_index"),
    }


def summarize_lab_result(case: dataset_loader.DatasetCase, result: lab.LabResult) -> dict[str, Any]:
    parsed_answer = dataset_loader.parse_multiple_choice_answer(result.our_answer, case.options)
    correct = parsed_answer == case.answer_letter if parsed_answer else False
    return {
        "case_id": case.case_id,
        "dataset_id": case.dataset_id,
        "subset": case.subset,
        "split": case.split,
        "run_id": result.run_id,
        "run_dir": str(result.run_dir),
        "workflow": result.workflow_decision.get("selected_workflow"),
        "prompt_style": None,
        "answer_key": case.answer_letter,
        "answer_text": case.answer_text,
        "parsed_answer": parsed_answer,
        "correct": correct,
        "parse_success": parsed_answer is not None,
        "trace_health_status": result.trace_health.get("status"),
        "trace_severe_count": result.trace_health.get("severe_count", 0),
        "looping_detected": result.trace_health.get("looping_detected", False),
        "json_fallback_count": len(result.trace_health.get("json_fallbacks") or []),
        "code_violation_count": len(result.trace_health.get("code_violations") or []),
        "chatgpt_comparison": {
            "status": result.chatgpt_comparison.get("status"),
            "winner": result.chatgpt_comparison.get("winner"),
        },
        "critical_audit": {
            "logic_score": result.critical_audit.get("logic_score"),
            "recommendation": result.critical_audit.get("recommendation"),
        },
        "warnings": list(result.warnings),
    }


def summarize_error(case: dataset_loader.DatasetCase, exc: BaseException) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "dataset_id": case.dataset_id,
        "subset": case.subset,
        "split": case.split,
        "run_id": None,
        "run_dir": None,
        "workflow": None,
        "prompt_style": None,
        "answer_key": case.answer_letter,
        "answer_text": case.answer_text,
        "parsed_answer": None,
        "correct": False,
        "parse_success": False,
        "trace_health_status": "error",
        "trace_severe_count": 1,
        "looping_detected": False,
        "json_fallback_count": 0,
        "code_violation_count": 0,
        "chatgpt_comparison": {"status": "error", "winner": None},
        "critical_audit": {"logic_score": None, "recommendation": "error"},
        "warnings": [f"{type(exc).__name__}: {exc}"],
    }


def review_batch(
    records: list[dict[str, Any]],
    *,
    batch_index: int,
    policy: RuntimePolicy,
    target_accuracy: float,
) -> dict[str, Any]:
    total = len(records)
    parse_success = sum(1 for record in records if record.get("parse_success"))
    correct = sum(1 for record in records if record.get("correct"))
    error_count = sum(1 for record in records if record.get("trace_health_status") == "error")
    severe_count = sum(int(record.get("trace_severe_count") or 0) for record in records)
    loop_count = sum(1 for record in records if record.get("looping_detected"))
    json_fallback_count = sum(int(record.get("json_fallback_count") or 0) for record in records)
    code_violation_count = sum(int(record.get("code_violation_count") or 0) for record in records)
    clean_count = sum(1 for record in records if record.get("trace_health_status") == "clean")

    accuracy = correct / total if total else 0.0
    parse_success_rate = parse_success / total if total else 0.0
    accuracy_on_parseable = correct / parse_success if parse_success else 0.0
    clean_trace_rate = clean_count / total if total else 0.0
    accuracy_evaluable = parse_success_rate >= 0.95 and error_count == 0

    issues: list[dict[str, Any]] = []
    if parse_success_rate < 0.95:
        issues.append(
            {
                "issue": "answer_parse_failures",
                "severity": "high" if parse_success_rate < 0.8 else "medium",
                "evidence": f"{parse_success}/{total} cases had a parseable final answer.",
            }
        )
    if accuracy_evaluable and accuracy < target_accuracy:
        issues.append(
            {
                "issue": "low_accuracy",
                "severity": "high" if accuracy < max(target_accuracy * 0.5, 0.2) else "medium",
                "evidence": f"{correct}/{total} cases matched the answer key.",
            }
        )
    if severe_count:
        issues.append(
            {
                "issue": "trace_health_severe",
                "severity": "high",
                "evidence": f"Trace health reported {severe_count} severe signals across the batch.",
            }
        )
    if loop_count:
        issues.append(
            {
                "issue": "looping_detected",
                "severity": "high",
                "evidence": f"{loop_count}/{total} cases had loop signals.",
            }
        )
    if json_fallback_count:
        issues.append(
            {
                "issue": "json_fallbacks",
                "severity": "medium",
                "evidence": f"{json_fallback_count} JSON fallback signals were observed.",
            }
        )
    if code_violation_count:
        issues.append(
            {
                "issue": "code_violations",
                "severity": "medium",
                "evidence": f"{code_violation_count} no-code violations were observed.",
            }
        )
    if error_count:
        issues.append(
            {
                "issue": "case_errors",
                "severity": "high",
                "evidence": f"{error_count}/{total} cases failed before producing a normal lab result.",
            }
        )

    return {
        "review_type": "batch_critical_review",
        "batch_index": batch_index,
        "case_count": total,
        "policy_before": asdict(policy),
        "metrics": {
            "accuracy": accuracy,
            "accuracy_on_parseable": accuracy_on_parseable,
            "accuracy_evaluable": accuracy_evaluable,
            "correct": correct,
            "parse_success_rate": parse_success_rate,
            "parse_success": parse_success,
            "clean_trace_rate": clean_trace_rate,
            "clean_trace_count": clean_count,
            "error_count": error_count,
            "severe_count": severe_count,
            "loop_count": loop_count,
            "json_fallback_count": json_fallback_count,
            "code_violation_count": code_violation_count,
        },
        "issues": issues,
        "evidence_case_ids": [record["case_id"] for record in records],
    }


def decide_batch_adjustment(review: dict[str, Any], policy: RuntimePolicy) -> tuple[RuntimePolicy, list[dict[str, Any]]]:
    issues = {item["issue"]: item for item in review.get("issues", [])}
    recommendations: list[dict[str, Any]] = []
    next_policy = policy

    if "answer_parse_failures" in issues and next_policy.prompt_style != "strict_final":
        next_policy = replace(
            next_policy,
            prompt_style="strict_final",
            revision=next_policy.revision + 1,
            notes=[*next_policy.notes, "Batch evidence showed parse failures; tightened final-answer contract."],
        )
        recommendations.append(
            {
                "field": "prompt_style",
                "from": policy.prompt_style,
                "to": "strict_final",
                "reason": issues["answer_parse_failures"]["evidence"],
            }
        )

    if "low_accuracy" in issues:
        if next_policy.forced_workflow is None:
            old = next_policy.forced_workflow
            next_policy = replace(
                next_policy,
                forced_workflow="assisted",
                revision=next_policy.revision + 1,
                notes=[*next_policy.notes, "Batch evidence showed low accuracy; moved next batch to assisted workflow."],
            )
            recommendations.append(
                {
                    "field": "forced_workflow",
                    "from": old,
                    "to": "assisted",
                    "reason": issues["low_accuracy"]["evidence"],
                }
            )
        elif next_policy.forced_workflow == "assisted":
            next_policy = replace(
                next_policy,
                forced_workflow="deep",
                force_lenses=True,
                prompt_style="deliberate",
                revision=next_policy.revision + 1,
                notes=[*next_policy.notes, "Second low-accuracy batch; escalated next batch to deep lens workflow."],
            )
            recommendations.append(
                {
                    "field": "forced_workflow",
                    "from": "assisted",
                    "to": "deep",
                    "reason": issues["low_accuracy"]["evidence"],
                }
            )

    if ("looping_detected" in issues or "trace_health_severe" in issues) and next_policy.forced_workflow == "deep":
        next_policy = replace(
            next_policy,
            forced_workflow="assisted",
            force_lenses=False,
            revision=next_policy.revision + 1,
            notes=[*next_policy.notes, "Trace health showed loop/severe signals; reduced next batch to assisted workflow."],
        )
        recommendations.append(
            {
                "field": "forced_workflow",
                "from": "deep",
                "to": "assisted",
                "reason": "Severe trace health or loop signals should be fixed before adding more agents.",
            }
        )

    return next_policy, recommendations


def build_summary_markdown(
    *,
    dataset_run_id: str,
    cases: list[dataset_loader.DatasetCase],
    records: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    final_policy: RuntimePolicy,
) -> str:
    total = len(records)
    correct = sum(1 for record in records if record.get("correct"))
    parse_success = sum(1 for record in records if record.get("parse_success"))
    clean_trace = sum(1 for record in records if record.get("trace_health_status") == "clean")
    lines = [
        f"# Dataset Run {dataset_run_id}",
        "",
        f"- Cases loaded: {len(cases)}",
        f"- Cases completed: {total}",
        f"- Accuracy: {correct}/{total}" if total else "- Accuracy: n/a",
        f"- Parse success: {parse_success}/{total}" if total else "- Parse success: n/a",
        f"- Clean trace: {clean_trace}/{total}" if total else "- Clean trace: n/a",
        f"- Batch reviews: {len(reviews)}",
        f"- Final runtime policy: `{json.dumps(asdict(final_policy), ensure_ascii=False)}`",
        "",
        "## Batch Reviews",
    ]
    if not reviews:
        lines.append("- No review was run because no full review interval completed.")
    for review in reviews:
        metrics = review.get("metrics", {})
        lines.append(
            "- "
            f"batch {review.get('batch_index')}: "
            f"accuracy={metrics.get('correct')}/{review.get('case_count')}, "
            f"parse={metrics.get('parse_success')}/{review.get('case_count')}, "
            f"accuracy_evaluable={metrics.get('accuracy_evaluable')}, "
            f"severe={metrics.get('severe_count')}, "
            f"recommendations={len(review.get('recommendations') or [])}"
        )
    return "\n".join(lines) + "\n"


def run_benchmark(args: argparse.Namespace) -> int:
    config = lab.load_config()
    llm_options = lab.build_llm_options(args, config)
    selected_subsets = dataset_loader.split_subset_arg(args.subsets)
    cases = dataset_loader.load_logikon_cases(
        subsets=selected_subsets,
        limit=args.limit,
        offset=args.offset,
        shuffle=args.shuffle,
        seed=args.seed,
        cache_dir=args.dataset_cache_dir,
        refresh=args.refresh_dataset,
    )
    if not cases:
        raise SystemExit("No dataset cases loaded.")

    dataset_run_id = now_id("dataset")
    dataset_run_dir = args.out_dir / dataset_run_id
    case_run_dir = dataset_run_dir / "case_runs"
    dataset_run_dir.mkdir(parents=True, exist_ok=False)

    user_forced_workflow = None if args.workflow == "auto" else args.workflow
    policy = RuntimePolicy(
        prompt_style=args.prompt_style,
        forced_workflow=user_forced_workflow,
        force_lenses=args.force_lenses,
        notes=["Initial policy from CLI."],
    )
    baseline_mode = args.baseline_mode or config.default_baseline_mode
    chatgpt_mode = args.chatgpt_mode or ("mock" if args.mock else "auto")
    records: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []

    write_json(
        dataset_run_dir / "dataset_manifest.json",
        {
            "dataset_run_id": dataset_run_id,
            "source": "logikon/logikon-bench",
            "subsets": selected_subsets or dataset_loader.available_subsets(),
            "limit": args.limit,
            "offset": args.offset,
            "shuffle": args.shuffle,
            "seed": args.seed,
            "review_every": args.review_every,
            "target_accuracy": args.target_accuracy,
            "cases": [case_reference(case) for case in cases],
        },
    )

    print(f"Dataset run: {dataset_run_id}")
    print(f"Cases: {len(cases)}")
    print(f"Review cadence: every {args.review_every} completed cases")

    for index, case in enumerate(cases, start=1):
        question = dataset_loader.render_case_question(case, prompt_style=policy.prompt_style)
        try:
            runner = lab.SelfEvalLab(
                question=question,
                config=config,
                baseline_mode=baseline_mode,
                force_lenses=policy.force_lenses,
                forced_workflow=policy.forced_workflow,
                llm_options=llm_options,
                temperature=args.temperature,
                mock=args.mock,
                propose_updates=args.propose_updates,
                chatgpt_mode=chatgpt_mode,
                chatgpt_answer_file=None,
                out_dir=case_run_dir,
            )
            result = runner.run()
            record = summarize_lab_result(case, result)
        except Exception as exc:
            if args.fail_fast:
                raise
            record = summarize_error(case, exc)

        record["case_number"] = index
        record["prompt_style"] = policy.prompt_style
        record["runtime_policy_revision"] = policy.revision
        append_jsonl(dataset_run_dir / "case_results.jsonl", record)
        write_json(dataset_run_dir / "cases" / f"{index:05d}_{dataset_loader.safe_case_filename(case.case_id)}.json", record)
        records.append(record)
        print(
            f"[{index}/{len(cases)}] {case.case_id} "
            f"parsed={record.get('parsed_answer') or '-'} key={case.answer_letter} "
            f"correct={record.get('correct')} trace={record.get('trace_health_status')}"
        )

        if should_review_case(len(records), args.review_every):
            batch_records = records[-args.review_every :]
            batch_index = len(records) // args.review_every
            review = review_batch(
                batch_records,
                batch_index=batch_index,
                policy=policy,
                target_accuracy=args.target_accuracy,
            )
            new_policy, recommendations = decide_batch_adjustment(review, policy)
            review["recommendations"] = recommendations
            review["policy_after"] = asdict(new_policy)
            reviews.append(review)
            write_json(dataset_run_dir / "batch_reviews" / f"batch_{batch_index:04d}_review.json", review)
            policy = new_policy
            write_json(dataset_run_dir / "runtime_policy.json", asdict(policy))
            print(
                f"[batch {batch_index}] review complete: "
                f"accuracy={review['metrics']['correct']}/{review['case_count']} "
                f"recommendations={len(recommendations)}"
            )

    write_json(dataset_run_dir / "runtime_policy.json", asdict(policy))
    summary = build_summary_markdown(
        dataset_run_id=dataset_run_id,
        cases=cases,
        records=records,
        reviews=reviews,
        final_policy=policy,
    )
    (dataset_run_dir / "summary.md").write_text(summary, encoding="utf-8")
    print(f"Summary: {dataset_run_dir / 'summary.md'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Self Eval QA Lab against Open CoT Leaderboard-style datasets.")
    parser.add_argument("--dataset", choices=["logikon-bench"], default="logikon-bench")
    parser.add_argument("--subsets", default="logiqa", help="Comma-separated subsets. Default: logiqa. Use empty string for all.")
    parser.add_argument("--limit", type=int, default=20, help="Number of cases to run. Default: 20.")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--refresh-dataset", action="store_true")
    parser.add_argument("--dataset-cache-dir", type=Path, default=dataset_loader.DEFAULT_CACHE_DIR)
    parser.add_argument("--review-every", type=int, default=20, help="Run batch critical review only after this many completed cases.")
    parser.add_argument("--target-accuracy", type=float, default=0.7)
    parser.add_argument("--prompt-style", choices=["standard", "strict_final", "deliberate"], default="standard")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--baseline-mode", choices=["auto", "none", "local"], default="none")
    parser.add_argument("--llm-provider", choices=["local", "server"], default=None)
    parser.add_argument("--workflow", choices=["auto", *lab.WORKFLOW_CHOICES], default="auto")
    parser.add_argument("--chatgpt-mode", choices=["auto", "manual", "mock", "local", "server"], default=None)
    parser.add_argument("--force-lenses", action="store_true")
    parser.add_argument("--propose-updates", action="store_true")
    parser.add_argument("--model", default=None)
    parser.add_argument("--server-url", default=None)
    parser.add_argument("--server-api-key", default=None)
    parser.add_argument("--server-model", default=None)
    parser.add_argument("--llm-timeout", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_DATASET_RUN_DIR)
    parser.add_argument("--fail-fast", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.llm_provider == "server" and not (args.server_url or os.getenv("SELF_EVAL_SERVER_URL") or os.getenv("LLM_SERVER_URL")) and not args.mock:
        raise SystemExit(
            "Server LLM provider selected but no URL was provided. "
            "Set --server-url, SELF_EVAL_SERVER_URL, or LLM_SERVER_URL."
        )
    return run_benchmark(args)


if __name__ == "__main__":
    raise SystemExit(main())
