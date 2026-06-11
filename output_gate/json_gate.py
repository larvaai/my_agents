from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from output_gate.repair_rules import (
    extract_largest_json_region,
    light_json_repair,
    strip_bom,
    strip_markdown_fence,
    try_literal_eval,
)
from features.mcp_tools.config import MCP_TOOL_NAMES, TOOL_ALIASES, WORKSPACE_DIR
from features.mcp_tools.policy import check_tool_policy
from features.mcp_tools.schemas import JSON_TYPE_NAMES, TOOL_SCHEMAS, ToolSchema


MAX_ERROR_CANDIDATE_CHARS = 2000
MAX_SAFE_CONTENT_CHARS = 1_000_000


@dataclass(frozen=True)
class GateResult:
    ok: bool
    data: dict[str, Any] | None = None
    stage: str = ""
    error: dict[str, Any] | None = None
    repaired_by_code: bool = False
    candidate: str | None = None


class JsonGateError(ValueError):
    def __init__(self, result: GateResult):
        self.result = result
        message = json.dumps(
            {
                "stage": result.stage,
                "error": result.error,
                "candidate": _truncate(result.candidate or "", 1000),
            },
            ensure_ascii=False,
            default=str,
        )
        super().__init__(message)


def json_gate(raw_output: str) -> GateResult:
    candidates = build_candidates(raw_output)
    parse_errors: list[dict[str, Any] | None] = []

    for index, candidate in enumerate(candidates):
        parsed = try_parse_json(candidate)
        if not parsed.ok:
            parse_errors.append(parsed.error)
            continue

        parsed_obj = parsed.data or {}
        obj = apply_action_aliases(parsed_obj)
        repaired_by_code = index != 0 or obj != parsed_obj

        schema_result = validate_agent_action_schema(obj)
        if not schema_result.ok:
            return _with_context(schema_result, candidate, repaired_by_code)

        obj = schema_result.data or obj
        if obj.get("action") == "tool":
            resolved = resolve_tool_action(obj)
            if not resolved.ok:
                return _with_context(resolved, candidate, repaired_by_code)
            resolved_obj = resolved.data or obj
            obj = apply_safe_arg_aliases(resolved_obj)
            repaired_by_code = repaired_by_code or obj.get("args") != resolved_obj.get("args")

        tool_result = validate_tool_args_for_action(obj)
        if not tool_result.ok:
            return _with_context(tool_result, candidate, repaired_by_code)
        obj = tool_result.data or obj

        dry_result = dry_run_safety_check(obj)
        if not dry_result.ok:
            return _with_context(dry_result, candidate, repaired_by_code)

        return GateResult(
            ok=True,
            data=obj,
            stage="pass",
            repaired_by_code=repaired_by_code,
            candidate=candidate,
        )

    return GateResult(
        ok=False,
        stage="parse",
        error={
            "error_type": "JSON_PARSE_FAILED",
            "message": "All deterministic JSON repair attempts failed.",
            "parse_errors": parse_errors[-3:],
        },
        candidate=candidates[-1] if candidates else _truncate(raw_output, MAX_ERROR_CANDIDATE_CHARS),
    )


def parse_json_action(raw_output: str) -> dict[str, Any]:
    result = json_gate(raw_output)
    if not result.ok or result.data is None:
        raise JsonGateError(result)
    return result.data


def _with_context(result: GateResult, candidate: str, repaired_by_code: bool) -> GateResult:
    return GateResult(
        ok=result.ok,
        data=result.data,
        stage=result.stage,
        error=result.error,
        repaired_by_code=repaired_by_code,
        candidate=result.candidate or candidate,
    )


def build_candidates(raw_output: str) -> list[str]:
    raw = raw_output or ""
    base = strip_bom(raw)
    fenced = strip_markdown_fence(base)
    region = extract_largest_json_region(fenced)
    candidates = [
        base,
        fenced,
        light_json_repair(fenced, extract_region=False),
        region,
        light_json_repair(region),
    ]

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        unique.append(candidate)
        seen.add(candidate)
    return unique


