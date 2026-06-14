import argparse
import os
import sys
from pathlib import Path

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

    parser = argparse.ArgumentParser(description="Run the root single-agent orchestrator.")
    parser.add_argument("prompt_path", nargs="?", help="Prompt file. Defaults to prompts/user_prompt.md.")
    parser.add_argument("--max-steps", type=int, default=None, help="Override ORCH_MAX_STEPS.")
    parser.add_argument(
        "--interactive-user-agent",
        action="store_true",
        help="Read live user directives from stdin while the run is active.",
    )
    parser.add_argument(
        "--user-control-dir",
        type=Path,
        default=None,
        help="Directory containing control/inbox.jsonl or inbox/*.txt live directives.",
    )
    parsed = parser.parse_args(args)

    task = read_user_prompt(parsed.prompt_path)

    max_steps = parsed.max_steps or int(os.getenv("ORCH_MAX_STEPS", "30"))

    result = run_orchestrator(
        task,
        max_steps=max_steps,
        user_control_dir=parsed.user_control_dir,
        interactive_user_agent=parsed.interactive_user_agent,
    )

    print("\n=== FINAL RESULT ===")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
