from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parent
PROJECT_DIR = LAB_DIR.parents[1]
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from repo_understanding.context_pack import (  # noqa: E402
    build_context_pack,
    generate_answer,
    generate_impact_answer,
)
from repo_understanding.docs_reader import read_docs  # noqa: E402
from repo_understanding.graphs import build_graph, build_test_map  # noqa: E402
from repo_understanding.graphs import build_external_test_map  # noqa: E402
from repo_understanding.io_utils import (  # noqa: E402
    append_jsonl,
    make_run_id,
    write_json,
    write_text,
)
from repo_understanding.manifests import read_manifests  # noqa: E402
from repo_understanding.observer import observe_answer  # noqa: E402
from repo_understanding.runtime import infer_runtime_commands  # noqa: E402
from repo_understanding.scanner import scan_repo  # noqa: E402
from repo_understanding.symbols import extract_python_symbols  # noqa: E402


KNOWN_COMMANDS = {"baseline", "ask", "impact"}
VALUE_OPTIONS = {"--repo", "--out-dir", "--limit-files"}
FLAG_OPTIONS = {"--mock"}


def fixture_repo_path() -> Path:
    return LAB_DIR / "fixtures" / "tiny_python_repo"


def default_out_dir() -> Path:
    return PROJECT_DIR / "var" / "repo_understanding_lab" / make_run_id()


def hoist_global_options(argv: list[str]) -> list[str]:
    globals_: list[str] = []
    rest: list[str] = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in FLAG_OPTIONS:
            globals_.append(arg)
            index += 1
            continue
        if arg in VALUE_OPTIONS:
            globals_.append(arg)
            if index + 1 < len(argv):
                globals_.append(argv[index + 1])
                index += 2
            else:
                index += 1
            continue
        rest.append(arg)
        index += 1
    return globals_ + rest


