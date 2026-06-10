from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


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
