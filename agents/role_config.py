from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agents.base_agent import BaseAgent
from agents.lenses import (
    ARCHITECT_LENSES,
    BUSINESS_ANALYST_LENSES,
    CODE_LENSES,
    FINAL_LENSES,
    LEDGER_LENSES,
    PLANNER_LENSES,
    RESEARCH_LENSES,
    REVIEW_LENSES,
    TEST_LENSES,
    LensSpec,
)
from core.runtime_paths import PROJECT_DIR


AGENTS_CONFIG_PATH = PROJECT_DIR / "config" / "agents.yaml"
DEFAULT_ROLES_DIR = PROJECT_DIR / "config" / "roles"

LENS_GROUPS: dict[str, tuple[LensSpec, ...]] = {
    "architect": ARCHITECT_LENSES,
    "business_analyst": BUSINESS_ANALYST_LENSES,
    "code": CODE_LENSES,
    "final": FINAL_LENSES,
    "ledger": LEDGER_LENSES,
    "planner": PLANNER_LENSES,
    "research": RESEARCH_LENSES,
    "review": REVIEW_LENSES,
    "test": TEST_LENSES,
    "none": (),
}


@dataclass(frozen=True)
class RoleConfig:
    key: str
    name: str
    role: str
    system_prompt: str
    department: str | None = None
    department_rule: str = ""
    lenses: str | list[str] | None = None
    allowed_tools: tuple[str, ...] | None = None
    allowed_skills: tuple[str, ...] | None = None
    route_permissions: dict[str, Any] = field(default_factory=dict)
    test_ownership: dict[str, Any] = field(default_factory=dict)


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a mapping: {path}")
    return data


def load_agents_config(path: Path = AGENTS_CONFIG_PATH) -> dict[str, Any]:
    return _read_yaml(path)


def roles_dir() -> Path:
    raw_path = load_agents_config().get("roles_dir")
    if not raw_path:
        return DEFAULT_ROLES_DIR
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = PROJECT_DIR / path
    return path


def role_keys() -> list[str]:
    keys = load_agents_config().get("roles", [])
    if not isinstance(keys, list) or not all(isinstance(item, str) for item in keys):
        raise ValueError("config/agents.yaml must define roles as a list of strings.")
    return keys


def aliases() -> dict[str, str]:
    raw_aliases = load_agents_config().get("aliases", {})
    if not isinstance(raw_aliases, dict):
        raise ValueError("config/agents.yaml aliases must be a mapping.")
    return {str(key): str(value) for key, value in raw_aliases.items()}


def load_role_config(key: str) -> RoleConfig:
    path = roles_dir() / f"{key}.yaml"
    raw = _read_yaml(path)
    role_key = str(raw.get("key") or key)
    if role_key != key:
        raise ValueError(f"Role config key mismatch in {path}: {role_key} != {key}")

    for required in ("name", "role", "system_prompt"):
        if not raw.get(required):
            raise ValueError(f"Role config missing {required}: {path}")

    allowed_tools = raw.get("allowed_tools")
    if allowed_tools is not None:
        if not isinstance(allowed_tools, list) or not all(isinstance(item, str) for item in allowed_tools):
            raise ValueError(f"allowed_tools must be a list of strings: {path}")
        allowed_tools = tuple(allowed_tools)

    allowed_skills = raw.get("allowed_skills")
    if allowed_skills is not None:
        if not isinstance(allowed_skills, list) or not all(isinstance(item, str) for item in allowed_skills):
            raise ValueError(f"allowed_skills must be a list of strings: {path}")
        allowed_skills = tuple(allowed_skills)

    route_permissions = raw.get("route_permissions") or {}
    test_ownership = raw.get("test_ownership") or {}
    if not isinstance(route_permissions, dict) or not isinstance(test_ownership, dict):
        raise ValueError(f"route_permissions and test_ownership must be mappings: {path}")

    return RoleConfig(
        key=role_key,
        name=str(raw["name"]),
        role=str(raw["role"]),
        department=raw.get("department"),
        department_rule=str(raw.get("department_rule") or ""),
        system_prompt=str(raw["system_prompt"]),
        lenses=raw.get("lenses"),
        allowed_tools=allowed_tools,
        allowed_skills=allowed_skills,
        route_permissions=route_permissions,
        test_ownership=test_ownership,
    )


def _resolve_lenses(config: RoleConfig) -> tuple[LensSpec, ...]:
    raw_lenses = config.lenses
    if raw_lenses is None:
        return ()
    if isinstance(raw_lenses, str):
        try:
            return LENS_GROUPS[raw_lenses]
        except KeyError as exc:
            raise ValueError(f"Unknown lens group for {config.key}: {raw_lenses}") from exc
    if isinstance(raw_lenses, list):
        specs: list[LensSpec] = []
        by_name = {
            lens.name: lens
            for group in LENS_GROUPS.values()
            for lens in group
        }
        for name in raw_lenses:
            if not isinstance(name, str) or name not in by_name:
                raise ValueError(f"Unknown lens name for {config.key}: {name}")
            specs.append(by_name[name])
        return tuple(specs)
    raise ValueError(f"Invalid lenses value for {config.key}: {raw_lenses!r}")


def build_agent(config: RoleConfig) -> BaseAgent:
    return BaseAgent(
        name=config.name,
        role=config.role,
        department=config.department,
        department_rule=config.department_rule,
        system_prompt=config.system_prompt,
        lenses=_resolve_lenses(config),
        allowed_tools=config.allowed_tools,
        allowed_skills=config.allowed_skills,
        route_permissions=config.route_permissions,
        test_ownership=config.test_ownership,
    )


def load_role_agents() -> dict[str, BaseAgent]:
    return {
        key: build_agent(load_role_config(key))
        for key in role_keys()
    }


def list_role_configs() -> list[dict[str, Any]]:
    return [
        {
            "key": config.key,
            "name": config.name,
            "department": config.department,
            "lenses": config.lenses,
            "allowed_tools": list(config.allowed_tools or []),
            "allowed_skills": list(config.allowed_skills or []),
            "route_permissions": config.route_permissions,
            "test_ownership": config.test_ownership,
        }
        for config in (load_role_config(key) for key in role_keys())
    ]
