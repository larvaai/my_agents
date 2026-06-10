from __future__ import annotations

from typing import Any

from agents.lenses.base_lens import LensResult, LensSpec, lens_results_to_dict, run_prompt_lens
from tools.tool_registry import call_tool


VERSION = "v0.5"


def safe_tool_call(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = call_tool(tool, args)
        if isinstance(result, dict):
            return result
        return {"ok": False, "tool": tool, "error": "Tool returned non-dict result.", "raw": str(result)}
    except Exception as exc:
        return {"ok": False, "tool": tool, "error": str(exc)}


def run_lenses(
    *,
    lenses: tuple[LensSpec, ...],
    task: str,
    context: dict[str, Any],
    deterministic: dict[str, dict[str, Any]],
    use_llm: bool = False,
    model: str | None = None,
) -> list[LensResult]:
    payload = {"task": task, "context": context, "version": VERSION}
    results: list[LensResult] = []
    for spec in lenses:
        if use_llm:
            result = run_prompt_lens(spec.name, spec.to_prompt_block(), payload, model=model)
            if result.ok:
                results.append(result)
                continue

        data = dict(deterministic.get(spec.name, {"lens": spec.name, "notes": [], "confidence": "medium"}))
        data.setdefault("lens", spec.name)
        results.append(LensResult(lens=spec.name, ok=True, data=data))
    return results


def compact_history(history: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    compacted: list[dict[str, Any]] = []
    for item in history or []:
        result = item.get("result", {}) if isinstance(item, dict) else {}
        synthesis = result.get("synthesis", {}) if isinstance(result, dict) else {}
        route = result.get("route", {}) if isinstance(result, dict) else {}
        compacted.append(
            {
                "cycle": item.get("cycle") if isinstance(item, dict) else None,
                "agent": item.get("agent") if isinstance(item, dict) else None,
                "decision": synthesis.get("decision") if isinstance(synthesis, dict) else None,
                "next_agent": route.get("next_agent") if isinstance(route, dict) else None,
            }
        )
    return compacted


def changed_files_from_code_result(code_result: dict[str, Any] | None) -> list[str]:
    code_result = code_result or {}
    files: list[str] = []
    synthesis = code_result.get("synthesis", {})
    if isinstance(synthesis, dict):
        for path in synthesis.get("files_to_modify", []):
            if isinstance(path, str) and path not in files:
                files.append(path)
    executor_plan = code_result.get("executor_plan", {})
    if isinstance(executor_plan, dict):
        for item in executor_plan.get("files_to_write", []):
            if isinstance(item, dict):
                path = item.get("path")
                if isinstance(path, str) and path not in files:
                    files.append(path)
    return files


def test_commands_from_test_result(test_result: dict[str, Any] | None) -> list[dict[str, Any]]:
    test_result = test_result or {}
    synthesis = test_result.get("synthesis", {})
    if isinstance(synthesis, dict):
        tests = synthesis.get("tests_to_run", [])
        if isinstance(tests, list):
            return [item for item in tests if isinstance(item, dict)]
    return []


def execution_ok(result: dict[str, Any] | None) -> bool:
    if not isinstance(result, dict):
        return False
    execution = result.get("execution", {})
    return isinstance(execution, dict) and execution.get("ok") is True


def append_ledger(
    *,
    agent: str,
    title: str,
    task: str,
    synthesis: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = {
        "agent": agent,
        "version": VERSION,
        "task": task,
        "decision": synthesis.get("decision"),
        "summary": synthesis.get("summary") or synthesis.get("architecture_summary") or synthesis.get("final_message"),
    }
    if extra:
        data.update(extra)
    return safe_tool_call(
        "ledger.ledger_append",
        {
            "entry_type": "agent_run",
            "title": title,
            "data": data,
            "tags": ["v0.5", agent],
        },
    )


def route(next_agent: str, reason: str) -> dict[str, str]:
    return {"next_agent": next_agent, "reason": reason}


def result_payload(
    *,
    agent: str,
    lens_results: list[LensResult],
    synthesis: dict[str, Any],
    records: dict[str, Any],
    next_agent: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "agent": agent,
        "version": VERSION,
        "lens_results": lens_results_to_dict(lens_results),
        "synthesis": synthesis,
        "records": records,
        "route": route(next_agent, reason),
    }
