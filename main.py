import sys

from orchestrator import run_orchestrator
from tools.prompt_loader import read_user_prompt


def main() -> None:
    prompt_path = sys.argv[1] if len(sys.argv) > 1 else None
    task = read_user_prompt(prompt_path)

    result = run_orchestrator(task)

    print("\n=== FINAL RESULT ===")
    print(result)


if __name__ == "__main__":
    main()