def try_parse_json(candidate: str) -> GateResult:
    last_error: dict[str, Any] | None = None
    for parser_name, parser in (("json", json.loads), ("literal_eval", try_literal_eval)):
        try:
            parsed = parser(candidate)
        except json.JSONDecodeError as exc:
            last_error = {
                "error_type": "JSON_DECODE_ERROR",
                "parser": parser_name,
                "message": exc.msg,
                "line": exc.lineno,
                "column": exc.colno,
                "position": exc.pos,
                "near": candidate[max(0, exc.pos - 80): exc.pos + 80],
            }
            continue
        except Exception as exc:
            last_error = {
                "error_type": "JSON_PARSE_ERROR",
                "parser": parser_name,
                "message": str(exc),
            }
            continue

        if isinstance(parsed, dict):
            return GateResult(ok=True, data=parsed, stage="parse", candidate=candidate)
        if parsed is not None:
            return GateResult(
                ok=False,
                stage="parse",
                error={
                    "error_type": "ROOT_NOT_OBJECT",
                    "message": "Root JSON must be an object.",
                    "received_type": type(parsed).__name__,
                },
                candidate=_truncate(candidate, MAX_ERROR_CANDIDATE_CHARS),
            )

    return GateResult(
        ok=False,
        stage="parse",
        error=last_error
        or {"error_type": "JSON_PARSE_ERROR", "message": "No parser accepted the candidate."},
        candidate=_truncate(candidate, MAX_ERROR_CANDIDATE_CHARS),
    )


def apply_action_aliases(obj: dict[str, Any]) -> dict[str, Any]:
    fixed = dict(obj)
    if "action" not in fixed and "tool" not in fixed:
        if isinstance(fixed.get("path"), str) and isinstance(fixed.get("lines"), list):
            return {
                "action": "tool",
                "tool": "file_editor.file_editor_write_lines",
                "args": fixed,
            }
        if isinstance(fixed.get("path"), str) and isinstance(fixed.get("content"), str):
            return {
                "action": "tool",
                "tool": "file_editor.file_editor_create",
                "args": fixed,
            }
    if "tool" not in fixed and isinstance(fixed.get("tool_name"), str):
        fixed["tool"] = fixed["tool_name"]
    if "args" not in fixed:
        for alias in ("arguments", "parameters", "input"):
            if isinstance(fixed.get(alias), dict):
                fixed["args"] = fixed[alias]
                break
    return fixed


def validate_agent_action_schema(obj: dict[str, Any]) -> GateResult:
    action = obj.get("action")
    if action not in {"tool", "final"}:
        return GateResult(
            ok=False,
            stage="action_schema",
            error={
                "error_type": "INVALID_ACTION",
                "message": "Field 'action' must be either 'tool' or 'final'.",
                "received": action,
            },
        )

    if action == "tool":
        if "tool" not in obj:
            return GateResult(
                ok=False,
                stage="action_schema",
                error={"error_type": "MISSING_TOOL", "message": "Tool action requires field 'tool'."},
            )
        if "args" not in obj:
            return GateResult(
                ok=False,
                stage="action_schema",
                error={"error_type": "MISSING_ARGS", "message": "Tool action requires field 'args'."},
            )
        if not isinstance(obj["tool"], str):
            return GateResult(
                ok=False,
                stage="action_schema",
                error={
                    "error_type": "TOOL_NOT_STRING",
                    "message": "Field 'tool' must be string.",
                    "received_type": type(obj["tool"]).__name__,
                },
            )
        if not isinstance(obj["args"], dict):
            return GateResult(
                ok=False,
                stage="action_schema",
                error={
                    "error_type": "ARGS_NOT_OBJECT",
                    "message": "Field 'args' must be object.",
                    "received_type": type(obj["args"]).__name__,
                },
            )

    if action == "final":
        message_like_fields = ("message", "summary", "plan", "result", "review")
        if not any(isinstance(obj.get(field), str) for field in message_like_fields):
            return GateResult(
                ok=False,
                stage="action_schema",
                error={
                    "error_type": "MISSING_MESSAGE",
                    "message": "Final action requires a string message, summary, plan, result, or review field.",
                },
            )
        if "message" not in obj:
            fixed = dict(obj)
            for field in message_like_fields[1:]:
                if isinstance(fixed.get(field), str):
                    fixed["message"] = fixed[field]
                    return GateResult(ok=True, data=fixed, stage="action_schema")

    return GateResult(ok=True, data=obj, stage="action_schema")