def normalize_argv(argv: list[str]) -> list[str]:
    args = hoist_global_options(argv)
    first_positional_index = None
    skip_next = False
    for index, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if arg in VALUE_OPTIONS:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        first_positional_index = index
        break
    if first_positional_index is None:
        return [*args, "baseline"]
    if args[first_positional_index] in KNOWN_COMMANDS:
        return args
    return [*args[:first_positional_index], "ask", *args[first_positional_index:]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Repo Understanding Lab: build repo maps and answer with evidence."
    )
    parser.add_argument("--mock", action="store_true", help="Use the tiny fixture repo.")
    parser.add_argument("--repo", type=Path, default=None, help="Repository path to inspect.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Exact output run directory.")
    parser.add_argument("--limit-files", type=int, default=None, help="Limit scanned files.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("baseline", help="Build repo maps and a baseline summary.")

    ask = subparsers.add_parser("ask", help="Answer a repo question with evidence.")
    ask.add_argument("question", nargs=argparse.REMAINDER)

    impact = subparsers.add_parser("impact", help="Analyze impact for a file or symbol.")
    impact.add_argument("target", nargs=argparse.REMAINDER)

    return parser


def resolve_repo_path(args: argparse.Namespace) -> Path:
    if args.mock:
        return fixture_repo_path()
    if args.repo is not None:
        return args.repo.resolve()
    return PROJECT_DIR


def run_baseline(repo_path: Path, out_dir: Path, limit_files: int | None = None) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    maps_dir = out_dir / "maps"
    reports_dir = out_dir / "reports"
    maps_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    transcript = out_dir / "transcript.jsonl"
    append_jsonl(
        transcript,
        {
            "event": "run_started",
            "command": "baseline",
            "repo_path": str(repo_path),
            "out_dir": str(out_dir),
        },
    )

    file_map = scan_repo(repo_path, limit_files=limit_files)
    write_json(maps_dir / "file_map.json", file_map)
    append_jsonl(transcript, {"event": "map_written", "name": "file_map", "count": len(file_map)})

    repo_profile = read_manifests(repo_path, file_map)
    write_json(maps_dir / "repo_profile.json", repo_profile)
    append_jsonl(transcript, {"event": "map_written", "name": "repo_profile"})

    docs = read_docs(repo_path, file_map)
    write_json(maps_dir / "docs_map.json", docs)
    append_jsonl(transcript, {"event": "map_written", "name": "docs_map", "count": len(docs)})

    symbol_index = extract_python_symbols(repo_path, file_map)
    write_json(maps_dir / "symbol_map.json", symbol_index)
    append_jsonl(
        transcript,
        {
            "event": "map_written",
            "name": "symbol_map",
            "count": len(symbol_index["symbols"]),
            "parse_errors": len(symbol_index["parse_errors"]),
        },
    )

    graph = build_graph(file_map, symbol_index, docs)
    write_json(maps_dir / "dependency_graph.json", graph)
    append_jsonl(transcript, {"event": "map_written", "name": "dependency_graph", "edges": len(graph["edges"])})

    test_map = build_test_map(file_map, symbol_index)
    test_map.extend(
        build_external_test_map(
            repo_path=repo_path,
            project_dir=PROJECT_DIR,
            file_map=file_map,
            symbol_index=symbol_index,
        )
    )
    write_json(maps_dir / "test_map.json", test_map)
    append_jsonl(transcript, {"event": "map_written", "name": "test_map", "count": len(test_map)})

    runtime_map = infer_runtime_commands(repo_path, repo_profile, file_map)
    write_json(maps_dir / "runtime_map.json", runtime_map)
    append_jsonl(transcript, {"event": "map_written", "name": "runtime_map", "count": len(runtime_map)})

    summary = build_baseline_summary(repo_path, file_map, repo_profile, symbol_index, graph, test_map, runtime_map)
    write_json(out_dir / "summary.json", summary)
    write_text(out_dir / "summary.md", render_baseline_summary(summary))
    baseline = {
        "repo_path": str(repo_path),
        "out_dir": str(out_dir),
        "file_map": file_map,
        "repo_profile": repo_profile,
        "docs": docs,
        "symbol_index": symbol_index,
        "graph": graph,
        "test_map": test_map,
        "runtime_map": runtime_map,
        "summary": summary,
    }
    write_admin_trace(out_dir=out_dir, command="baseline", repo_path=repo_path, baseline=baseline)
    append_jsonl(transcript, {"event": "run_finished", "status": "baseline_complete"})
    return baseline


def build_baseline_summary(
    repo_path: Path,
    file_map: list[dict[str, Any]],
    repo_profile: dict[str, Any],
    symbol_index: dict[str, Any],
    graph: dict[str, Any],
    test_map: list[dict[str, Any]],
    runtime_map: list[dict[str, Any]],
) -> dict[str, Any]:
    role_counts: dict[str, int] = {}
    for file_node in file_map:
        role_counts[file_node["role"]] = role_counts.get(file_node["role"], 0) + 1
    return {
        "repo_path": str(repo_path),
        "languages": repo_profile["languages"],
        "frameworks": repo_profile["frameworks"],
        "file_count": len(file_map),
        "role_counts": dict(sorted(role_counts.items())),
        "symbol_count": len(symbol_index["symbols"]),
        "edge_count": len(graph["edges"]),
        "test_count": len(test_map),
        "runtime_commands": runtime_map,
        "entrypoints": repo_profile["entrypoints"],
        "parse_errors": symbol_index["parse_errors"],
    }


def render_baseline_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Repo Understanding Baseline",
        "",
        f"Repo: `{summary['repo_path']}`",
        f"Files scanned: {summary['file_count']}",
        f"Symbols extracted: {summary['symbol_count']}",
        f"Graph edges: {summary['edge_count']}",
        f"Tests mapped: {summary['test_count']}",
        "",
        "## Languages",
    ]
    for language in summary["languages"]:
        lines.append(f"- {language}")
    lines.extend(["", "## Entry Points"])
    for entrypoint in summary["entrypoints"] or ["No entrypoint detected"]:
        lines.append(f"- `{entrypoint}`")
    lines.extend(["", "## Runtime Commands"])
    for command in summary["runtime_commands"]:
        lines.append(f"- `{command['command']}`: {command['purpose']} ({command['confidence']:.2f})")
    lines.extend(["", "## File Roles"])
    for role, count in summary["role_counts"].items():
        lines.append(f"- {role}: {count}")
    if summary["parse_errors"]:
        lines.extend(["", "## Parse Errors"])
        for error in summary["parse_errors"]:
            lines.append(f"- `{error['path']}`: {error['error']}")
    return "\n".join(lines) + "\n"


def write_admin_trace(
    *,
    out_dir: Path,
    command: str,
    repo_path: Path,
    baseline: dict[str, Any],
    context_pack: dict[str, Any] | None = None,
    final_answer: str | None = None,
    observer_report: dict[str, Any] | None = None,
) -> None:
    trace = {
        "trace_type": "observable_full_trace",
        "note": (
            "This file contains complete observable tool/runtime data for the lab run: "
            "inputs, maps, selected context, final answer, and observer report. "
            "It does not contain private hidden chain-of-thought."
        ),
        "command": command,
        "repo_path": str(repo_path),
        "out_dir": str(out_dir),
        "maps": {
            "repo_profile": baseline["repo_profile"],
            "file_map": baseline["file_map"],
            "docs_map": baseline["docs"],
            "symbol_map": baseline["symbol_index"],
            "dependency_graph": baseline["graph"],
            "test_map": baseline["test_map"],
            "runtime_map": baseline["runtime_map"],
        },
        "context_pack": context_pack,
        "final_answer": final_answer,
        "observer_report": observer_report,
        "summary": baseline.get("summary"),
    }
    write_json(out_dir / "admin" / "full_trace.json", trace)


