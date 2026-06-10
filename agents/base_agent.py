from __future__ import annotations

import json
import re
import ast
from dataclasses import dataclass
from typing import Any

from llm import call_llm
from agents.lenses.base_lens import LensSpec, lens_names, render_department_lens_prompt
from output_gate import JsonGateError, parse_json_action
from tools.mcp_client import (
    MCPToolError,
    build_tool_prompt,
    canonicalize_tool_name,
    expand_tool_patterns,
)
from tools.prompt_loader import render_system_prompt
from tools.skill_loader import build_skills_prompt


@dataclass(frozen=True)
class BaseAgent:
    """
    Base class for role-scoped agents.

    The class does not execute tools directly. It builds a role-specific system
    prompt, calls the LLM, and blocks tool calls outside the role allowlist.
    Runtime tool execution still goes through the orchestrator and MCP client.
    """

    name: str
    role: str
    system_prompt: str
    department: str | None = None
    department_rule: str = ""
    lenses: tuple[LensSpec, ...] = ()
    allowed_tools: tuple[str, ...] | None = None
    allowed_skills: tuple[str, ...] | None = None
    model: str | None = None
    temperature: float = 0.2

    @property
    def canonical_allowed_tools(self) -> set[str] | None:
        return expand_tool_patterns(self.allowed_tools)

    def is_tool_allowed(self, tool_name: str) -> bool:
        allowed = self.canonical_allowed_tools
        if allowed is None:
            return True
        try:
            canonical_name = canonicalize_tool_name(tool_name)
        except MCPToolError:
            return False
        return canonical_name in allowed

    def build_system_prompt(self) -> str:
        role_header = "\n".join(
            [
                f"You are {self.name}.",
                f"Role: {self.role}",
                f"Department: {self.department}" if self.department else "",
                "",
                self.system_prompt.strip(),
                "",
                "Role boundary:",
                "- Stay inside your role.",
                "- Use only your allowed tools and allowed skills.",
                "- Project tool policy overrides user-requested tool names when they conflict.",
                "- Skills are instructions, not tools. Never put a skill name in the JSON tool field.",
                "- If the task requires a forbidden tool, return a short final JSON and do not list your full allowlist.",
            ]
        )
        lens_prompt = ""
        if self.lenses:
            lens_prompt = "\n\n" + render_department_lens_prompt(
                self.department or self.name,
                self.department_rule or "Use lenses as narrow cognitive checks before deciding.",
                self.lenses,
            )
        shared_prompt = render_system_prompt(
            build_tool_prompt(self.allowed_tools),
            build_skills_prompt(self.allowed_skills),
        )
        return f"{role_header}{lens_prompt}\n\n{shared_prompt}".strip()

    def _permission_block_response(self, tool_name: str) -> str:
        allowed = self.canonical_allowed_tools or set()
        payload = {
            "action": "final",
            "finish_reason": "blocker",
            "message": (
                f"{self.name} is not allowed to call '{tool_name}'. "
                "Handoff required to a role with that permission."
            ),
            "allowed_tools_preview": sorted(allowed)[:12],
        }
        return json.dumps(payload, ensure_ascii=False)

    def _parse_json_object(self, output: str) -> dict[str, Any] | None:
        try:
            return parse_json_action(output)
        except JsonGateError:
            pass

        text = output.strip()
        if text.startswith("```"):
            text = re.sub(r"^```json", "", text)
            text = re.sub(r"^```", "", text)
            text = re.sub(r"```$", "", text)
            text = text.strip()

        def repair_json_like(candidate: str) -> str:
            candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

            def escape_raw_content_field(value: str) -> str:
                def replace(match: re.Match[str]) -> str:
                    prefix = match.group(1)
                    content = match.group(2)
                    suffix = match.group(3)
                    return f"{prefix}{json.dumps(content, ensure_ascii=False)}{suffix}"

                return re.sub(
                    r'("content"\s*:\s*)"(.*)"(\s*,\s*"(?:overwrite|expected_replacements|line|old_text|new_text|path)"\s*:)',
                    replace,
                    value,
                    flags=re.DOTALL,
                )

            def balance_delimiters(value: str) -> str:
                stack: list[str] = []
                in_string = False
                escaped = False
                for char in value:
                    if escaped:
                        escaped = False
                        continue
                    if char == "\\":
                        escaped = True
                        continue
                    if char == '"':
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if char in "{[":
                        stack.append(char)
                    elif char == "}" and stack and stack[-1] == "{":
                        stack.pop()
                    elif char == "]" and stack and stack[-1] == "[":
                        stack.pop()

                closing = {"{": "}", "[": "]"}
                return value + "".join(closing[item] for item in reversed(stack))

            def escape_control_chars_in_strings(value: str) -> str:
                repaired: list[str] = []
                in_string = False
                escaped = False
                for char in value:
                    if escaped:
                        repaired.append(char)
                        escaped = False
                        continue
                    if char == "\\":
                        repaired.append(char)
                        escaped = True
                        continue
                    if char == '"':
                        repaired.append(char)
                        in_string = not in_string
                        continue
                    if in_string and char == "\n":
                        repaired.append("\\n")
                        continue
                    if in_string and char == "\r":
                        repaired.append("\\r")
                        continue
                    if in_string and char == "\t":
                        repaired.append("\\t")
                        continue
                    repaired.append(char)
                return "".join(repaired)

            candidate = balance_delimiters(escape_control_chars_in_strings(escape_raw_content_field(candidate)))

            def replace_single_quoted_value(match: re.Match[str]) -> str:
                prefix = match.group(1)
                literal = f"'{match.group(2)}'"
                try:
                    value = ast.literal_eval(literal)
                except Exception:
                    value = match.group(2)
                return f"{prefix}{json.dumps(value, ensure_ascii=False)}"

            return re.sub(
                r"(:\s*)'((?:\\.|[^'\\])*)'",
                replace_single_quoted_value,
                candidate,
            )

        def load_candidate(candidate: str) -> dict[str, Any] | None:
            for variant in (candidate, repair_json_like(candidate)):
                try:
                    parsed = json.loads(variant)
                except json.JSONDecodeError:
                    try:
                        parsed = ast.literal_eval(variant)
                    except Exception:
                        continue
                if isinstance(parsed, dict):
                    return parsed
            return None

        parsed = load_candidate(text)
        if parsed is not None:
            return parsed

        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", text):
            candidate = text[match.start():]
            for variant in (candidate, repair_json_like(candidate)):
                try:
                    parsed, _ = decoder.raw_decode(variant)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed
        return None

    def _extract_tool_name_from_text(self, output: str) -> str | None:
        action_tool = re.search(r'"action"\s*:\s*"tool"', output)
        tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', output)
        if action_tool and tool_match:
            return tool_match.group(1)
        return None

    def _guard_output(self, output: str) -> str:
        parsed = self._parse_json_object(output)
        if parsed is None:
            tool_name = self._extract_tool_name_from_text(output)
            if isinstance(tool_name, str) and not self.is_tool_allowed(tool_name):
                return self._permission_block_response(tool_name)
            return output

        if parsed.get("action") != "tool":
            return output

        tool_name = parsed.get("tool")
        if not isinstance(tool_name, str):
            return output

        if self.is_tool_allowed(tool_name):
            return output

        return self._permission_block_response(tool_name)

    def run(self, messages: list[dict[str, Any]]) -> str:
        full_messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(),
            }
        ] + messages
        output = call_llm(
            full_messages,
            model=self.model,
            temperature=self.temperature,
        )
        return self._guard_output(output)

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "department": self.department,
            "lenses": [lens.describe() for lens in self.lenses],
            "lens_names": list(lens_names(self.lenses)),
            "allowed_tools": sorted(self.canonical_allowed_tools or []),
            "allowed_skills": list(self.allowed_skills or []),
        }
