import json
import os
import time
from typing import Any

from agents.tool_agent import tool_agent
from output_gate import JsonGateError, build_json_gate_retry_message, parse_json_action
from tools.event_log import EventLogger
from core.capabilities import call_tool
from core.schemas import CapabilityResult, capability_data, capability_get, capability_metadata


CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".sh",
    ".ps1",
}

VALIDATION_TOOLS = {
    "python.run_python",
    "python.python_probe",
    "lint_test.lint_compile",
    "lint_test.lint_ruff_check",
    "lint_test.lint_ruff_format_check",
    "lint_test.test_python_file",
    "lint_test.test_smoke_suite",
}


def _local_capability_failure(tool_name: str, error: str, data: dict[str, Any]) -> dict[str, Any]:
    payload = dict(data)
    payload.setdefault("tool", tool_name)
    return CapabilityResult(
        ok=False,
        capability=tool_name,
        feature=None,
        data=payload,
        error=error,
        metadata={"source": "orchestrator"},
    ).as_dict()


def parse_json(text: str) -> dict:
    """
    Try to parse a JSON object from the model output.
    Fenced JSON and surrounding text are tolerated as a recovery path.
    """
    return parse_json_action(text)


def _json_retry_message(error: Exception, agent_output: str) -> str:
    if isinstance(error, JsonGateError):
        return build_json_gate_retry_message(error.result, agent_output)

    return (
        "You returned invalid JSON, so the orchestrator could not read it.\n"
        "Return exactly one valid JSON object.\n"
        "No markdown. No explanation. Do not use ```json.\n\n"
        "Valid format when using a tool:\n"
        "{\n"
        '  "action": "tool",\n'
        '  "tool": "tool_name",\n'
        '  "args": {}\n'
        "}\n\n"
        "Valid format when the task is complete:\n"
        "{\n"
        '  "action": "final",\n'
        '  "message": "response text"\n'
        "}\n\n"
        f"Parse error: {str(error)}\n\n"
        f"Your invalid output was:\n{agent_output}"
    )


def _invalid_action_retry_message() -> str:
    return (
        "Your JSON parsed successfully, but the action is invalid.\n"
        "The action must be exactly 'tool' or 'final'.\n"
        "Return corrected JSON only."
    )