def run_ask(
    repo_path: Path,
    out_dir: Path,
    question: str,
    limit_files: int | None = None,
) -> dict[str, Any]:
    baseline = run_baseline(repo_path, out_dir, limit_files=limit_files)
    context_dir = out_dir / "context"
    reports_dir = out_dir / "reports"
    context_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    context_pack = build_context_pack(
        question=question,
        repo_profile=baseline["repo_profile"],
        file_map=baseline["file_map"],
        symbol_index=baseline["symbol_index"],
        graph=baseline["graph"],
        docs=baseline["docs"],
        test_map=baseline["test_map"],
        runtime_map=baseline["runtime_map"],
    )
    write_json(context_dir / "context_pack.json", context_pack)

    final_answer = generate_answer(context_pack)
    write_text(out_dir / "final_answer.md", final_answer)

    observer_report = observe_answer(context_pack, final_answer)
    write_json(reports_dir / "observer_report.json", observer_report)
    write_json(reports_dir / "understanding_report.json", context_pack["understanding_report"])

    summary = {
        "repo_path": str(repo_path),
        "question": question,
        "intent": context_pack["task"]["intent"],
        "out_dir": str(out_dir),
        "context_file_count": len(context_pack["relevant_files"]),
        "context_symbol_count": len(context_pack["relevant_symbols"]),
        "observer_overall": observer_report["scores"]["overall"],
        "understanding_score_5": context_pack["understanding_report"]["score_5"],
        "understanding_level": context_pack["understanding_report"]["level"],
        "verdict": observer_report["verdict"],
    }
    write_json(out_dir / "summary.json", summary)
    write_admin_trace(
        out_dir=out_dir,
        command="ask",
        repo_path=repo_path,
        baseline=baseline,
        context_pack=context_pack,
        final_answer=final_answer,
        observer_report=observer_report,
    )
    append_jsonl(
        out_dir / "transcript.jsonl",
        {
            "event": "run_finished",
            "status": "ask_complete",
            "question": question,
            "observer_overall": observer_report["scores"]["overall"],
        },
    )
    return {
        **baseline,
        "context_pack": context_pack,
        "final_answer": final_answer,
        "observer_report": observer_report,
        "summary": summary,
    }


def run_impact(
    repo_path: Path,
    out_dir: Path,
    target: str,
    limit_files: int | None = None,
) -> dict[str, Any]:
    baseline = run_baseline(repo_path, out_dir, limit_files=limit_files)
    question = f"What is the impact of changing {target}?"
    context_pack = build_context_pack(
        question=question,
        repo_profile=baseline["repo_profile"],
        file_map=baseline["file_map"],
        symbol_index=baseline["symbol_index"],
        graph=baseline["graph"],
        docs=baseline["docs"],
        test_map=baseline["test_map"],
        runtime_map=baseline["runtime_map"],
        forced_entities=[target],
    )
    context_dir = out_dir / "context"
    reports_dir = out_dir / "reports"
    context_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(context_dir / "context_pack.json", context_pack)

    final_answer = generate_impact_answer(context_pack, target)
    write_text(out_dir / "final_answer.md", final_answer)
    observer_report = observe_answer(context_pack, final_answer)
    write_json(reports_dir / "observer_report.json", observer_report)
    write_json(reports_dir / "understanding_report.json", context_pack["understanding_report"])
    summary = {
        "repo_path": str(repo_path),
        "target": target,
        "out_dir": str(out_dir),
        "observer_overall": observer_report["scores"]["overall"],
        "understanding_score_5": context_pack["understanding_report"]["score_5"],
        "understanding_level": context_pack["understanding_report"]["level"],
        "verdict": observer_report["verdict"],
    }
    write_json(out_dir / "summary.json", summary)
    write_admin_trace(
        out_dir=out_dir,
        command="impact",
        repo_path=repo_path,
        baseline=baseline,
        context_pack=context_pack,
        final_answer=final_answer,
        observer_report=observer_report,
    )
    append_jsonl(out_dir / "transcript.jsonl", {"event": "run_finished", "status": "impact_complete", "target": target})
    return {
        **baseline,
        "context_pack": context_pack,
        "final_answer": final_answer,
        "observer_report": observer_report,
        "summary": summary,
    }


def run(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(normalize_argv(raw_args))
    repo_path = resolve_repo_path(args)
    out_dir = (args.out_dir or default_out_dir()).resolve()

    if args.command == "baseline":
        result = run_baseline(repo_path, out_dir, limit_files=args.limit_files)
        print(f"Run directory: {result['out_dir']}")
        print(f"Summary: {out_dir / 'summary.md'}")
        return 0

    if args.command == "ask":
        question = " ".join(args.question).strip() or "What are the repo entrypoints?"
        result = run_ask(repo_path, out_dir, question, limit_files=args.limit_files)
        print(f"Run directory: {result['summary']['out_dir']}")
        print(f"Context: {out_dir / 'context' / 'context_pack.json'}")
        print(f"Observer: {out_dir / 'reports' / 'observer_report.json'}")
        print("\n=== FINAL ANSWER ===")
        print(result["final_answer"])
        return 0

    if args.command == "impact":
        target = " ".join(args.target).strip()
        if not target:
            print("Missing impact target.", file=sys.stderr)
            return 2
        result = run_impact(repo_path, out_dir, target, limit_files=args.limit_files)
        print(f"Run directory: {result['summary']['out_dir']}")
        print("\n=== IMPACT ANSWER ===")
        print(result["final_answer"])
        return 0

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(run())
