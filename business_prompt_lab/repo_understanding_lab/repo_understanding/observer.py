from __future__ import annotations

from typing import Any


STRONG_CLAIMS = ("root cause", "always", "never", "safe to change", "obviously", "broken")


def score_presence(value: list[Any], full: float, partial: float = 0.0) -> float:
    return full if value else partial


def observe_answer(context_pack: dict[str, Any], final_answer: str) -> dict[str, Any]:
    unsupported_claims = [
        claim for claim in STRONG_CLAIMS if claim in final_answer.lower() and not context_pack["graph_slice"]
    ]
    missed_evidence = []
    if context_pack["relevant_symbols"] and "Relevant Symbols" not in final_answer:
        missed_evidence.append("Final answer omitted relevant symbols section.")
    if context_pack["tests"] and "Tests" not in final_answer:
        missed_evidence.append("Final answer omitted tests section.")
    if context_pack["unknowns"] and "Unknowns" not in final_answer and "Caveats" not in final_answer:
        missed_evidence.append("Final answer omitted unknowns/caveats section.")

    scores = {
        "context_precision": score_presence(context_pack["relevant_files"], 0.78, 0.35),
        "context_recall": score_presence(context_pack["graph_slice"], 0.74, 0.42),
        "tool_efficiency": 0.86,
        "patch_minimality": None,
        "test_adequacy": score_presence(context_pack["tests"], 0.8, 0.45),
        "no_leap_score": 0.9 if not unsupported_claims else 0.48,
        "ledger_quality": 0.4,
    }
    numeric_scores = [value for value in scores.values() if isinstance(value, float)]
    scores["overall"] = round(sum(numeric_scores) / len(numeric_scores), 3)
    verdict = "answer_supported"
    if unsupported_claims:
        verdict = "rerun_retrieval"
    elif scores["overall"] < 0.65:
        verdict = "weak_context"

    return {
        "agent": "NoLeapGuardian",
        "scores": scores,
        "findings": missed_evidence,
        "unsupported_claims": unsupported_claims,
        "missed_evidence": missed_evidence,
        "recommended_next_flow": context_pack["task"]["intent"],
        "verdict": verdict,
    }

