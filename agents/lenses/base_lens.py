from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LensResult:
    lens: str
    ok: bool
    data: dict[str, Any]
    raw: str = ""
    error: str | None = None


@dataclass(frozen=True)
class LensSpec:
    name: str
    department: str
    purpose: str
    allowed_tools: tuple[str, ...] = ()
    forbidden_tools: tuple[str, ...] = ()
    output_schema: dict[str, Any] | None = None

    def to_prompt_block(self) -> str:
        schema = self.output_schema or {}
        return "\n".join(
            [
                f"- {self.name}: {self.purpose}",
                f"  allowed_tools: {', '.join(self.allowed_tools) if self.allowed_tools else 'none'}",
                f"  forbidden_tools: {', '.join(self.forbidden_tools) if self.forbidden_tools else 'none'}",
                f"  output_schema: {json.dumps(schema, ensure_ascii=False)}",
            ]
        )

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "department": self.department,
            "purpose": self.purpose,
            "allowed_tools": list(self.allowed_tools),
            "forbidden_tools": list(self.forbidden_tools),
            "output_schema": self.output_schema or {},
        }


def lens_names(lenses: tuple[LensSpec, ...]) -> tuple[str, ...]:
    return tuple(lens.name for lens in lenses)


def safe_json_dumps(data: Any, *, indent: int = 2) -> str:
    return json.dumps(data, ensure_ascii=False, indent=indent, default=str)


def extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw).strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(raw[start:end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("Could not parse JSON object from lens output.")


def run_prompt_lens(
    lens_name: str,
    system_prompt: str,
    payload: dict[str, Any],
    *,
    model: str | None = None,
    temperature: float = 0.1,
) -> LensResult:
    from llm import call_llm

    user_prompt = (
        "INPUT:\n"
        f"{safe_json_dumps(payload)}\n\n"
        "Return only one valid JSON object. No markdown."
    )

    try:
        raw = call_llm(system_prompt, user_prompt, model=model, temperature=temperature)
        data = extract_json_object(raw)
        data.setdefault("lens", lens_name)
        return LensResult(lens=lens_name, ok=True, data=data, raw=raw)
    except Exception as exc:
        return LensResult(
            lens=lens_name,
            ok=False,
            data={"lens": lens_name, "error": str(exc)},
            error=str(exc),
        )


def lens_results_to_dict(results: list[LensResult]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for result in results:
        item = dict(result.data)
        item.setdefault("lens", result.lens)
        item.setdefault("ok", result.ok)
        if result.error:
            item["error"] = result.error
        output.append(item)
    return output


def render_department_lens_prompt(
    department_name: str,
    department_rule: str,
    lenses: tuple[LensSpec, ...],
) -> str:
    blocks = "\n".join(lens.to_prompt_block() for lens in lenses)
    return "\n".join(
        [
            f"Department model: {department_name}",
            department_rule.strip(),
            "",
            "Lens operating rules:",
            "- Lenses are cognitive review roles, not independent tool executors.",
            "- Use each lens to inspect the task from one narrow angle.",
            "- The department agent synthesizes lens findings and makes the decision.",
            "- Keep lens findings compact; do not let lens analysis become a separate conversation.",
            "- Put lens output inside your final JSON as department_report or relevant report fields when useful.",
            "- Tool calls must still use the normal JSON tool protocol and your role allowlist.",
            "",
            "Available lenses:",
            blocks,
        ]
    )
