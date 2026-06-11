from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.role_config import aliases, list_role_configs, load_role_agents


ROLE_AGENTS: dict[str, BaseAgent] = load_role_agents()
ALIASES = aliases()


def get_agent(name: str) -> BaseAgent:
    key = ALIASES.get(name, name)
    try:
        return ROLE_AGENTS[key]
    except KeyError as exc:
        known = sorted(set(ROLE_AGENTS) | set(ALIASES))
        raise KeyError(f"Unknown agent role: {name}. Known roles: {known}") from exc


def list_agents() -> list[dict]:
    return [
        {
            "key": key,
            **agent.describe(),
        }
        for key, agent in sorted(ROLE_AGENTS.items())
    ]


def list_agent_configs() -> list[dict]:
    return list_role_configs()
