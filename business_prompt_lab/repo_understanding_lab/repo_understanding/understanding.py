from __future__ import annotations

import re
from pathlib import Path
from typing import Any


FLOW_ORDER = [
    "run",
    "plan_tasks",
    "tasks_from_plan",
    "run_tasks",
    "review_outputs",
    "followup_tasks",
    "final_synthesis",
    "write_outputs",
]

RUNNER_HINTS = {
    "agent_room.py": "No-code multi-agent room runner.",
    "run.py": "Business prompt benchmark runner.",
    "talk.ps1": "PowerShell wrapper for agent_room.py.",
    "run.ps1": "PowerShell wrapper for prompt benchmark runs.",
    "main.py": "Python entrypoint.",
}


def file_basename(path: str) -> str:
    return path.replace("\\", "/").rsplit("/", 1)[-1]


def extract_artifact_paths_from_text(text: str) -> list[str]:
    patterns = [
        r"var/[A-Za-z0-9_./*<>{}-]+",
        r"[A-Za-z0-9_./-]+/(?:final|transcript|summary)\.(?:md|json)",
        r"[A-Za-z0-9_./-]+/(?:outputs|inputs)/\*\.(?:txt|md|json)",
    ]
    found: set[str] = set()
    for pattern in patterns:
        for match in re.findall(pattern, text):
            found.add(match.rstrip(".,;:"))
    return sorted(found)


def build_doc_hints(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for doc in docs:
        artifacts = extract_artifact_paths_from_text(doc.get("content", ""))
        if artifacts:
            hints.append(
                {
                    "path": doc["path"],
                    "title": doc["title"],
                    "artifact_paths": artifacts,
                }
            )
    return hints


def build_runner_summary(file_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runners: list[dict[str, Any]] = []
    for node in file_map:
        basename = file_basename(node["path"])
        if node["role"] == "entrypoint" or basename in RUNNER_HINTS:
            runners.append(
                {
                    "path": node["path"],
                    "language": node["language"],
                    "role": node["role"],
                    "description": RUNNER_HINTS.get(basename, "Detected entrypoint."),
                }
            )
    return sorted(runners, key=lambda item: (item["path"].count("/"), item["path"]))


def build_agent_room_flow(symbols: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_step: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        if "AgentRoom." not in symbol["qualified_name"]:
            continue
        step = symbol["name"]
        if step in FLOW_ORDER:
            by_step[step] = {
                "step": step,
                "symbol": symbol["qualified_name"],
                "file": symbol["file"],
                "line_start": symbol["line_start"],
                "line_end": symbol["line_end"],
            }
    return [by_step[name] for name in FLOW_ORDER if name in by_step]


def build_repo_flow_summary(
    *,
    file_map: list[dict[str, Any]],
    symbol_index: dict[str, Any],
    docs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "runners": build_runner_summary(file_map),
        "agent_room_flow": build_agent_room_flow(symbol_index["symbols"]),
        "doc_artifact_hints": build_doc_hints(docs),
    }


def build_understanding_report(context_pack: dict[str, Any]) -> dict[str, Any]:
    flow = context_pack.get("repo_flow", {})
    runners = flow.get("runners", [])
    agent_room_flow = flow.get("agent_room_flow", [])
    artifact_hints = flow.get("doc_artifact_hints", [])
    tests = context_pack.get("tests", [])
    relevant_files = context_pack.get("relevant_files", [])
    relevant_symbols = context_pack.get("relevant_symbols", [])
    graph_slice = context_pack.get("graph_slice", [])
    docs_context = context_pack.get("docs_context", [])
    unknowns = context_pack.get("unknowns", [])

    score = 0.0
    score += 0.9 if len(relevant_files) >= 4 else 0.18 * len(relevant_files)
    score += 0.8 if len(relevant_symbols) >= 8 else 0.1 * len(relevant_symbols)
    score += 0.8 if len(graph_slice) >= 8 else 0.1 * len(graph_slice)
    score += 0.7 if len(docs_context) >= 2 else 0.25 * len(docs_context)
    score += 0.7 if runners else 0.0
    score += 0.7 if len(agent_room_flow) >= 5 else 0.11 * len(agent_room_flow)
    score += 0.5 if artifact_hints else 0.0
    score += 0.7 if tests else 0.0
    score -= 0.15 * len(unknowns)
    normalized = max(0.0, min(5.0, score / 1.22))

    strengths = []
    weaknesses = []
    if runners:
        strengths.append("Detected runner/entrypoint files.")
    else:
        weaknesses.append("Did not identify runners.")
    if len(agent_room_flow) >= 5:
        strengths.append("Recovered the main AgentRoom method flow.")
    else:
        weaknesses.append("AgentRoom flow is incomplete.")
    if artifact_hints:
        strengths.append("Recovered output artifact paths from docs.")
    else:
        weaknesses.append("Did not recover output artifact paths.")
    if tests:
        strengths.append("Mapped at least one related test.")
    else:
        weaknesses.append("No related tests were mapped.")
    if unknowns:
        weaknesses.extend(unknowns)

    if normalized >= 4.2:
        level = "level_4_strong_repo_flow"
    elif normalized >= 3.2:
        level = "level_3_useful_static_understanding"
    elif normalized >= 2.0:
        level = "level_2_partial_indexing"
    else:
        level = "level_1_surface_scan"

    return {
        "score_5": round(normalized, 2),
        "level": level,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "coverage": {
            "relevant_files": len(relevant_files),
            "relevant_symbols": len(relevant_symbols),
            "graph_edges": len(graph_slice),
            "docs": len(docs_context),
            "runners": len(runners),
            "agent_room_flow_steps": len(agent_room_flow),
            "artifact_docs": len(artifact_hints),
            "tests": len(tests),
            "unknowns": len(unknowns),
        },
    }
