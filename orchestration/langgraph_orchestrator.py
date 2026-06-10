from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Callable

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - exercised when dependency is absent
    END = "__end__"
    START = "__start__"
    StateGraph = None  # type: ignore[assignment]

from agents.role_agents import get_agent
from orchestration.agent_state import AgentName, AgentState
from output_gate import JsonGateError, build_json_gate_retry_message, parse_json_action
from tools.event_log import EventLogger
from tools.mcp_config import WORKSPACE_DIR
from tools.tool_registry import call_tool


PIPELINE: tuple[AgentName, ...] = (
    "research",
    "planner",
    "architect",
    "code",
    "test",
    "review",
    "ledger",
    "final",
)

MAX_TOOL_CONTEXT_CHARS = 6000
MAX_STATE_SNIPPET_CHARS = 1600
MAX_JSON_RETRIES_PER_ROLE = 3
STRICT_JSON_ROLES = {"code", "test", "final"}
ROLE_BUDGETS = {
    "research": 2,
    "planner": 3,
    "architect": 4,
    "code": 140,
    "test": 48,
    "review": 8,
    "ledger": 4,
    "final": 4,
}
SUBTASK_BUDGETS = {
    "code:create": 14,
    "code:repair": 20,
    "code:general": 12,
    "test:validate": 20,
    "review:general": 4,
}
VALIDATION_KEYWORDS = (
    "test",
    "validation",
    "validate",
    "run",
    "tao file",
    "chay",
    "kiem",
    "sua",
    "fix",
    "bug",
    "code",
    "implement",
    "langgraph_smoke_ok",
)


ROLE_GUIDANCE: dict[str, str] = {
    "research": (
        "Research scope:\n"
        "- Gather facts only when needed.\n"
        "- For a simple implementation smoke, do not call tools; return a short handoff.\n"
        "- Never create, edit, validate, or commit files."
    ),
    "planner": (
        "Planner scope:\n"
        "- Produce a short plan and validation intent.\n"
        "- Do not implement code and do not run tests.\n"
        "- If the task already names the target file and expected output, plan from that evidence."
    ),
    "architect": (
        "Architect scope:\n"
        "- Define boundaries, paths, and tool ownership.\n"
        "- Do not inspect the whole repository for a small named file task.\n"
        "- Do not create, edit, or validate files."
    ),
    "code": (
        "Code scope:\n"
        "- You are the Engineering Department and the only implementation role.\n"
        "- Use engineering lenses mentally: implementation, integration, defensive_coding, refactor_discipline, developer_experience.\n"
        "- Lens outputs are advisory; the Code Agent synthesizes them and then performs one concrete edit action.\n"
        "- Use file_editor tools for normal file changes; do not edit files through terminal.\n"
        "- Use filesystem.write_file only for short filesystem MCP smoke tests; use file_editor for generated code even if an old prompt says write_file.\n"
        "- For multi-file projects, create exactly one file per tool call, then continue as code until all required files exist.\n"
        "- The current state summary includes missing_files. Create the first missing file before touching existing files.\n"
        "- If missing_files is not empty and there is no last_failure, your next mutating file tool must target missing_files[0].\n"
        "- Do not patch or polish an earlier file before all required files exist; QA will find syntax/runtime problems after the first full pass.\n"
        "- Keep generated file content compact and complete. Avoid long banners, large comments, and over-explaining inside code.\n"
        "- For generated files over roughly 30 lines, prefer file_editor.file_editor_write_lines with a JSON lines array instead of one large multiline content string.\n"
        "- For file_editor.file_editor_write_lines, args.lines must contain one physical file line per item; never put the whole file in one string with \\n escapes.\n"
        "- Every args.lines item must be a double-quoted JSON string. Do not use Python-style single quotes as JSON string delimiters.\n"
        "- Keep quotes JSON-safe: use single quotes inside generated Python code where practical, for example \"NAME = 'Society Sim'\".\n"
        "- Avoid double quote characters and triple-quoted docstrings inside generated Python source lines unless they are escaped for JSON.\n"
        "- If a file would be long, implement the smallest passing version first; tests can drive later expansion.\n"
        "- JSON booleans must be lowercase true/false, never Python True/False.\n"
        "- When state contains last_failure, enter repair mode: patch the exact failing file with file_editor.file_editor_str_replace or file_editor.file_editor_insert.\n"
        "- In repair mode, do not rewrite the whole file; make one narrow hypothesis-driven patch and hand off to Test.\n"
        "- If you need more context in repair mode, view only the failing file around the traceback line once.\n"
        "- Do not run validation tools. When implementation is complete, hand off to Test.\n"
        "- Do not hand off to Test while required project files are missing.\n"
        "- After required files are recorded in files_modified, return a handoff JSON."
    ),
    "test": (
        "Test scope:\n"
        "- You are the QA Department / Test Council.\n"
        "- Use QA lenses mentally: logic, critical_thinking, experienced_qa, regression, purpose_alignment, then test_executor.\n"
        "- Only test_executor may run validation tools; other lenses are reasoning-only.\n"
        "- Run the narrowest validation for changed files.\n"
        "- Use lint_test.test_python_file for project test files and python.run_python for workspace Python scripts when requested.\n"
        "- If a test file is missing, return final with finish_reason=\"blocker\" and do not try to create files.\n"
        "- If tests_run already contains an ok validation with required stdout, return a handoff JSON."
    ),
    "review": (
        "Review scope:\n"
        "- You are the Senior Review Board.\n"
        "- Use review lenses mentally: senior_engineer, scope_diff, security_review, maintainability, release_risk.\n"
        "- Review evidence already in state first.\n"
        "- If files_modified contains the target file and tests_run has ok=true with LANGGRAPH_SMOKE_OK, "
        "approve without extra tool calls.\n"
        "- Do not edit files."
    ),
    "ledger": (
        "Ledger scope:\n"
        "- You are the Secretary / Audit / Operations Department.\n"
        "- Use ledger lenses mentally: historian, task_state, decision_record, auditor, incident_tracker.\n"
        "- A ledger note is optional for a smoke run.\n"
        "- If useful, write at most one concise ledger.ledger_append entry.\n"
        "- If the run evidence is already clear, return a handoff JSON without tools."
    ),
}


