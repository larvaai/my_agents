from __future__ import annotations

from pathlib import Path

from core.runtime_paths import PROJECT_DIR

PROMPTS_DIR = PROJECT_DIR / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.md"
USER_PROMPT_PATH = PROMPTS_DIR / "user_prompt.md"
MCP_TOOLS_PLACEHOLDER = "{{MCP_TOOLS}}"
SKILLS_PLACEHOLDER = "{{SKILLS}}"


def read_prompt_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def resolve_prompt_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = PROJECT_DIR / path
    return path.resolve()


def render_system_prompt(mcp_tools_prompt: str, skills_prompt: str = "") -> str:
    template = read_prompt_file(SYSTEM_PROMPT_PATH)
    if MCP_TOOLS_PLACEHOLDER in template:
        template = template.replace(MCP_TOOLS_PLACEHOLDER, mcp_tools_prompt)
    else:
        template = f"{template}\n\n{mcp_tools_prompt}"

    if SKILLS_PLACEHOLDER in template:
        return template.replace(SKILLS_PLACEHOLDER, skills_prompt)

    return f"{template}\n\n{skills_prompt}".strip()


def read_user_prompt(path: str | Path | None = None) -> str:
    prompt_path = resolve_prompt_path(path) if path else USER_PROMPT_PATH
    return read_prompt_file(prompt_path)