def resolve_tool_action(obj: dict[str, Any]) -> GateResult:
    tool_name = str(obj.get("tool") or "")
    args = dict(obj.get("args") or {})

    resolved = _resolve_tool(tool_name, args)
    if not resolved.ok:
        return resolved

    fixed = dict(obj)
    fixed["tool"] = resolved.data["tool"]
    fixed["args"] = resolved.data["args"]
    fixed["requested_tool"] = tool_name
    return GateResult(ok=True, data=fixed, stage="tool_resolve")


def _resolve_tool(tool_name: str, args: dict[str, Any]) -> GateResult:
    if tool_name in TOOL_ALIASES:
        server_name, resolved_tool_name, rename_map = TOOL_ALIASES[tool_name]
        mapped_args = {
            rename_map.get(key, key): value
            for key, value in args.items()
        }
        return GateResult(
            ok=True,
            data={"tool": f"{server_name}.{resolved_tool_name}", "args": mapped_args},
            stage="tool_resolve",
        )

    if "." in tool_name:
        server_name, resolved_tool_name = tool_name.split(".", 1)
        if server_name not in MCP_TOOL_NAMES:
            return _unknown_tool(tool_name, f"Unknown MCP server: {server_name}")
        if resolved_tool_name not in MCP_TOOL_NAMES[server_name]:
            return _unknown_tool(tool_name, f"Unknown MCP tool on server {server_name}: {resolved_tool_name}")
        return GateResult(
            ok=True,
            data={"tool": f"{server_name}.{resolved_tool_name}", "args": args},
            stage="tool_resolve",
        )

    matches = [
        server_name
        for server_name, tool_names in MCP_TOOL_NAMES.items()
        if tool_name in tool_names
    ]
    if not matches:
        return _unknown_tool(tool_name, f"Unknown MCP tool: {tool_name}")
    if len(matches) > 1:
        return GateResult(
            ok=False,
            stage="tool_resolve",
            error={
                "error_type": "AMBIGUOUS_TOOL",
                "message": f"Tool '{tool_name}' is ambiguous; use server.tool form.",
                "matches": [f"{server}.{tool_name}" for server in matches],
            },
        )
    return GateResult(
        ok=True,
        data={"tool": f"{matches[0]}.{tool_name}", "args": args},
        stage="tool_resolve",
    )


def _unknown_tool(tool_name: str, message: str) -> GateResult:
    return GateResult(
        ok=False,
        stage="tool_resolve",
        error={
            "error_type": "UNKNOWN_TOOL",
            "message": message,
            "tool": tool_name,
            "available_tools_preview": sorted(TOOL_SCHEMAS)[:80],
        },
    )


def apply_safe_arg_aliases(obj: dict[str, Any]) -> dict[str, Any]:
    if obj.get("action") != "tool":
        return obj
    tool = obj.get("tool")
    args = obj.get("args")
    if not isinstance(tool, str) or not isinstance(args, dict):
        return obj

    aliases: dict[str, dict[str, str]] = {
        "filesystem.write_file": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
            "data": "content",
            "text": "content",
            "body": "content",
        },
        "filesystem.read_file": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
        },
        "filesystem.read_text_file": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
        },
        "filesystem.list_directory": {
            "folder": "path",
            "dir": "path",
            "directory": "path",
        },
        "file_editor.file_editor_create": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
            "data": "content",
            "text": "content",
            "body": "content",
        },
        "file_editor.file_editor_write_lines": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
            "content_lines": "lines",
            "line_list": "lines",
        },
        "file_editor.file_editor_view": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
        },
        "python.run_python": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
        },
        "lint_test.test_python_file": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
        },
        "document.document_write_markdown": {
            "filepath": "path",
            "file_path": "path",
            "file": "path",
            "body": "content",
            "text": "content",
        },
        "terminal.terminal_run": {
            "command_args": "argv",
        },
    }

    if tool not in aliases:
        return obj

    fixed_args = dict(args)
    for old_key, new_key in aliases[tool].items():
        if old_key in fixed_args and new_key not in fixed_args:
            fixed_args[new_key] = fixed_args.pop(old_key)

    fixed = dict(obj)
    fixed["args"] = fixed_args
    return fixed