def parse_json(text: str) -> dict[str, Any]:
    """
    Parse and validate one JSON action from an LLM response.
    """
    return parse_json_action(text)


def _build_role_json_retry_message(role: str, exc: Exception, output: str) -> str:
    if isinstance(exc, JsonGateError):
        message = build_json_gate_retry_message(exc.result, output)
    else:
        message = (
            f"{role} returned invalid JSON. Return exactly one valid JSON object. "
            f"Parse error: {exc}\n"
            "Use JSON booleans true/false/null, not Python True/False/None. "
            "If this was a file write, make the file content shorter and fully close all quotes/braces. "
            "For Code Agent, create only the first missing file in a compact passing form."
        )

    if role == "code":
        message += (
            "\n\nCode Agent emergency retry rules:\n"
            "- Do not retry the same long payload.\n"
            "- Create or repair exactly one file in this response.\n"
            "- Keep the file compact enough for the first tests to run; expand only after QA failure evidence.\n"
            "- For file_editor.file_editor_write_lines, every lines item is a double-quoted JSON string.\n"
            "- Avoid double quote characters inside generated Python source lines; prefer single-quoted Python strings and dict keys.\n"
            "- Avoid triple-quoted docstrings in generated payloads; use comments until tests pass.\n"
            "- If a Python line truly needs a double quote, escape it as \\\" inside the JSON string.\n"
        )

    return message


def _require_langgraph() -> None:
    if StateGraph is None:
        raise RuntimeError(
            "LangGraph is not installed. Run: python -m pip install -r requirements.txt"
        )


def _append_message(state: AgentState, role: str, content: str) -> list[dict[str, str]]:
    messages = list(state.get("messages", []))
    messages.append({"role": role, "content": content})
    return messages


def _next_pipeline_role(role: str) -> AgentName:
    if role not in PIPELINE:
        return "final"
    index = PIPELINE.index(role)  # type: ignore[arg-type]
    if index + 1 >= len(PIPELINE):
        return "final"
    return PIPELINE[index + 1]


def _truncate(value: str, max_chars: int = MAX_STATE_SNIPPET_CHARS) -> str:
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}...<truncated {len(value) - max_chars} chars>"


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(
        char
        for char in normalized
        if unicodedata.category(char) != "Mn"
    )


def _normalize_project_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("workspace/"):
        normalized = normalized.removeprefix("workspace/")
    return normalized


def _extract_required_files(user_task: str) -> list[str]:
    scope_prefix = "society_sim/" if "society_sim/" in user_task or "society_sim\\" in user_task else ""
    seen: set[str] = set()
    files: list[str] = []
    for match in re.finditer(r"(?<![A-Za-z0-9_./\\-])([A-Za-z0-9_./\\-]+\.py)(?![A-Za-z0-9_./\\-])", user_task):
        path = _normalize_project_path(match.group(1))
        if scope_prefix and "/" not in path:
            path = f"{scope_prefix}{path}"
        if scope_prefix and not path.startswith(scope_prefix):
            continue
        if path == f"{scope_prefix}main.py" and "python main.py" in user_task:
            continue
        if path not in seen:
            seen.add(path)
            files.append(path)
    return files


def _known_existing_files(state: AgentState) -> set[str]:
    known = {
        _normalize_project_path(path)
        for path in state.get("files_modified", [])
        if isinstance(path, str)
    }

    tool_result = state.get("tool_result")
    if isinstance(tool_result, dict) and tool_result.get("ok"):
        path = tool_result.get("path")
        if isinstance(path, str):
            known.add(_normalize_project_path(path))
    return known


def _missing_required_files(state: AgentState) -> list[str]:
    required = [
        _normalize_project_path(path)
        for path in state.get("required_files", [])
        if isinstance(path, str)
    ]
    known = _known_existing_files(state)
    missing: list[str] = []
    for path in required:
        workspace_path = WORKSPACE_DIR / path
        if path in known or workspace_path.exists():
            continue
        missing.append(path)
    return missing


def _extract_failure_summary(tool_result: dict[str, Any]) -> dict[str, Any] | None:
    if tool_result.get("ok"):
        return None

    stderr = str(tool_result.get("stderr") or "")
    error = str(tool_result.get("error") or "")
    text = stderr or error
    if not text:
        return None

    frames = re.findall(r'File "([^"]+)", line (\d+), in ([^\n]+)', text)
    project_frame: tuple[str, str, str] | None = None
    workspace = str(WORKSPACE_DIR.resolve()).replace("\\", "/")
    for frame in frames:
        frame_path = frame[0].replace("\\", "/")
        if frame_path.startswith(workspace):
            project_frame = frame

    error_line = ""
    for line in reversed(text.strip().splitlines()):
        stripped = line.strip()
        if stripped:
            error_line = stripped
            break

    summary: dict[str, Any] = {
        "error": _truncate(error_line, 1000),
        "stderr_tail": _truncate("\n".join(text.strip().splitlines()[-12:]), 2000),
    }
    if project_frame is not None:
        path, line, function = project_frame
        try:
            rel_path = str(Path(path).resolve().relative_to(WORKSPACE_DIR.resolve()))
        except Exception:
            rel_path = path
        summary.update(
            {
                "file": _normalize_project_path(rel_path),
                "line": int(line),
                "function": function.strip(),
            }
        )
    return summary


def _failure_signature(failure: dict[str, Any] | None) -> str:
    if not failure:
        return "none"
    file_name = str(failure.get("file") or "unknown")
    line = str(failure.get("line") or "?")
    error = str(failure.get("error") or "error").split(":", 1)[0]
    return f"{file_name}:{line}:{error}"


