from __future__ import annotations

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
VAR_DIR = Path(os.getenv("AGENT_VAR_DIR", str(PROJECT_DIR / "var"))).resolve()
WORKSPACE_DIR = Path(os.getenv("AGENT_WORKSPACE_DIR", str(VAR_DIR / "workspace"))).resolve()
AGENT_RUNS_DIR = Path(os.getenv("AGENT_RUNS_DIR", str(VAR_DIR / "agent_runs"))).resolve()
TEST_RUNS_DIR = Path(os.getenv("AGENT_TEST_RUNS_DIR", str(VAR_DIR / "test_runs"))).resolve()
QDRANT_STORAGE_DIR = Path(os.getenv("QDRANT_STORAGE_DIR", str(VAR_DIR / "qdrant_storage"))).resolve()


def ensure_runtime_dirs() -> None:
    for path in (VAR_DIR, WORKSPACE_DIR, AGENT_RUNS_DIR, TEST_RUNS_DIR, QDRANT_STORAGE_DIR):
        path.mkdir(parents=True, exist_ok=True)
