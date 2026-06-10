import os
import sys

from orchestrator import run_orchestrator
from tools.prompt_loader import read_user_prompt


def configure_console_encoding() -> None:
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> None:
    configure_console_encoding()

    prompt_path = sys.argv[1] if len(sys.argv) > 1 else None
    task = read_user_prompt(prompt_path)

    max_steps = int(os.getenv("ORCH_MAX_STEPS", "30"))

    result = run_orchestrator(
        task,
        max_steps=max_steps,
    )

    print("\n=== FINAL RESULT ===")
    print(result)


if __name__ == "__main__":
    main()