def _compact_tool_result(tool_result: Any) -> Any:
    if not isinstance(tool_result, dict):
        return tool_result

    keys_to_keep = (
        "ok",
        "server",
        "tool",
        "requested_tool",
        "path",
        "error",
        "policy_blocked",
        "policy_code",
        "schema_error",
        "stuck",
        "returncode",
        "stdout",
        "stderr",
        "duration_seconds",
        "command",
        "chars_written",
        "replacements",
        "line",
        "files_count",
        "symbols_count",
        "imports_count",
        "truncated",
        "metadata",
        "tool_metadata",
    )
    compact = {
        key: tool_result[key]
        for key in keys_to_keep
        if key in tool_result
    }

    if "results" in tool_result and isinstance(tool_result["results"], list):
        compact["results"] = tool_result["results"][:5]
        compact["results_truncated"] = len(tool_result["results"]) > 5

    if "lines" in tool_result and isinstance(tool_result["lines"], list):
        compact["lines"] = tool_result["lines"][:80]
        compact["lines_truncated"] = len(tool_result["lines"]) > 80

    if "content" in tool_result and "content" not in compact:
        content = str(tool_result["content"])
        compact["content"] = _truncate(content, 1200)

    for key in ("stdout", "stderr", "error"):
        if isinstance(compact.get(key), str):
            compact[key] = _truncate(compact[key], 2000)

    rendered = json.dumps(compact, ensure_ascii=False, default=str)
    if len(rendered) > MAX_TOOL_CONTEXT_CHARS:
        compact["raw_result_truncated"] = True
        compact["raw_result_preview"] = _truncate(rendered, MAX_TOOL_CONTEXT_CHARS)
        for bulky_key in ("tool_metadata", "metadata", "results", "lines", "content"):
            compact.pop(bulky_key, None)

    return compact


def _state_brief(state: AgentState) -> str:
    tests = []
    for item in state.get("tests_run", [])[-5:]:
        if not isinstance(item, dict):
            continue
        tests.append(
            {
                "tool": item.get("tool"),
                "path": item.get("path") or item.get("args", {}).get("path"),
                "ok": item.get("ok") if "ok" in item else item.get("passed"),
                "stdout": _truncate(str(item.get("stdout", "")), 400),
                "error": _truncate(str(item.get("error", "")), 400),
            }
        )

    last_tool_result = state.get("tool_result")
    brief = {
        "plan": _truncate(str(state.get("plan", "")), 800),
        "required_files": state.get("required_files", []),
        "missing_files": _missing_required_files(state),
        "files_modified": state.get("files_modified", []),
        "tests_run": tests,
        "last_failure": state.get("last_failure"),
        "repair_attempts": state.get("repair_attempts", {}),
        "role_visits": state.get("role_visits", {}),
        "subtask_visits": {
            key: value
            for key, value in state.get("subtask_visits", {}).items()
            if value
        },
        "last_tool_result": _compact_tool_result(last_tool_result) if last_tool_result else None,
        "errors": state.get("errors", [])[-5:],
    }
    return json.dumps(brief, ensure_ascii=False, default=str)


def _role_instruction(role: str, state: AgentState) -> str:
    next_role = _next_pipeline_role(role)
    if role == "final":
        return (
            "LANGGRAPH NODE INSTRUCTION:\n"
            "You are the final node. Do not call tools.\n"
            "Return exactly one JSON final object for the user. Summarize evidence, "
            "tests, review, blockers, and changed files if any.\n"
            "If no passing validation exists in tests_run, finish_reason must be \"blocker\".\n"
            f"Current state summary: {_state_brief(state)}"
        )

    guidance = ROLE_GUIDANCE.get(role, "")
    return (
        "LANGGRAPH NODE INSTRUCTION:\n"
        f"You are running as the {role} node inside a LangGraph pipeline.\n"
        f"When your role step is done, return JSON final with finish_reason=\"handoff\"; "
        f"the graph will route to {next_role}.\n"
        "If you need evidence, return one JSON tool call using only your allowed tools.\n"
        "Do not pretend to be the final user-facing answer unless you are the final node.\n"
        "Return exactly one JSON object, with no markdown fences and no prose outside JSON.\n"
        "For handoff finals, keep message under 500 characters; no markdown tables, no code blocks, no directory trees.\n"
        "If implementation is needed and your role is not code, return a short handoff instead of calling edit tools.\n"
        f"{guidance}\n"
        f"Current state summary: {_state_brief(state)}\n"
    )