def validate_tool_args_for_action(obj: dict[str, Any]) -> GateResult:
    if obj.get("action") != "tool":
        return GateResult(ok=True, data=obj, stage="tool_args")

    tool_name = str(obj.get("tool") or "")
    args = obj.get("args")
    if not isinstance(args, dict):
        return GateResult(
            ok=False,
            stage="tool_args",
            error={"error_type": "ARGS_NOT_OBJECT", "tool": tool_name},
        )

    schema = TOOL_SCHEMAS.get(tool_name)
    if schema is None:
        return _unknown_tool(tool_name, f"Unknown tool schema: {tool_name}")

    issues = _schema_issues(schema, args)
    if issues:
        return GateResult(
            ok=False,
            stage="tool_args",
            error={
                "error_type": "TOOL_ARGS_SCHEMA_ERROR",
                "tool": tool_name,
                "issues": issues,
                "expected_args": {
                    key: {
                        "type": spec.type_name,
                        "required": spec.required,
                    }
                    for key, spec in schema.args.items()
                },
            },
        )

    return GateResult(ok=True, data=obj, stage="tool_args")


def _schema_issues(schema: ToolSchema, args: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field, spec in schema.args.items():
        if spec.required and field not in args:
            issues.append(
                {
                    "path": f"$.args.{field}",
                    "error": "missing_required_field",
                    "expected_type": spec.type_name,
                }
            )

    if not schema.allow_extra:
        allowed = set(schema.args)
        for field in sorted(set(args) - allowed):
            issues.append(
                {
                    "path": f"$.args.{field}",
                    "error": "unknown_field",
                    "allowed_fields": sorted(allowed),
                }
            )

    for field, value in args.items():
        spec = schema.args.get(field)
        if spec is None or value is None:
            continue
        expected = JSON_TYPE_NAMES.get(spec.type_name)
        if expected and not isinstance(value, expected):
            issues.append(
                {
                    "path": f"$.args.{field}",
                    "error": "wrong_type",
                    "expected_type": spec.type_name,
                    "received_type": type(value).__name__,
                }
            )

    return issues


def dry_run_safety_check(obj: dict[str, Any]) -> GateResult:
    if obj.get("action") != "tool":
        return GateResult(ok=True, data=obj, stage="dry_run")

    tool_name = str(obj.get("tool") or "")
    args = obj.get("args") or {}
    if not isinstance(args, dict):
        return GateResult(ok=False, stage="dry_run", error={"error_type": "ARGS_NOT_OBJECT"})

    server_name, mcp_tool_name = tool_name.split(".", 1)
    policy = check_tool_policy(server_name, mcp_tool_name, args)
    if not policy.allowed:
        return GateResult(
            ok=False,
            stage="dry_run",
            error={
                "error_type": "POLICY_BLOCKED",
                "policy_code": policy.code,
                "message": policy.reason,
                "tool": tool_name,
            },
        )

    path_error = _validate_path_fields(tool_name, args)
    if path_error is not None:
        return path_error

    content_error = _validate_content_size(tool_name, args)
    if content_error is not None:
        return content_error

    if tool_name == "terminal.terminal_run":
        command_error = _validate_terminal_args(args)
        if command_error is not None:
            return command_error

    return GateResult(ok=True, data=obj, stage="dry_run")


def _validate_path_fields(tool_name: str, args: dict[str, Any]) -> GateResult | None:
    path_fields = ("path", "source", "destination", "cwd", "repo_path")
    for field in path_fields:
        value = args.get(field)
        if not isinstance(value, str):
            continue
        if field == "repo_path" and value in {"", "."}:
            continue
        result = validate_safe_relative_path(value, field=field, tool=tool_name)
        if not result.ok:
            return result

    paths = args.get("paths")
    if isinstance(paths, list):
        for index, value in enumerate(paths):
            if isinstance(value, str):
                result = validate_safe_relative_path(value, field=f"paths[{index}]", tool=tool_name)
                if not result.ok:
                    return result
    return None


def validate_safe_relative_path(path: str, *, field: str = "path", tool: str = "") -> GateResult:
    normalized = path.replace("\\", "/").strip()
    if not normalized:
        return GateResult(
            ok=False,
            stage="dry_run",
            error={
                "error_type": "EMPTY_PATH",
                "message": "Path must not be empty.",
                "field": field,
                "tool": tool,
            },
        )

    if normalized.startswith("/"):
        return _path_error("ABSOLUTE_PATH_NOT_ALLOWED", path, field, tool)
    if ":" in normalized:
        return _path_error("WINDOWS_ABSOLUTE_PATH_NOT_ALLOWED", path, field, tool)
    if ".." in [part for part in normalized.split("/") if part]:
        return _path_error("PATH_ESCAPE_NOT_ALLOWED", path, field, tool)

    target = (WORKSPACE_DIR / normalized).resolve()
    workspace = WORKSPACE_DIR.resolve()
    if target != workspace and not target.is_relative_to(workspace):
        return _path_error("PATH_OUTSIDE_WORKSPACE", path, field, tool)

    return GateResult(ok=True, stage="dry_run")


def _path_error(error_type: str, path: str, field: str, tool: str) -> GateResult:
    return GateResult(
        ok=False,
        stage="dry_run",
        error={
            "error_type": error_type,
            "message": "Path must be a safe workspace-relative path.",
            "path": path,
            "field": field,
            "tool": tool,
        },
    )


def _validate_content_size(tool_name: str, args: dict[str, Any]) -> GateResult | None:
    for field in ("content", "text", "body"):
        value = args.get(field)
        if isinstance(value, str) and len(value) > MAX_SAFE_CONTENT_CHARS:
            return GateResult(
                ok=False,
                stage="dry_run",
                error={
                    "error_type": "CONTENT_TOO_LARGE",
                    "message": f"{field} is too large for a single tool call.",
                    "tool": tool_name,
                    "field": field,
                    "chars": len(value),
                    "max_chars": MAX_SAFE_CONTENT_CHARS,
                },
            )
    return None


def _validate_terminal_args(args: dict[str, Any]) -> GateResult | None:
    argv = args.get("argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        return GateResult(
            ok=False,
            stage="dry_run",
            error={
                "error_type": "TERMINAL_ARGV_REQUIRED",
                "message": "terminal.terminal_run requires argv as a list of strings.",
            },
        )

    joined = " ".join(argv).lower()
    dangerous_fragments = (
        "rm -rf /",
        "del /s",
        "format ",
        "shutdown",
        "reboot",
        "mkfs",
        ":(){",
        "curl ",
        "wget ",
        "invoke-webrequest",
        " iwr ",
    )
    for fragment in dangerous_fragments:
        if fragment in joined:
            return GateResult(
                ok=False,
                stage="dry_run",
                error={
                    "error_type": "DANGEROUS_COMMAND",
                    "message": f"Command contains dangerous fragment: {fragment}",
                    "argv": argv,
                },
            )
    return None


def build_json_gate_retry_message(result: GateResult, raw_output: str) -> str:
    return (
        "Your previous output failed the JSON gate.\n"
        "Return ONLY one corrected JSON object. No markdown. No explanation.\n\n"
        "Expected contracts:\n"
        '- Tool call: {"action":"tool","tool":"server.tool_name","args":{...}}\n'
        '- Final answer: {"action":"final","message":"..."}\n\n'
        f"Failed stage: {result.stage}\n"
        f"Sandbox error: {json.dumps(result.error, ensure_ascii=False, default=str)}\n\n"
        "Repair rules:\n"
        "- If parse failed, fix syntax only.\n"
        "- If schema failed, fix missing/wrong fields without changing intent.\n"
        "- If tool_args failed, match the registered tool schema exactly.\n"
        "- If dry_run failed, choose a safe workspace-relative path or safe argv.\n\n"
        "File writing rule:\n"
        "- For generated code, prefer file_editor.file_editor_write_lines.\n"
        "- Its args.lines should be a JSON array where each item is one physical file line when practical.\n"
        "- Do not put an entire file into one string with \\n escapes.\n"
        "- Every args.lines item must use double quotes as the JSON delimiter; use single quotes only inside the code text.\n"
        "- Create or repair one file per tool call, using compact passing code.\n\n"
        f"Previous bad output:\n{_truncate(raw_output, 2000)}"
    )


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}...<truncated {len(text) - max_chars} chars>"


def dump_gate_result(result: GateResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "stage": result.stage,
        "error": result.error,
        "repaired_by_code": result.repaired_by_code,
        "candidate": _truncate(result.candidate or "", MAX_ERROR_CANDIDATE_CHARS),
        "data": result.data,
    }


def is_workspace_relative(path: str) -> bool:
    try:
        validate_safe_relative_path(path)
    except Exception:
        return False
    return True


def workspace_path(path: str) -> Path:
    return (WORKSPACE_DIR / path).resolve()
