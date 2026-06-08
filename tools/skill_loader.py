from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_DIR / "skills"


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    path: Path


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
    )


def load_skills() -> list[Skill]:
    if not SKILLS_DIR.exists():
        return []

    skills = []
    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        skills.append(_parse_skill_markdown(skill_file))
    return skills


def build_skills_prompt() -> str:
    skills = load_skills()
    if not skills:
        return "No project skills are installed."

    sections = ["Available project skills:"]
    for skill in skills:
        sections.append(
            "\n".join(
                [
                    f"## {skill.name}",
                    f"Description: {skill.description}",
                    f"Path: {skill.path}",
                    skill.body,
                ]
            )
        )

    return "\n\n".join(sections)