def _record_role_output(state: AgentState, role: str, action: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    outputs = {
        key: list(value)
        for key, value in state.get("role_outputs", {}).items()
    }
    outputs.setdefault(role, [])
    outputs[role].append(action)
    return outputs


def _synthetic_invalid_json_action(role: str, exc: Exception, next_role: str) -> dict[str, Any]:
    return {
        "action": "final",
        "finish_reason": "handoff",
        "message": (
            f"{role} returned invalid JSON too many times. "
            f"Routing to {next_role} with the parse error recorded."
        ),
        "error": str(exc),
    }


def _compact_action_for_log(action: dict[str, Any]) -> dict[str, Any]:
    compact = dict(action)
    args = compact.get("args")
    if isinstance(args, dict):
        compact["args"] = {
            key: _truncate(value, 600) if isinstance(value, str) else value
            for key, value in args.items()
        }
    message = compact.get("message")
    if isinstance(message, str):
        compact["message"] = _truncate(message, 1000)
    return compact


def _extract_simple_file_create_action(state: AgentState) -> dict[str, Any] | None:
    task = state.get("user_task", "")
    folded = _fold_text(task)
    if not any(marker in folded for marker in ("tao file", "create file", "write file")):
        return None

    path_match = re.search(
        r"(?:file|path)\s+[`\"]?([A-Za-z0-9_./\\-]+\.py)",
        task,
        flags=re.IGNORECASE,
    )
    if path_match is None:
        path_match = re.search(r"`([^`]+\.py)`", task, flags=re.IGNORECASE)
    if path_match is None:
        path_match = re.search(r"([A-Za-z0-9_./\\-]+\.py)", task, flags=re.IGNORECASE)
    if path_match is None:
        return None

    path = path_match.group(1).replace("\\", "/").strip()
    if path.startswith("workspace/"):
        path = path.removeprefix("workspace/")
    path = _normalize_project_path(path)

    content = _extract_inline_file_content(task)
    if not content:
        return None

    if not content.endswith("\n"):
        content += "\n"

    return {
        "action": "tool",
        "tool": "file_editor.file_editor_create",
        "args": {
            "path": path,
            "content": content,
            "overwrite": True,
        },
        "reason": "simple_file_create_rescue",
    }


def _extract_inline_file_content(task: str) -> str | None:
    fence = re.search(r"```(?:python)?\s*(.*?)```", task, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        return fence.group(1).strip()

    lines = task.splitlines()
    for index, line in enumerate(lines):
        folded = _fold_text(line)
        if "noi dung" not in folded and "content" not in folded:
            continue

        inline = line.split(":", 1)[1].strip() if ":" in line else ""
        if inline:
            return inline.strip("`")

        collected: list[str] = []
        for next_line in lines[index + 1:]:
            stripped = next_line.strip()
            if not stripped and collected:
                break
            if collected and re.match(r"^\d+\.", stripped):
                break
            if collected and stripped.lower().startswith(("test agent", "review agent", "ledger agent", "final")):
                break
            if stripped:
                collected.append(next_line.strip("`"))
        if collected:
            return "\n".join(collected).strip()

    return None


def _extract_files(action: dict[str, Any], state: AgentState) -> list[str]:
    files = list(state.get("files_modified", []))
    payload = action.get("files_modified") or action.get("changed_files") or []
    if isinstance(payload, str):
        payload = [payload]
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, str):
                normalized = _normalize_project_path(item)
                if normalized not in files:
                    files.append(normalized)
    return files


def _extract_tests(action: dict[str, Any], state: AgentState) -> list[dict[str, Any]]:
    tests = list(state.get("tests_run", []))
    payload = action.get("tests_run") or action.get("validation") or []
    if isinstance(payload, dict):
        payload = [payload]
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                tests.append(item)
    return tests


def _is_file_change_tool(tool_name: str) -> bool:
    return tool_name in {
        "file_editor.file_editor_create",
        "file_editor.file_editor_write_lines",
        "file_editor.file_editor_str_replace",
        "file_editor.file_editor_insert",
        "file_editor_create",
        "file_editor_write_lines",
        "file_editor_str_replace",
        "file_editor_insert",
        "filesystem.write_file",
        "filesystem.edit_file",
        "write_file",
        "edit_file",
    }


def _is_whole_file_write_tool(tool_name: str) -> bool:
    return tool_name in {
        "file_editor.file_editor_create",
        "file_editor.file_editor_write_lines",
        "file_editor_create",
        "file_editor_write_lines",
        "filesystem.write_file",
        "write_file",
    }


def _should_block_whole_file_repair(state: AgentState, tool_name: str, tool_args: dict[str, Any]) -> bool:
    failure = state.get("last_failure")
    if not isinstance(failure, dict) or not failure:
        return False
    if not _is_whole_file_write_tool(tool_name):
        return False

    target = tool_args.get("path")
    failing_file = failure.get("file")
    if not isinstance(target, str) or not isinstance(failing_file, str):
        return False

    normalized_target = _normalize_project_path(target)
    normalized_failure = _normalize_project_path(failing_file)
    if normalized_target != normalized_failure:
        return False

    return (WORKSPACE_DIR / normalized_target).exists()


def _is_validation_tool(tool_name: str) -> bool:
    return (
        tool_name.startswith("lint_test.")
        or tool_name.startswith("python.")
        or tool_name in {
            "lint_compile",
            "lint_ruff_check",
            "lint_ruff_format_check",
            "test_python_file",
            "test_smoke_suite",
            "run_python",
        }
    )


def _record_tool_files(tool_name: str, tool_args: dict[str, Any], tool_result: dict[str, Any], state: AgentState) -> list[str]:
    files = list(state.get("files_modified", []))
    if not tool_result.get("ok") or not _is_file_change_tool(tool_name):
        return files

    path = tool_result.get("path") or tool_args.get("path")
    if isinstance(path, str):
        normalized = _normalize_project_path(path)
        if normalized not in files:
            files.append(normalized)
    return files


def _record_tool_tests(tool_name: str, tool_args: dict[str, Any], tool_result: dict[str, Any], state: AgentState) -> list[dict[str, Any]]:
    tests = list(state.get("tests_run", []))
    metadata = tool_result.get("metadata") or tool_result.get("tool_metadata") or {}
    is_validation = bool(isinstance(metadata, dict) and metadata.get("validation"))
    if not (_is_validation_tool(tool_name) or is_validation):
        return tests

    tests.append(
        {
            "tool": tool_name,
            "args": tool_args,
            "path": tool_result.get("path") or tool_args.get("path"),
            "ok": bool(tool_result.get("ok")),
            "returncode": tool_result.get("returncode"),
            "stdout": _truncate(str(tool_result.get("stdout", "")), 2000),
            "stderr": _truncate(str(tool_result.get("stderr", "")), 2000),
            "error": tool_result.get("error"),
            "duration_seconds": tool_result.get("duration_seconds"),
        }
    )
    return tests


def _requires_validation(state: AgentState) -> bool:
    if state.get("files_modified"):
        return True

    task = _fold_text(state.get("user_task", ""))
    return any(keyword in task for keyword in VALIDATION_KEYWORDS)


def _has_passing_validation(state: AgentState) -> bool:
    tests = state.get("tests_run", [])
    if not tests:
        return False

    task = _fold_text(state.get("user_task", ""))
    requires_langgraph_token = "langgraph_smoke_ok" in task
    requires_society_token = "society_sim_tests_ok" in task

    for item in tests:
        if not isinstance(item, dict) or not item.get("ok"):
            continue
        stdout = str(item.get("stdout", ""))
        if requires_langgraph_token and "LANGGRAPH_SMOKE_OK" not in stdout:
            continue
        if requires_society_token and "SOCIETY_SIM_TESTS_OK" not in stdout:
            continue
        if "LANGGRAPH_SMOKE_OK" in stdout or "SOCIETY_SIM_TESTS_OK" in stdout or not (requires_langgraph_token or requires_society_token):
            return True

    return False


def _has_run_path(state: AgentState, path: str) -> bool:
    normalized = _normalize_project_path(path)
    for item in state.get("tests_run", []):
        if not isinstance(item, dict):
            continue
        if item.get("ok") is not True:
            continue
        item_path = item.get("path") or item.get("args", {}).get("path")
        if isinstance(item_path, str) and _normalize_project_path(item_path).endswith(normalized):
            return True
    return False


def _requires_cli_demo(state: AgentState) -> bool:
    task = _fold_text(state.get("user_task", ""))
    return "cli_demo.py" in task or "cli_demo" in task


def _validation_complete(state: AgentState) -> bool:
    if not _has_passing_validation(state):
        return False
    if _requires_cli_demo(state) and not _has_run_path(state, "society_sim/cli_demo.py"):
        return False
    return True


def _forced_test_action(state: AgentState) -> dict[str, Any] | None:
    if (
        _has_passing_validation(state)
        and _requires_cli_demo(state)
        and not _has_run_path(state, "society_sim/cli_demo.py")
    ):
        return {
            "action": "tool",
            "tool": "python.run_python",
            "args": {
                "path": "society_sim/cli_demo.py",
                "timeout": 30,
            },
            "reason": "required_cli_demo_after_tests",
        }

    if _has_passing_validation(state):
        return None

    required = [
        _normalize_project_path(path)
        for path in state.get("required_files", [])
        if isinstance(path, str)
    ]

    for path in required:
        filename = path.rsplit("/", 1)[-1]
        if not (filename.startswith("test_") and filename.endswith(".py")):
            continue

        last_tool_result = state.get("tool_result")
        if isinstance(last_tool_result, dict):
            last_path = last_tool_result.get("path")
            if (
                isinstance(last_path, str)
                and _normalize_project_path(last_path).endswith(path)
                and not last_tool_result.get("ok")
            ):
                return None

        if filename.startswith("test_") and filename.endswith(".py"):
            return {
                "action": "tool",
                "tool": "python.run_python",
                "args": {
                    "path": path,
                    "timeout": 30,
                },
                "reason": "required_test_file",
            }

    return None


def _finish_gate_message(state: AgentState) -> str:
    evidence = {
        "finish_reason": "blocker",
        "reason": "Validation is required, but no passing validation evidence is recorded in tests_run.",
        "files_modified": state.get("files_modified", []),
        "tests_run": state.get("tests_run", []),
        "missing_files": _missing_required_files(state),
        "last_failure": state.get("last_failure"),
        "repair_attempts": state.get("repair_attempts", {}),
        "errors": state.get("errors", [])[-5:],
        "last_tool_result": _compact_tool_result(state.get("tool_result")),
    }
    return (
        "Blocked by finish gate. The graph cannot report completion until a real "
        "tool validation passes. Evidence:\n"
        f"{json.dumps(evidence, ensure_ascii=False, indent=2, default=str)}"
    )


def _build_validated_final_message(state: AgentState) -> str:
    files = [
        _normalize_project_path(path)
        for path in state.get("required_files", [])
        if isinstance(path, str)
    ]
    if not files:
        files = [
            _normalize_project_path(path)
            for path in state.get("files_modified", [])
            if isinstance(path, str)
        ]

    tests = [
        item
        for item in state.get("tests_run", [])
        if isinstance(item, dict)
    ]
    test_stdout = ""
    demo_status = "not requested"
    for item in tests:
        path = _normalize_project_path(str(item.get("path") or item.get("args", {}).get("path") or ""))
        stdout = str(item.get("stdout", ""))
        if path.endswith("test_society_sim.py") and "SOCIETY_SIM_TESTS_OK" in stdout:
            test_stdout = stdout
        if path.endswith("cli_demo.py"):
            demo_status = "ran successfully" if item.get("ok") else "failed"

    lines = [
        "=== SOCIETY SIM PROJECT COMPLETE ===",
        "",
        f"Files covered: {', '.join(files) if files else 'no file list recorded'}",
        "",
        "Validation:",
        "- Required Python test passed with SOCIETY_SIM_TESTS_OK.",
        f"- cli_demo.py: {demo_status}.",
    ]
    if test_stdout:
        lines.extend(["", "Test stdout:", test_stdout.strip()])
    lines.extend(
        [
            "",
            "Current limits:",
            "- Terminal/std-lib simulation only.",
            "- Small fixed world and simple rule-based behavior.",
            "- Economy, events, and relationships are intentionally lightweight.",
        ]
    )
    return "\n".join(lines)


def _current_subtask_key(role: str, state: AgentState) -> str:
    if role == "code":
        failure = state.get("last_failure")
        if isinstance(failure, dict) and failure:
            return f"code:repair:{_failure_signature(failure)}"
        missing = _missing_required_files(state)
        if missing:
            return f"code:create:{missing[0]}"
        return "code:general"

    if role == "test":
        required = [
            _normalize_project_path(path)
            for path in state.get("required_files", [])
            if isinstance(path, str)
        ]
        for path in required:
            filename = path.rsplit("/", 1)[-1]
            if filename.startswith("test_") and filename.endswith(".py"):
                return f"test:validate:{path}"
        return "test:validate"

    if role == "review":
        return "review:general"

    return f"{role}:general"


def _should_fast_handoff_to_code(role: str, state: AgentState) -> bool:
    if role not in {"research", "planner", "architect"}:
        return False
    required = [
        _normalize_project_path(path)
        for path in state.get("required_files", [])
        if isinstance(path, str)
    ]
    return any(path.endswith(".py") for path in required)


def _fast_handoff_action(role: str) -> dict[str, Any]:
    return {
        "action": "final",
        "finish_reason": "handoff",
        "message": (
            f"{role} handoff: Python implementation task detected. "
            "Engineering owns file edits; continue to the next role."
        ),
    }


def _subtask_budget_for(key: str) -> int:
    for prefix, budget in SUBTASK_BUDGETS.items():
        if key.startswith(prefix):
            return budget
    return 6


def _budget_blocker(role: str, role_visits: dict[str, int], subtask_key: str, subtask_visits: dict[str, int]) -> str | None:
    role_budget = ROLE_BUDGETS.get(role, 8)
    if role_visits.get(role, 0) > role_budget:
        return f"Role budget exceeded for {role}: {role_visits.get(role)} > {role_budget}."

    subtask_budget = _subtask_budget_for(subtask_key)
    if subtask_visits.get(subtask_key, 0) > subtask_budget:
        return (
            f"Subtask budget exceeded for {subtask_key}: "
            f"{subtask_visits.get(subtask_key)} > {subtask_budget}."
        )

    return None


def make_role_node(role: AgentName, event_logger: EventLogger | None = None) -> Callable[[AgentState], AgentState]:
    def node(state: AgentState) -> AgentState:
        step = state.get("step_count", 0) + 1
        role_visits = dict(state.get("role_visits", {}))
        subtask_visits = dict(state.get("subtask_visits", {}))
        subtask_key = _current_subtask_key(role, state)
        role_visits[role] = role_visits.get(role, 0) + 1
        subtask_visits[subtask_key] = subtask_visits.get(subtask_key, 0) + 1
        messages = _append_message(state, "user", _role_instruction(role, state))

        if event_logger:
            event_logger.emit("StateEvent", status="langgraph_node_started", node=role, step=step)

        budget_error = _budget_blocker(role, role_visits, subtask_key, subtask_visits)
        if budget_error:
            message = (
                "Blocked by role/subtask budget. "
                f"{budget_error} State summary: {_state_brief(state)}"
            )
            if event_logger:
                event_logger.emit(
                    "ErrorEvent",
                    status="budget_exceeded",
                    node=role,
                    step=step,
                    subtask=subtask_key,
                    error=budget_error,
                )
            return {
                "last_agent": role,
                "agent_output": message,
                "messages": _append_message(state, "assistant", message),
                "role_visits": role_visits,
                "subtask_visits": subtask_visits,
                "final_message": message,
                "next_agent": "final",
                "step_count": step,
            }

        if role == "final":
            validation_complete = _validation_complete(state)
            if _requires_validation(state) and not validation_complete:
                message = _finish_gate_message(state)
            elif validation_complete:
                message = _build_validated_final_message(state)
            else:
                message = "Done. No validation requirement was detected for this run."

            action = {
                "action": "final",
                "finish_reason": "validated" if validation_complete else "blocker",
                "message": message,
            }
            output = json.dumps(action, ensure_ascii=False)
            if event_logger:
                event_logger.emit(
                    "ActionEvent",
                    action="final",
                    node=role,
                    step=step,
                    tool=None,
                    payload=action,
                    synthetic=True,
                )
            return {
                "last_agent": role,
                "agent_output": output,
                "parsed_action": action,
                "messages": _append_message(state, "assistant", output),
                "role_outputs": _record_role_output(state, role, action),
                "role_visits": role_visits,
                "subtask_visits": subtask_visits,
                "final_message": message,
                "next_agent": "final",
                "step_count": step,
            }

        if _should_fast_handoff_to_code(role, state):
            action = _fast_handoff_action(role)
            output = json.dumps(action, ensure_ascii=False)
            if event_logger:
                event_logger.emit(
                    "ActionEvent",
                    action="final",
                    node=role,
                    step=step,
                    tool=None,
                    payload=action,
                    synthetic=True,
                )
            result: AgentState = {
                "last_agent": role,
                "agent_output": output,
                "parsed_action": action,
                "messages": _append_message(state, "assistant", output),
                "role_outputs": _record_role_output(state, role, action),
                "role_visits": role_visits,
                "subtask_visits": subtask_visits,
                "step_count": step,
                "next_agent": _next_pipeline_role(role),
            }
            if role == "planner":
                result["plan"] = str(action.get("message", ""))
            return result

        if (
            role == "code"
            and state.get("required_files")
            and not _missing_required_files(state)
            and not state.get("last_failure")
            and not _validation_complete(state)
        ):
            action = {
                "action": "final",
                "finish_reason": "handoff",
                "message": "All required files exist. Engineering hands off to QA validation.",
            }
            output = json.dumps(action, ensure_ascii=False)
            if event_logger:
                event_logger.emit(
                    "ActionEvent",
                    action="final",
                    node=role,
                    step=step,
                    tool=None,
                    payload=action,
                    synthetic=True,
                )
            return {
                "last_agent": role,
                "agent_output": output,
                "parsed_action": action,
                "messages": _append_message(state, "assistant", output),
                "role_outputs": _record_role_output(state, role, action),
                "files_modified": list(state.get("files_modified", [])),
                "json_retries": dict(state.get("json_retries", {})),
                "role_visits": role_visits,
                "subtask_visits": subtask_visits,
                "step_count": step,
                "next_agent": "test",
            }

        if role == "test":
            missing_files = _missing_required_files(state)
            if missing_files:
                message = json.dumps(
                    {
                        "action": "final",
                        "finish_reason": "handoff",
                        "message": "Validation skipped because required files are still missing.",
                        "missing_files": missing_files,
                    },
                    ensure_ascii=False,
                )
                return {
                    "last_agent": role,
                    "agent_output": message,
                    "messages": _append_message(state, "assistant", message),
                    "role_visits": role_visits,
                    "subtask_visits": subtask_visits,
                    "next_agent": "code",
                    "missing_files": missing_files,
                    "step_count": step,
                }

            forced_action = _forced_test_action(state)
            if forced_action is not None:
                output = json.dumps(forced_action, ensure_ascii=False)
                if event_logger:
                    event_logger.emit(
                        "ActionEvent",
                        action="tool",
                        node=role,
                        step=step,
                        tool=forced_action.get("tool"),
                        payload=_compact_action_for_log(forced_action),
                        synthetic=True,
                    )
                return {
                    "last_agent": role,
                    "agent_output": output,
                    "parsed_action": forced_action,
                    "messages": _append_message(state, "assistant", output),
                    "tool_name": str(forced_action.get("tool", "")),
                    "tool_args": forced_action.get("args", {}),
                    "role_visits": role_visits,
                    "subtask_visits": subtask_visits,
                    "next_agent": "tool",
                    "step_count": step,
                }

            if _validation_complete(state):
                action = {
                    "action": "final",
                    "finish_reason": "handoff",
                    "message": "QA validation complete: required test evidence is passing and required demo has run.",
                }
                output = json.dumps(action, ensure_ascii=False)
                if event_logger:
                    event_logger.emit(
                        "ActionEvent",
                        action="final",
                        node=role,
                        step=step,
                        tool=None,
                        payload=action,
                        synthetic=True,
                    )
                return {
                    "last_agent": role,
                    "agent_output": output,
                    "parsed_action": action,
                    "messages": _append_message(state, "assistant", output),
                    "role_outputs": _record_role_output(state, role, action),
                    "role_visits": role_visits,
                    "subtask_visits": subtask_visits,
                    "next_agent": "review",
                    "step_count": step,
                }

        output = get_agent(role).run(messages)

        try:
            action = parse_json(output)
        except Exception as exc:
            errors = list(state.get("errors", []))
            errors.append(f"{role}: invalid JSON: {exc}")
            json_retries = dict(state.get("json_retries", {}))
            json_retries[role] = json_retries.get(role, 0) + 1

            if event_logger:
                gate_stage = exc.result.stage if isinstance(exc, JsonGateError) else "parse"
                event_logger.emit(
                    "ErrorEvent",
                    status="json_gate_error",
                    node=role,
                    step=step,
                    retry=json_retries[role],
                    stage=gate_stage,
                    error=str(exc),
                    output_preview=_truncate(output, 1000),
                )

            if json_retries[role] >= MAX_JSON_RETRIES_PER_ROLE:
                if role == "final":
                    return {
                        "last_agent": role,
                        "agent_output": output,
                        "messages": _append_message(state, "assistant", output),
                        "errors": errors,
                        "json_retries": json_retries,
                        "role_visits": role_visits,
                        "subtask_visits": subtask_visits,
                        "final_message": (
                            "Blocked: Final Agent returned invalid JSON too many times. "
                            f"Last parse error: {exc}"
                        ),
                        "next_agent": "final",
                        "step_count": step,
                    }

                next_role = _next_pipeline_role(role)
                if role in STRICT_JSON_ROLES:
                    next_role = "final"

                synthetic_action = _synthetic_invalid_json_action(role, exc, next_role)
                synthetic_output = json.dumps(synthetic_action, ensure_ascii=False)

                if event_logger:
                    event_logger.emit(
                        "ActionEvent",
                        action="final",
                        node=role,
                        step=step,
                        tool=None,
                        synthetic=True,
                    )

                return {
                    "last_agent": role,
                    "agent_output": output,
                    "parsed_action": synthetic_action,
                    "messages": _append_message(state, "assistant", synthetic_output),
                    "role_outputs": _record_role_output(state, role, synthetic_action),
                    "errors": errors,
                    "json_retries": json_retries,
                    "role_visits": role_visits,
                    "subtask_visits": subtask_visits,
                    "next_agent": next_role,
                    "step_count": step,
                }

            retry_messages = _append_message(
                state,
                "user",
                _build_role_json_retry_message(role, exc, output),
            )
            return {
                "last_agent": role,
                "agent_output": output,
                "messages": retry_messages,
                "errors": errors,
                "json_retries": json_retries,
                "role_visits": role_visits,
                "subtask_visits": subtask_visits,
                "next_agent": role,
                "step_count": step,
            }

        messages_after = _append_message(state, "assistant", output)

        if event_logger:
            event_logger.emit(
                "ActionEvent",
                action=action.get("action"),
                node=role,
                step=step,
                tool=action.get("tool"),
                payload=_compact_action_for_log(action),
            )

        if (
            role == "code"
            and action.get("action") != "tool"
            and not state.get("files_modified")
        ):
            rescue_action = _extract_simple_file_create_action(state)
            if rescue_action is not None:
                action = rescue_action
                output = json.dumps(action, ensure_ascii=False)
                messages_after = _append_message(state, "assistant", output)
                if event_logger:
                    event_logger.emit(
                        "ActionEvent",
                        action="tool",
                        node=role,
                        step=step,
                        tool=action.get("tool"),
                        payload=_compact_action_for_log(action),
                        synthetic=True,
                    )

        result: AgentState = {
            "last_agent": role,
            "agent_output": output,
            "parsed_action": action,
            "messages": messages_after,
            "role_outputs": _record_role_output(state, role, action),
            "files_modified": _extract_files(action, state),
            "tests_run": _extract_tests(action, state),
            "json_retries": dict(state.get("json_retries", {})),
            "role_visits": role_visits,
            "subtask_visits": subtask_visits,
            "step_count": step,
        }

        if action.get("action") == "tool":
            result["tool_name"] = str(action.get("tool", ""))
            args = action.get("args", {})
            result["tool_args"] = args if isinstance(args, dict) else {}
            result["next_agent"] = "tool"
            return result

        if role == "code" and action.get("finish_reason") != "blocker":
            projected_state: AgentState = {
                **state,
                "files_modified": result.get("files_modified", []),
            }
            missing_files = _missing_required_files(projected_state)
            if missing_files:
                result["missing_files"] = missing_files
                result["next_agent"] = "code"
                return result

        if role == "test" and not _has_passing_validation(state):
            result["next_agent"] = "code"
            return result

        if role == "planner":
            plan = action.get("plan") or action.get("message") or action.get("summary")
            if plan:
                result["plan"] = str(plan)

        if role == "review":
            result["review_result"] = action

        if role == "ledger":
            result["ledger_result"] = action

        if role == "final" and action.get("action") == "final":
            if _requires_validation(state) and not _validation_complete(state):
                result["final_message"] = _finish_gate_message(state)
            else:
                result["final_message"] = str(action.get("message", ""))
            result["next_agent"] = "final"
            return result

        if role == "final":
            result["final_message"] = (
                "Blocked: Final Agent returned an unsupported action instead of "
                f"a JSON final object. Parsed action: {json.dumps(action, ensure_ascii=False, default=str)}"
            )
            result["next_agent"] = "final"
            return result

        result["next_agent"] = _next_pipeline_role(role)
        return result

    return node


def make_tool_node(event_logger: EventLogger | None = None) -> Callable[[AgentState], AgentState]:
    def node(state: AgentState) -> AgentState:
        step = state.get("step_count", 0) + 1
        tool_name = state.get("tool_name", "")
        tool_args = state.get("tool_args", {}) or {}
        last_agent = state.get("last_agent", "code")
        repeated = dict(state.get("repeated_tool_calls", {}))
        key = json.dumps({"tool": tool_name, "args": tool_args}, ensure_ascii=False, sort_keys=True)
        repeated[key] = repeated.get(key, 0) + 1
        requested_validation = _is_validation_tool(tool_name)
        last_failure = dict(state.get("last_failure", {})) if isinstance(state.get("last_failure"), dict) else {}
        repair_attempts = (
            dict(state.get("repair_attempts", {}))
            if isinstance(state.get("repair_attempts"), dict)
            else {}
        )

        handoff_after_tool = False
        if not get_agent(last_agent).is_tool_allowed(tool_name):
            tool_result = {
                "ok": False,
                "policy_blocked": True,
                "policy_code": "role_tool_not_allowed",
                "error": f"{last_agent} is not allowed to call {tool_name}",
            }
            handoff_after_tool = True
        elif last_agent == "code" and _should_block_whole_file_repair(state, tool_name, tool_args):
            failure_file = state.get("last_failure", {}).get("file")
            tool_result = {
                "ok": False,
                "policy_blocked": True,
                "policy_code": "repair_requires_patch_tool",
                "error": (
                    "A failed validation is active. Patch the failing file with "
                    "file_editor.file_editor_str_replace or file_editor.file_editor_insert "
                    f"instead of rewriting {failure_file}."
                ),
                "tool": tool_name,
                "args": tool_args,
            }
        elif repeated[key] > 2 and not requested_validation:
            tool_result = {
                "ok": False,
                "stuck": True,
                "error": "Same tool call repeated too many times in LangGraph tool node.",
                "tool": tool_name,
                "args": tool_args,
            }
            handoff_after_tool = True
        else:
            tool_result = call_tool(tool_name, tool_args)

        if event_logger:
            event_logger.emit(
                "ObservationEvent",
                step=step,
                node="tool",
                tool=tool_name,
                args=tool_args,
                result=tool_result,
            )

        messages = _append_message(
            state,
            "user",
            json.dumps({"tool_result": _compact_tool_result(tool_result)}, ensure_ascii=False),
        )

        metadata = tool_result.get("metadata") or tool_result.get("tool_metadata") or {}
        is_validation = bool(isinstance(metadata, dict) and metadata.get("validation")) or _is_validation_tool(tool_name)
        if is_validation:
            if tool_result.get("ok"):
                last_failure = {}
            else:
                extracted_failure = _extract_failure_summary(tool_result)
                if extracted_failure is None:
                    extracted_failure = {
                        "error": _truncate(str(tool_result.get("error") or tool_result.get("stderr") or "Validation failed."), 1000),
                        "tool": tool_name,
                        "path": tool_result.get("path") or tool_args.get("path"),
                    }
                last_failure = extracted_failure
                signature = _failure_signature(last_failure)
                repair_attempts[signature] = repair_attempts.get(signature, 0) + 1

        next_agent: str
        if last_agent == "test" and is_validation and not tool_result.get("ok"):
            next_agent = "code"
        elif handoff_after_tool and last_agent == "code" and _missing_required_files(
            {
                **state,
                "files_modified": _record_tool_files(tool_name, tool_args, tool_result, state),
                "tool_result": tool_result,
            }
        ):
            next_agent = "code"
        elif handoff_after_tool and last_agent in PIPELINE:
            next_agent = _next_pipeline_role(last_agent)
        elif last_agent in PIPELINE:
            next_agent = last_agent
        else:
            next_agent = "final"

        return {
            "tool_result": tool_result,
            "messages": messages,
            "repeated_tool_calls": repeated,
            "files_modified": _record_tool_files(tool_name, tool_args, tool_result, state),
            "tests_run": _record_tool_tests(tool_name, tool_args, tool_result, state),
            "last_failure": last_failure,
            "repair_attempts": repair_attempts,
            "next_agent": next_agent,
            "step_count": step,
        }

    return node


def route_next(state: AgentState) -> str:
    if state.get("final_message"):
        return END

    next_agent = state.get("next_agent", "research")
    if next_agent == "tool":
        return "tool"

    max_steps = int(state.get("max_steps", int(os.getenv("LANGGRAPH_MAX_STEPS", "80"))))
    if state.get("step_count", 0) >= max_steps:
        return "final"

    if next_agent in {*PIPELINE, "tool"}:
        return next_agent
    return "final"


def build_graph(event_logger: EventLogger | None = None):
    _require_langgraph()
    graph = StateGraph(AgentState)

    for role in PIPELINE:
        graph.add_node(role, make_role_node(role, event_logger))
    graph.add_node("tool", make_tool_node(event_logger))

    graph.add_edge(START, "research")

    route_map = {
        "research": "research",
        "planner": "planner",
        "architect": "architect",
        "code": "code",
        "test": "test",
        "review": "review",
        "ledger": "ledger",
        "final": "final",
        "tool": "tool",
        END: END,
    }
    for node_name in [*PIPELINE, "tool"]:
        graph.add_conditional_edges(node_name, route_next, route_map)

    return graph.compile()


def run_langgraph_orchestrator(user_task: str, max_steps: int | None = None) -> str:
    event_logger = EventLogger()
    if event_logger.enabled:
        print(f"LANGGRAPH RUN ID: {event_logger.run_id}")
        print(f"EVENT LOG: {event_logger.events_path}")

    app = build_graph(event_logger)
    required_files = _extract_required_files(user_task)
    existing_required_files = [
        path
        for path in required_files
        if (WORKSPACE_DIR / path).exists()
    ]
    missing_required_files = [
        path
        for path in required_files
        if path not in set(existing_required_files)
    ]
    initial_state: AgentState = {
        "user_task": user_task,
        "messages": [{"role": "user", "content": user_task}],
        "next_agent": "research",
        "step_count": 0,
        "max_steps": max_steps or int(os.getenv("LANGGRAPH_MAX_STEPS", "80")),
        "errors": [],
        "required_files": required_files,
        "missing_files": missing_required_files,
        "files_modified": existing_required_files,
        "tests_run": [],
        "role_outputs": {},
        "repeated_tool_calls": {},
        "json_retries": {},
        "role_visits": {},
        "subtask_visits": {},
        "last_failure": {},
        "repair_attempts": {},
    }
    final_state = app.invoke(initial_state)
    final_message = final_state.get("final_message")
    status = "completed" if final_message and not str(final_message).startswith("Blocked") else "blocked"
    event_logger.write_summary(
        status=status,
        metrics={
            "steps": final_state.get("step_count"),
            "events": event_logger.sequence,
            "tests_run": len(final_state.get("tests_run", [])),
            "files_modified": len(final_state.get("files_modified", [])),
            "role_visits": final_state.get("role_visits", {}),
        },
        final_message=str(final_message or ""),
    )
    if final_message:
        return str(final_message)
    return json.dumps(final_state, ensure_ascii=False, indent=2, default=str)
