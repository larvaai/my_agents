from __future__ import annotations

from core.runtime_paths import PROJECT_DIR


def load_project_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(PROJECT_DIR / ".env", override=False)
