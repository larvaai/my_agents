from __future__ import annotations

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


def _load_project_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(PROJECT_DIR / ".env", override=False)


_load_project_env()


def _resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_DIR / path
    return path.resolve()


def _path_env(name: str, default: Path) -> Path:
    return _resolve_project_path(os.getenv(name, str(default)))


VAR_DIR = _path_env("AGENT_VAR_DIR", PROJECT_DIR / "var")
WORKSPACE_DIR = _path_env("AGENT_WORKSPACE_DIR", VAR_DIR / "workspace")
AGENT_RUNS_DIR = _path_env("AGENT_RUNS_DIR", VAR_DIR / "agent_runs")
TEST_RUNS_DIR = _path_env("AGENT_TEST_RUNS_DIR", VAR_DIR / "test_runs")
QDRANT_STORAGE_DIR = _path_env("QDRANT_STORAGE_DIR", VAR_DIR / "qdrant_storage")


def ensure_runtime_dirs() -> None:
    for path in (VAR_DIR, WORKSPACE_DIR, AGENT_RUNS_DIR, TEST_RUNS_DIR, QDRANT_STORAGE_DIR):
        path.mkdir(parents=True, exist_ok=True)
