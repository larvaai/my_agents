import os
import sys

from orchestrator import run_orchestrator
from tools.prompt_loader import read_user_prompt


LAB_ENTRYPOINTS = {"lab", "labs", "mini", "mini-repo", "mini-repos"}


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


def main(argv: list[str] | None = None) -> int:
    configure_console_encoding()

    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0].lower() in LAB_ENTRYPOINTS:
        from tools.mini_repo_registry import run_lab_cli

        return run_lab_cli(args[1:])

    prompt_path = args[0] if args else None
    task = read_user_prompt(prompt_path)

    max_steps = int(os.getenv("ORCH_MAX_STEPS", "30"))

    result = run_orchestrator(
        task,
        max_steps=max_steps,
    )

    print("\n=== FINAL RESULT ===")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
