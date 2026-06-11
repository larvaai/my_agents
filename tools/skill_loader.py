from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from core.runtime_paths import PROJECT_DIR

SKILLS_DIR = PROJECT_DIR / "skills"


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    path: Path
    agent_metadata: dict[str, Any]


def _load_agent_metadata(skill_dir: Path) -> dict[str, Any]:
    metadata_path = skill_dir / "agents" / "openai.yaml"

    if not metadata_path.exists():
        return {}

    data = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Skill agent metadata must be a mapping: {metadata_path}")

    return data


def _parse_skill_markdown(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8").strip()
    if not text.startswith("---"):
        raise ValueError(f"Missing YAML frontmatter: {path}")

    _, frontmatter, body = text.split("---", 2)
    metadata: dict[str, str] = {}
    for raw_line in frontmatter.strip().splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        metadata[key.strip()] = value.strip()

    name = metadata.get("name")
    description = metadata.get("description")
    if not name or not description:
        raise ValueError(f"Skill must define name and description: {path}")

    return Skill(
        name=name,
        description=description,
        body=body.strip(),
        path=path,
        agent_metadata=_load_agent_metadata(path.parent),
    )


def load_skills() -> list[Skill]:
    if not SKILLS_DIR.exists():
        return []

    skills = []
    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        skills.append(_parse_skill_markdown(skill_file))
    return skills


def build_skills_prompt(allowed_skills: list[str] | tuple[str, ...] | set[str] | None = None) -> str:
    skills = load_skills()
    if allowed_skills is not None and "*" not in allowed_skills:
        allowed = set(allowed_skills)
        skills = [
            skill
            for skill in skills
            if skill.name in allowed
        ]

    if not skills:
        return "No project skills are available for this agent."

    sections = ["Available project skills:"]
    for skill in skills:
        interface = skill.agent_metadata.get("interface", {})
        interface_lines = []

        if isinstance(interface, dict):
            for key in ("display_name", "short_description", "default_prompt"):
                value = interface.get(key)
                if value:
                    interface_lines.append(f"{key}: {value}")

        metadata_text = (
            "Interface metadata:\n" + "\n".join(interface_lines)
            if interface_lines
            else "Interface metadata: none"
        )

        sections.append(
            "\n".join(
                [
                    f"## {skill.name}",
                    f"Description: {skill.description}",
                    f"Path: {skill.path}",
                    metadata_text,
                    skill.body,
                ]
            )
        )

    return "\n\n".join(sections)
