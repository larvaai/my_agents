from __future__ import annotations

from pathlib import Path
from typing import Any


def infer_runtime_commands(repo_path: Path, repo_profile: dict[str, Any], file_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = {node["path"] for node in file_map}
    commands: list[dict[str, Any]] = []

    if "main.py" in paths:
        commands.append(
            {
                "id": "run_main",
                "command": "python main.py",
                "purpose": "run primary Python entrypoint",
                "source": "file_map",
                "confidence": 0.82,
                "risk": "low",
            }
        )

    if any(node["is_test"] for node in file_map) and "python" in repo_profile["languages"]:
        test_command = "python -m pytest" if "pytest" in repo_profile["frameworks"] else "python -m unittest discover -s tests"
        commands.append(
            {
                "id": "python_tests",
                "command": test_command,
                "purpose": "run Python tests",
                "source": "file_map+manifest",
                "confidence": 0.76,
                "risk": "medium",
            }
        )

    scripts = repo_profile.get("scripts", {})
    for name, script in sorted(scripts.items()):
        commands.append(
            {
                "id": f"npm_{name}",
                "command": f"npm run {name}",
                "purpose": f"package.json script: {script}",
                "source": "package.json",
                "confidence": 0.83,
                "risk": "medium",
            }
        )

    if (repo_path / "docker-compose.yml").exists():
        commands.append(
            {
                "id": "docker_compose",
                "command": "docker compose up",
                "purpose": "start compose-defined services",
                "source": "docker-compose.yml",
                "confidence": 0.7,
                "risk": "high",
            }
        )

    return commands

