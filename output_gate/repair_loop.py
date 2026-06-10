from __future__ import annotations

import json
from typing import Any, Callable

from output_gate.json_gate import GateResult, build_json_gate_retry_message, json_gate


RepairAgent = Callable[[str], str]


def repair_until_valid(
    raw_output: str,
    repair_agent: RepairAgent | None = None,
    max_agent_repairs: int = 0,
) -> dict[str, Any]:
    """
    Deterministic-first JSON repair loop.

    The gate tries code-based extraction/repair/validation first. An optional
    repair_agent is called only after deterministic repair fails.
    """

    current = raw_output
    history: list[dict[str, Any]] = []

    for attempt in range(max_agent_repairs + 1):
        result = json_gate(current)
        if result.ok:
            return {
                "ok": True,
                "data": result.data,
                "repaired_by_code": result.repaired_by_code,
                "attempt": attempt,
                "history": history,
            }

        history.append(_history_item(attempt, result, current))
        if repair_agent is None:
            break

        current = repair_agent(
            build_repair_prompt(
                bad_output=current,
                stage=result.stage,
                error=result.error,
            )
        )

    return {
        "ok": False,
        "error": "JSON_GATE_FAILED",
        "history": history,
        "last_output": _truncate(current, 2000),
    }


def build_repair_prompt(
    bad_output: str,
    stage: str,
    error: dict[str, Any] | None,
) -> str:
    return (
        "You are a strict JSON repair module.\n\n"
        "Fix the previous output according to the JSON gate error.\n\n"
        "Rules:\n"
        "- Return ONLY one valid JSON object.\n"
        "- No markdown.\n"
        "- No explanation.\n"
        "- Do not change the user's intended action unless the error requires it.\n"
        "- If the error is parse-related, fix syntax only.\n"
        "- If the error is schema-related, fix field names/types.\n"
        "- If the error is tool-args-related, match the expected tool args.\n"
        "- If the error is dry-run safety-related, choose a safe workspace-relative path or safe argv.\n\n"
        f"Failed stage:\n{stage}\n\n"
        f"Sandbox error:\n{json.dumps(error, ensure_ascii=False, default=str)}\n\n"
        f"Previous bad output:\n{bad_output}"
    )


def retry_message_for_gate(result: GateResult, raw_output: str) -> str:
    return build_json_gate_retry_message(result, raw_output)


def _history_item(attempt: int, result: GateResult, raw_output: str) -> dict[str, Any]:
    return {
        "attempt": attempt,
        "stage": result.stage,
        "error": result.error,
        "candidate": _truncate(result.candidate or "", 1000),
        "bad_output_preview": _truncate(raw_output, 1000),
    }


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}...<truncated {len(text) - max_chars} chars>"