def _tool_call_key(tool_name: str, args: dict[str, Any]) -> str:
    return json.dumps(
        {
            "tool": tool_name,
            "args": args,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _coerce_args(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    raise ValueError("Tool args must be a JSON object.")


def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head
    return (
        text[:head]
        + f"\n...[truncated {len(text) - max_chars} chars]...\n"
        + text[-tail:]
    )


def _tail_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"[tail {max_chars} of {len(text)} chars]\n{text[-max_chars:]}"


def _compact_list(items: list[Any], limit: int = 5) -> dict[str, Any]:
    return {
        "count": len(items),
        "items": items[:limit],
        "truncated": len(items) > limit,
    }


def _compact_dict(items: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    selected = list(items.items())[:limit]
    return {
        "count": len(items),
        "items": dict(selected),
        "truncated": len(items) > limit,
    }


def _condense_tool_result(tool_result: dict[str, Any]) -> dict[str, Any]:
    """
    Keep enough evidence for the next agent step without feeding huge outputs
    back into the prompt. Full results still stay in the event log.
    """
    max_chars = int(os.getenv("ORCH_MAX_OBSERVATION_CHARS", "6000"))
    data = capability_data(tool_result)
    result_metadata = capability_metadata(tool_result)
    condensed: dict[str, Any] = {
        "ok": tool_result.get("ok"),
        "capability": tool_result.get("capability"),
        "feature": tool_result.get("feature"),
        "error": tool_result.get("error"),
    }
    if result_metadata:
        condensed["metadata"] = _compact_dict(result_metadata)

    keep_keys = {
        "ok",
        "server",
        "tool",
        "requested_tool",
        "error",
        "policy_blocked",
        "policy_code",
        "schema_error",
        "duration_seconds",
        "path",
        "url",
        "final_url",
        "status",
        "title",
        "returncode",
        "truncated",
        "command_metadata",
        "tool_metadata",
        "blocked",
        "failure_class",
        "stuck",
        "count",
        "total",
        "files_count",
        "symbols_count",
        "imports_count",
        "checked_files",
        "dependency_failure",
    }

    for key in keep_keys:
        if key in data:
            condensed[key] = data[key]

    for key in ("stdout", "stderr"):
        value = data.get(key)
        if isinstance(value, str):
            condensed[key] = _tail_text(value, max_chars // 3)

    for key in ("text", "content"):
        value = data.get(key)
        if isinstance(value, str):
            condensed[key] = _truncate_text(value, max_chars // 2)
        elif isinstance(value, list):
            condensed[key] = _compact_list(value)

    for key in (
        "results",
        "hits",
        "entries",
        "items",
        "symbols",
        "imports",
        "references",
        "matches",
        "issues",
        "comments",
        "notes",
        "failures",
    ):
        value = data.get(key)
        if isinstance(value, list):
            condensed[key] = _compact_list(value)

    for key in ("graph", "by_status", "by_kind"):
        value = data.get(key)
        if isinstance(value, dict):
            condensed[key] = _compact_dict(value)

    entry = data.get("entry")
    if isinstance(entry, dict):
        condensed["entry"] = {
            item_key: entry.get(item_key)
            for item_key in ("id", "timestamp", "entry_type", "title", "tags")
            if item_key in entry
        }

    if json.dumps(condensed, ensure_ascii=False, default=str) != json.dumps(tool_result, ensure_ascii=False, default=str):
        condensed["condensed"] = True

    return condensed


def _path_suffix(raw_path: Any) -> str:
    if not isinstance(raw_path, str):
        return ""
    return os.path.splitext(raw_path.lower())[1]


def _is_code_change_tool(tool_name: str, args: dict[str, Any]) -> bool:
    if tool_name in {
        "filesystem.write_file",
        "filesystem.edit_file",
        "file_editor.file_editor_create",
        "file_editor.file_editor_str_replace",
        "file_editor.file_editor_insert",
    }:
        return _path_suffix(args.get("path")) in CODE_EXTENSIONS
    return False


def _is_validation_tool(tool_name: str, args: dict[str, Any]) -> bool:
    if tool_name in VALIDATION_TOOLS:
        return True
    if tool_name == "terminal.terminal_run":
        argv = args.get("argv") or []
        if isinstance(argv, list):
            joined = " ".join(str(item) for item in argv)
            return any(token in joined for token in ("py_compile", "pytest", "run_all_cases.py", "main.py"))
    return False


def _validation_passed(tool_result: dict[str, Any]) -> bool:
    if not tool_result.get("ok"):
        return False
    returncode = capability_get(tool_result, "returncode")
    return returncode in (None, 0)


def _final_reports_blocker(message: Any) -> bool:
    text = str(message).lower()
    return any(
        token in text
        for token in (
            "blocker",
            "dependency failure",
            "environment/tool failure",
            "cannot validate",
            "khong the validate",
            "bi chan",
        )
    )


def run_orchestrator(
    user_task: str,
    max_steps: int = 80,
    max_parse_errors: int = 3,
    max_same_tool_calls: int | None = None,
) -> Any:
    """
    Main orchestration loop:
    User -> Agent -> Tool -> Agent -> Final.
    """
    if max_same_tool_calls is None:
        max_same_tool_calls = int(os.getenv("ORCH_MAX_SAME_TOOL_CALLS", "3"))

    event_logger = EventLogger()
    metrics: dict[str, Any] = {
        "steps": 0,
        "llm_calls": 0,
        "parse_errors": 0,
        "invalid_actions": 0,
        "tool_calls": 0,
        "tool_failures": 0,
        "policy_blocks": 0,
        "repeated_tool_failures": 0,
        "stuck_events": 0,
        "code_changes": 0,
        "validations": 0,
        "finish_gate_blocks": 0,
        "condensed_observations": 0,
    }

    print(f"RUN ID: {event_logger.run_id}")
    if event_logger.enabled:
        print(f"EVENT LOG: {event_logger.events_path}")

    def finish(status: str, message: Any) -> Any:
        metrics["status"] = status
        event_logger.emit(
            "StateEvent",
            status="run_finished",
            result_status=status,
            metrics=metrics,
            message=message,
        )
        event_logger.write_summary(
            status=status,
            metrics=metrics,
            final_message=message,
        )
        return message

    messages = [
        {
            "role": "user",
            "content": user_task,
        }
    ]
    parse_error_count = 0
    failed_tool_call_count: dict[str, int] = {}
    seen_tool_call_count: dict[str, int] = {}
    pending_code_validation = False
    last_code_change: dict[str, Any] | None = None
    last_validation_result: dict[str, Any] | None = None

    event_logger.emit(
        "StateEvent",
        status="run_started",
        max_steps=max_steps,
        max_parse_errors=max_parse_errors,
        max_same_tool_calls=max_same_tool_calls,
    )
    event_logger.emit("MessageEvent", role="user", content=user_task)

    for step in range(max_steps):
        metrics["steps"] = step + 1
        print(f"\n--- STEP {step + 1} ---")
        event_logger.emit("StateEvent", status="step_started", step=step + 1)

        try:
            llm_started = time.monotonic()
            agent_output = tool_agent(messages)
            llm_duration = round(time.monotonic() - llm_started, 3)
            metrics["llm_calls"] += 1
        except Exception as exc:
            return finish("llm_error", f"Agent/LLM call failed: {exc}")

        print("AGENT RAW OUTPUT:")
        print(agent_output)
        event_logger.emit(
            "MessageEvent",
            role="assistant",
            content=agent_output,
            step=step + 1,
            duration_seconds=llm_duration,
            raw=True,
        )

        try:
            action = parse_json(agent_output)
            parse_error_count = 0
        except Exception as exc:
            parse_error_count += 1
            metrics["parse_errors"] += 1

            print("JSON PARSE ERROR:")
            print(exc)
            gate_stage = exc.result.stage if isinstance(exc, JsonGateError) else "parse"
            event_logger.emit(
                "StateEvent",
                status="json_gate_error",
                step=step + 1,
                stage=gate_stage,
                error=str(exc),
                parse_error_count=parse_error_count,
            )

            if parse_error_count >= max_parse_errors:
                return finish(
                    "invalid_json",
                    f"Agent returned invalid JSON too many times. Last error: {exc}",
                )

            messages.append({
                "role": "user",
                "content": _json_retry_message(exc, agent_output),
            })
            continue

        event_logger.emit(
            "StateEvent",
            status="react_observe",
            step=step + 1,
            messages=len(messages),
            pending_code_validation=pending_code_validation,
        )

        if action.get("action") == "final":
            final_message = action.get("message", "")
            enforce_finish_gate = os.getenv("ORCH_ENFORCE_FINISH_GATE", "1") != "0"
            if enforce_finish_gate and pending_code_validation:
                if _final_reports_blocker(final_message):
                    event_logger.emit(
                        "StateEvent",
                        status="finish_gate_blocker_reported",
                        step=step + 1,
                        last_code_change=last_code_change,
                        last_validation_result=last_validation_result,
                    )
                    event_logger.emit(
                        "ActionEvent",
                        action="final",
                        step=step + 1,
                        message=final_message,
                    )
                    return finish("blocked", final_message)

                metrics["finish_gate_blocks"] += 1
                event_logger.emit(
                    "StateEvent",
                    status="finish_gate_blocked",
                    step=step + 1,
                    last_code_change=last_code_change,
                    last_validation_result=last_validation_result,
                )
                messages.append({
                    "role": "assistant",
                    "content": agent_output,
                })
                messages.append({
                    "role": "user",
                    "content": (
                        "FINISH GATE BLOCKED.\n"
                        "You changed code after the last passing validation, "
                        "or the latest validation failed.\n"
                        "Run the narrowest relevant validation now. If you "
                        "cannot validate or fix the failure, return final JSON "
                        "with a clear BLOCKER/dependency failure explanation."
                    ),
                })
                continue

            event_logger.emit(
                "ActionEvent",
                action="final",
                step=step + 1,
                message=final_message,
            )
            return finish("completed", final_message)

        if action.get("action") == "tool":
            tool_name = action.get("tool")
            try:
                args = _coerce_args(action.get("args", {}))
            except Exception as exc:
                metrics["invalid_actions"] += 1
                event_logger.emit(
                    "StateEvent",
                    status="invalid_action",
                    step=step + 1,
                    error=str(exc),
                    action=action,
                )
                messages.append({
                    "role": "user",
                    "content": f"{_invalid_action_retry_message()}\n\n{exc}",
                })
                continue

            if not isinstance(tool_name, str) or not tool_name.strip():
                metrics["invalid_actions"] += 1
                event_logger.emit(
                    "StateEvent",
                    status="invalid_action",
                    step=step + 1,
                    error="Tool action must include a non-empty string tool name.",
                    action=action,
                )
                messages.append({
                    "role": "user",
                    "content": _invalid_action_retry_message(),
                })
                continue

            print(f"CALL TOOL: {tool_name}")
            print(f"ARGS: {args}")
            event_logger.emit(
                "ActionEvent",
                action="tool",
                step=step + 1,
                tool=tool_name,
                args=args,
                plan=action.get("plan"),
            )

            tool_call_key = _tool_call_key(tool_name, args)
            seen_tool_call_count[tool_call_key] = (
                seen_tool_call_count.get(tool_call_key, 0) + 1
            )

            if seen_tool_call_count[tool_call_key] > max_same_tool_calls:
                metrics["stuck_events"] += 1
                error = (
                    "The exact same tool call repeated more than "
                    f"{max_same_tool_calls} times. The orchestrator blocked "
                    "another retry to prevent a loop."
                )
                tool_result = _local_capability_failure(
                    tool_name,
                    error,
                    {"args": args, "stuck": True, "failure_class": "agent_stuck"},
                )
            else:
                metrics["tool_calls"] += 1
                tool_started = time.monotonic()
                tool_result = call_tool(tool_name, args)
                tool_result.setdefault("metadata", {})["duration_seconds"] = round(time.monotonic() - tool_started, 3)

            if capability_get(tool_result, "policy_blocked"):
                metrics["policy_blocks"] += 1

            if not tool_result.get("ok", True):
                metrics["tool_failures"] += 1

            if _is_code_change_tool(tool_name, args):
                metrics["code_changes"] += 1
                pending_code_validation = True
                last_code_change = {
                    "step": step + 1,
                    "tool": tool_name,
                    "path": args.get("path"),
                }

            if _is_validation_tool(tool_name, args):
                metrics["validations"] += 1
                last_validation_result = {
                    "step": step + 1,
                    "tool": tool_name,
                    "ok": tool_result.get("ok"),
                    "returncode": capability_get(tool_result, "returncode"),
                    "error": tool_result.get("error"),
                }
                if pending_code_validation and _validation_passed(tool_result):
                    pending_code_validation = False

            print("TOOL RESULT:")
            print(tool_result)
            event_logger.emit(
                "ObservationEvent",
                step=step + 1,
                tool=tool_name,
                args=args,
                result=tool_result,
            )

            condensed_tool_result = _condense_tool_result(tool_result)
            if condensed_tool_result.get("condensed"):
                metrics["condensed_observations"] += 1
            event_logger.emit(
                "StateEvent",
                status="react_update_context",
                step=step + 1,
                tool=tool_name,
                condensed=bool(condensed_tool_result.get("condensed")),
                pending_code_validation=pending_code_validation,
            )

            if not tool_result.get("ok", True):
                failed_tool_call_count[tool_call_key] = (
                    failed_tool_call_count.get(tool_call_key, 0) + 1
                )

                if failed_tool_call_count[tool_call_key] >= 2:
                    metrics["repeated_tool_failures"] += 1
                    event_logger.emit(
                        "StateEvent",
                        status="repeated_tool_failure",
                        step=step + 1,
                        tool=tool_name,
                        args=args,
                        result=tool_result,
                    )
                    messages.append({
                        "role": "assistant",
                        "content": agent_output,
                    })

                    messages.append({
                        "role": "user",
                        "content": (
                            "The exact same tool call failed twice.\n"
                            "Do not call the same tool with the same args again.\n"
                            "Return a final JSON now.\n"
                            "Explain that this is an environment/tool failure, "
                            "not a code logic failure.\n\n"
                            f"Failed tool: {tool_name}\n"
                            f"Args: {json.dumps(args, ensure_ascii=False)}\n"
                            f"Tool result: {json.dumps(tool_result, ensure_ascii=False)}"
                        ),
                    })
                    continue

            messages.append({
                "role": "assistant",
                "content": agent_output,
            })

            messages.append({
                "role": "user",
                "content": json.dumps({
                    "tool_result": condensed_tool_result,
                }, ensure_ascii=False),
            })
            continue

        metrics["invalid_actions"] += 1
        event_logger.emit(
            "StateEvent",
            status="invalid_action",
            step=step + 1,
            action=action,
        )
        messages.append({
            "role": "user",
            "content": _invalid_action_retry_message(),
        })
        continue

    return finish("max_steps", "Agent exceeded the maximum number of allowed steps.")
