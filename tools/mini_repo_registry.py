from __future__ import annotations

import os
import runpy
import sys
from dataclasses import dataclass
from pathlib import Path

from core.runtime_paths import PROJECT_DIR


@dataclass(frozen=True)
class MiniRepoCommand:
    id: str
    script: Path
    description: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class MiniRepo:
    id: str
    root: Path
    description: str
    default_command: str
    aliases: tuple[str, ...]
    commands: tuple[MiniRepoCommand, ...]


MINI_REPOS: tuple[MiniRepo, ...] = (
    MiniRepo(
        id="business_prompt_lab",
        root=PROJECT_DIR / "business_prompt_lab",
        description="Business prompt experiments and no-code multi-agent answer room.",
        default_command="agent-room",
        aliases=("business", "bpl"),
        commands=(
            MiniRepoCommand(
                id="agent-room",
                script=PROJECT_DIR / "business_prompt_lab" / "agent_room.py",
                description="No-code agent room: coordinator delegates, reviewers challenge, final agent synthesizes.",
                aliases=("agent_room", "room", "talk"),
            ),
            MiniRepoCommand(
                id="benchmark",
                script=PROJECT_DIR / "business_prompt_lab" / "run.py",
                description="Business prompt benchmark runner for cases/prompts.",
                aliases=("prompt-benchmark", "prompt_benchmark", "eval", "run"),
            ),
        ),
    ),
    MiniRepo(
        id="self_eval_qa_lab",
        root=PROJECT_DIR / "experiments" / "self_eval_qa_lab",
        description="Self-evaluating QA lab v0.2 with workflow routing, direct/assisted/deep/repo_debug paths, observer, and lessons.",
        default_command="run",
        aliases=("self-eval", "qa-lab", "selfeval"),
        commands=(
            MiniRepoCommand(
                id="run",
                script=PROJECT_DIR / "experiments" / "self_eval_qa_lab" / "main.py",
                description="Run one self-evaluation answer flow.",
                aliases=("eval", "qa", "answer-flow"),
            ),
        ),
    ),
)


def _matches(value: str, canonical: str, aliases: tuple[str, ...]) -> bool:
    normalized = value.strip().lower().replace("_", "-")
    names = (canonical, *aliases)
    return any(normalized == name.lower().replace("_", "-") for name in names)


def list_mini_repos() -> list[MiniRepo]:
    return list(MINI_REPOS)


def resolve_mini_repo(name: str) -> MiniRepo:
    for repo in MINI_REPOS:
        if _matches(name, repo.id, repo.aliases):
            return repo
    known = ", ".join(repo.id for repo in MINI_REPOS)
    raise KeyError(f"Unknown mini repo {name!r}. Known mini repos: {known}")


def resolve_command(repo: MiniRepo, name: str | None) -> MiniRepoCommand:
    command_name = name or repo.default_command
    for command in repo.commands:
        if _matches(command_name, command.id, command.aliases):
            return command
    known = ", ".join(command.id for command in repo.commands)
    raise KeyError(f"Unknown command {command_name!r} for {repo.id}. Known commands: {known}")


def split_target(target: str) -> tuple[str, str | None]:
    if ":" not in target:
        return target, None
    repo_name, command_name = target.split(":", 1)
    return repo_name, command_name or None


def resolve_lab_invocation(target: str, forwarded_args: list[str]) -> tuple[MiniRepo, MiniRepoCommand, list[str]]:
    repo_name, command_hint = split_target(target)
    repo = resolve_mini_repo(repo_name)
    args = list(forwarded_args)

    if command_hint is None and args:
        try:
            command = resolve_command(repo, args[0])
        except KeyError:
            command = resolve_command(repo, None)
        else:
            args = args[1:]
            return repo, command, args

    return repo, resolve_command(repo, command_hint), args


def _format_lab_list() -> str:
    lines = ["Registered mini repos", ""]
    for repo in MINI_REPOS:
        alias_text = f" (aliases: {', '.join(repo.aliases)})" if repo.aliases else ""
        lines.append(f"- {repo.id}{alias_text}: {repo.description}")
        lines.append(f"  default: {repo.default_command}")
        for command in repo.commands:
            command_aliases = f" [{', '.join(command.aliases)}]" if command.aliases else ""
            rel_script = command.script.relative_to(PROJECT_DIR)
            lines.append(f"  - {command.id}{command_aliases}: {command.description}")
            lines.append(f"    script: {rel_script}")
    lines.extend(
        [
            "",
            "Examples",
            "  python main.py lab list",
            "  python main.py lab business_prompt_lab --mock \"question\"",
            "  python main.py lab business_prompt_lab benchmark --list",
            "  python main.py lab business_prompt_lab:agent-room --dry-run \"question\"",
            "  python main.py lab self_eval_qa_lab --mock \"question\"",
        ]
    )
    return "\n".join(lines)


def print_lab_help() -> None:
    print(
        "\n".join(
            [
                "Usage:",
                "  python main.py lab list",
                "  python main.py lab <mini-repo> [command] [args...]",
                "  python main.py lab run <mini-repo> [command] [args...]",
                "  python main.py lab <mini-repo>:<command> [args...]",
                "",
                _format_lab_list(),
            ]
        )
    )


def run_script(command: MiniRepoCommand, args: list[str]) -> int:
    if not command.script.exists():
        print(f"Mini repo command script not found: {command.script}", file=sys.stderr)
        return 2

    old_argv = sys.argv[:]
    old_cwd = Path.cwd()
    sys.argv = [str(command.script), *args]
    os.chdir(PROJECT_DIR)
    try:
        runpy.run_path(str(command.script), run_name="__main__")
    except SystemExit as exc:
        if exc.code is None:
            return 0
        if isinstance(exc.code, int):
            return exc.code
        print(exc.code, file=sys.stderr)
        return 1
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
    return 0


def run_lab_cli(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print_lab_help()
        return 0

    command = argv[0].lower()
    if command in {"list", "ls"}:
        print(_format_lab_list())
        return 0

    if command in {"run", "exec"}:
        if len(argv) < 2:
            print("Missing mini repo id after 'lab run'.", file=sys.stderr)
            print_lab_help()
            return 2
        target = argv[1]
        forwarded_args = argv[2:]
    else:
        target = argv[0]
        forwarded_args = argv[1:]

    try:
        repo, repo_command, args = resolve_lab_invocation(target, forwarded_args)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"[mini-repo] {repo.id}:{repo_command.id}")
    return run_script(repo_command, args)
