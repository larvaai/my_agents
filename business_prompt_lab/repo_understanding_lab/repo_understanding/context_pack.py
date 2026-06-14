from __future__ import annotations

import re
from typing import Any


STOPWORDS = {
    "about",
    "after",
    "agent",
    "call",
    "calls",
    "code",
    "co",
    "dau",
    "doc",
    "does",
    "file",
    "from",
    "have",
    "hieu",
    "how",
    "impact",
    "into",
    "lien",
    "nam",
    "nao",
    "nay",
    "nhung",
    "repo",
    "sao",
    "test",
    "that",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
    "work",
    "works",
}

FILE_HINTS = {
    "artifact": {"README.md", "NO_CODE_AGENT_FLOW.md", "agent_room.py", "run.py"},
    "artifacts": {"README.md", "NO_CODE_AGENT_FLOW.md", "agent_room.py", "run.py"},
    "benchmark": {"run.py", "README.md"},
    "output": {"README.md", "NO_CODE_AGENT_FLOW.md", "agent_room.py", "run.py"},
    "outputs": {"README.md", "NO_CODE_AGENT_FLOW.md", "agent_room.py", "run.py"},
    "prompt": {"run.py", "README.md"},
    "prompts": {"run.py", "README.md"},
    "room": {"agent_room.py", "NO_CODE_AGENT_FLOW.md", "README.md", "talk.ps1"},
    "run": {"run.py", "agent_room.py", "run.ps1", "talk.ps1", "README.md"},
    "runner": {"run.py", "agent_room.py", "run.ps1", "talk.ps1", "README.md"},
    "runners": {"run.py", "agent_room.py", "run.ps1", "talk.ps1", "README.md"},
    "chay": {"run.py", "agent_room.py", "run.ps1", "talk.ps1", "README.md"},
}


def classify_question(question: str) -> str:
    lowered = question.lower()
    if any(word in lowered for word in ("impact", "change", "break", "risk", "blast")):
        return "impact_analysis"
    if any(word in lowered for word in ("test", "verify", "validation")):
        return "test_selection"
    if any(word in lowered for word in ("entrypoint", "run", "runtime", "start")):
        return "runtime_question"
    if re.search(r"[A-Z][A-Za-z]+|\w+\.py", question):
        return "symbol_question"
    return "architecture_question"


def extract_entities(question: str, forced_entities: list[str] | None = None) -> list[str]:
    entities: set[str] = set(forced_entities or [])
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_./-]*", question):
        normalized = token.strip("./")
        if not normalized:
            continue
        if normalized.lower() in STOPWORDS:
            continue
        if len(normalized) >= 4 or "." in normalized or "_" in normalized or any(char.isupper() for char in normalized):
            entities.add(normalized)
    return sorted(entities)


def token_match(value: str, entities: list[str]) -> bool:
    lowered = value.lower()
    return any(entity.lower() in lowered for entity in entities)


def select_files(file_map: list[dict[str, Any]], entities: list[str], limit: int = 12) -> list[dict[str, Any]]:
    path_entities = {entity.lower() for entity in entities if "." in entity or "/" in entity}
    exact_path_entities = {
        entity for entity in path_entities if any(node["path"].lower() == entity for node in file_map)
    }
    scored = []
    for node in file_map:
        path = node["path"].lower()
        basename = path.rsplit("/", 1)[-1]
        score = None
        for entity in entities:
            lowered = entity.lower()
            hint_paths = {hint.lower() for hint in FILE_HINTS.get(lowered, set())}
            if hint_paths and (node["path"] in FILE_HINTS[lowered] or basename in hint_paths):
                hint_score = 0 if node["role"] == "entrypoint" else 1
                score = hint_score if score is None else min(score, hint_score)
                continue
            if path == lowered:
                score = 0 if score is None else min(score, 0)
            elif basename == lowered:
                if lowered in exact_path_entities:
                    continue
                score = 1 if score is None else min(score, 1)
            elif lowered in path:
                score = 2 if score is None else min(score, 2)
        if score is not None:
            scored.append((score, node["role"] != "entrypoint", node["path"], node))
    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    selected = [item[3] for item in scored]
    if not selected:
        selected = [node for node in file_map if node["role"] in {"entrypoint", "manifest"}]
    root_docs = [
        node
        for node in file_map
        if node["role"] == "docs" and "/" not in node["path"] and node["path"] not in {item["path"] for item in selected}
    ]
    selected.extend(root_docs[:3])
    return selected[:limit]


def symbol_kind_priority(symbol: dict[str, Any]) -> int:
    if symbol["kind"] == "function" and not symbol["name"].startswith("_"):
        return 0
    if symbol["kind"] in {"class", "method"} and not symbol["name"].startswith("_"):
        return 1
    if symbol["kind"] == "function":
        return 2
    if symbol["kind"] == "constant":
        return 3
    return 4


def symbol_match_score(
    symbol: dict[str, Any],
    entities: list[str],
    selected_file_paths: set[str],
    exact_path_entities: set[str],
) -> int | None:
    qualified = symbol["qualified_name"].lower()
    name = symbol["name"].lower()
    file_path = symbol["file"].lower()
    file_name = file_path.rsplit("/", 1)[-1]
    file_stem = file_name.rsplit(".", 1)[0]
    best: int | None = None
    for entity in entities:
        raw_lowered = entity.lower()
        lowered = raw_lowered.removesuffix(".py")
        if not lowered:
            continue
        if "." in raw_lowered or "/" in raw_lowered:
            if file_path == raw_lowered:
                path_score = 0 if name == lowered else 1
                best = path_score if best is None else min(best, path_score)
            elif file_name == raw_lowered:
                if raw_lowered in exact_path_entities:
                    continue
                path_score = 1 if name == lowered else 2
                best = path_score if best is None else min(best, path_score)
            continue
        if qualified == lowered or name == lowered:
            best = 0 if best is None else min(best, 0)
        elif qualified.startswith(f"{lowered}.") or file_stem == lowered:
            module_score = 0 if lowered in name else 1
            best = module_score if best is None else min(best, module_score)
        elif lowered in qualified:
            best = 2 if best is None else min(best, 2)
    if symbol["file"] in selected_file_paths:
        best = 1 if best is None else min(best, 1)
    return best


def select_symbols(
    symbols: list[dict[str, Any]],
    entities: list[str],
    selected_files: list[dict[str, Any]],
    all_files: list[dict[str, Any]],
    limit: int = 20,
) -> list[dict[str, Any]]:
    selected_file_paths = {node["path"] for node in selected_files}
    path_entities = {entity.lower() for entity in entities if "." in entity or "/" in entity}
    exact_path_entities = {
        entity for entity in path_entities if any(node["path"].lower() == entity for node in all_files)
    }
    selected = []
    for symbol in symbols:
        score = symbol_match_score(symbol, entities, selected_file_paths, exact_path_entities)
        if score is not None:
            selected.append((score, symbol_kind_priority(symbol), symbol["qualified_name"], symbol))
    selected.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in selected[:limit]]


def merge_symbol_files(
    file_map: list[dict[str, Any]],
    selected_files: list[dict[str, Any]],
    selected_symbols: list[dict[str, Any]],
    limit: int = 12,
) -> list[dict[str, Any]]:
    by_path = {node["path"]: node for node in file_map}
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in selected_files:
        merged.append(node)
        seen.add(node["path"])
    for symbol in selected_symbols:
        node = by_path.get(symbol["file"])
        if node and node["path"] not in seen:
            merged.append(node)
            seen.add(node["path"])
    return merged[:limit]


def select_graph_edges(graph: dict[str, Any], selected_files: list[dict[str, Any]], selected_symbols: list[dict[str, Any]], limit: int = 40) -> list[dict[str, Any]]:
    file_ids = {node["id"] for node in selected_files}
    symbol_ids = {symbol["id"] for symbol in selected_symbols}
    symbol_rank = {symbol["id"]: index for index, symbol in enumerate(selected_symbols)}
    if symbol_ids:
        edges = [
            edge
            for edge in graph["edges"]
            if edge["source"] in symbol_ids
            or edge["target"] in symbol_ids
            or (edge["type"] == "defines" and edge["target"] in symbol_ids)
        ]
    else:
        edges = [edge for edge in graph["edges"] if edge["source"] in file_ids or edge["target"] in file_ids]
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge["source"], edge["target"], edge["type"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(edge)
    edge_priority = {"calls": 0, "imports": 1, "defines": 2, "documents": 3}
    def selected_rank(edge: dict[str, Any]) -> int:
        ranks = [
            symbol_rank[value]
            for value in (edge["source"], edge["target"])
            if value in symbol_rank
        ]
        return min(ranks) if ranks else 9999

    unique.sort(key=lambda edge: (selected_rank(edge), edge_priority.get(edge["type"], 9), edge["source"], edge["target"]))
    return unique[:limit]


def select_docs(docs: list[dict[str, Any]], entities: list[str], limit: int = 8) -> list[dict[str, Any]]:
    scored = []
    for doc in docs:
        text = f"{doc['path']} {doc['title']} {doc['summary']}"
        if token_match(text, entities):
            score = 0
        elif "/" not in doc["path"]:
            score = 1
        else:
            continue
        scored.append((score, doc["path"], {"path": doc["path"], "title": doc["title"], "summary": doc["summary"]}))
    scored.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in scored[:limit]]


def select_tests(test_map: list[dict[str, Any]], selected_files: list[dict[str, Any]], selected_symbols: list[dict[str, Any]]) -> list[dict[str, Any]]:
    file_paths = {node["path"] for node in selected_files}
    symbol_names = {symbol["qualified_name"] for symbol in selected_symbols}
    selected = []
    for test in test_map:
        if file_paths.intersection(test["target_files"]) or symbol_names.intersection(test["target_symbols"]):
            selected.append(test)
    return selected[:12]


def build_context_pack(
    *,
    question: str,
    repo_profile: dict[str, Any],
    file_map: list[dict[str, Any]],
    symbol_index: dict[str, Any],
    graph: dict[str, Any],
    docs: list[dict[str, Any]],
    test_map: list[dict[str, Any]],
    runtime_map: list[dict[str, Any]],
    forced_entities: list[str] | None = None,
) -> dict[str, Any]:
    intent = classify_question(question)
    entities = extract_entities(question, forced_entities=forced_entities)
    selected_files = select_files(file_map, entities)
    selected_symbols = select_symbols(symbol_index["symbols"], entities, selected_files, file_map)
    selected_files = merge_symbol_files(file_map, selected_files, selected_symbols)
    graph_slice = select_graph_edges(graph, selected_files, selected_symbols)
    selected_tests = select_tests(test_map, selected_files, selected_symbols)
    selected_docs = select_docs(docs, entities)
    unknowns = []
    if not selected_symbols and intent == "symbol_question":
        unknowns.append("No matching symbol was found; answer must stay at file/runtime level.")
    if not selected_tests:
        unknowns.append("No direct tests were mapped for the selected files or symbols.")
    if symbol_index.get("parse_errors"):
        unknowns.append("Some Python files failed to parse; symbol graph may be incomplete.")

    return {
        "task": {
            "user_request": question,
            "intent": intent,
            "success_criteria": ["cite files/symbols", "name tests or state tests are missing"],
        },
        "entities": entities,
        "repo_profile": {
            "languages": repo_profile["languages"],
            "frameworks": repo_profile["frameworks"],
            "entrypoints": repo_profile["entrypoints"],
        },
        "relevant_files": selected_files,
        "relevant_symbols": selected_symbols,
        "graph_slice": graph_slice,
        "docs_context": selected_docs,
        "tests": selected_tests,
        "runtime_commands": runtime_map,
        "ledger_lessons": [],
        "known_risks": [],
        "unknowns": unknowns,
    }


def generate_answer(context_pack: dict[str, Any]) -> str:
    lines = [
        "# Evidence-Based Repo Answer",
        "",
        f"Question: {context_pack['task']['user_request']}",
        f"Intent: `{context_pack['task']['intent']}`",
        "",
        "## Direct Answer",
    ]
    if context_pack["relevant_symbols"]:
        primary = context_pack["relevant_symbols"][0]
        lines.append(
            f"The strongest code evidence points to `{primary['qualified_name']}` in `{primary['file']}`."
        )
    elif context_pack["relevant_files"]:
        primary_file = context_pack["relevant_files"][0]
        lines.append(f"The strongest file-level evidence points to `{primary_file['path']}`.")
    else:
        lines.append("No strong code evidence was found in the current maps.")

    if context_pack["repo_profile"]["entrypoints"]:
        entrypoints = ", ".join(f"`{item}`" for item in context_pack["repo_profile"]["entrypoints"])
        lines.append(f"Detected entrypoint evidence: {entrypoints}.")

    lines.extend(["", "## Relevant Files"])
    for file_node in context_pack["relevant_files"] or []:
        lines.append(f"- `{file_node['path']}` ({file_node['role']}, {file_node['language']})")

    lines.extend(["", "## Relevant Symbols"])
    for symbol in context_pack["relevant_symbols"] or []:
        lines.append(f"- `{symbol['qualified_name']}` in `{symbol['file']}` lines {symbol['line_start']}-{symbol['line_end']}")

    lines.extend(["", "## Graph Evidence"])
    for edge in context_pack["graph_slice"][:12]:
        lines.append(f"- `{edge['source']}` --{edge['type']}--> `{edge['target']}`")

    lines.extend(["", "## Tests"])
    if context_pack["tests"]:
        for test in context_pack["tests"]:
            targets = ", ".join(f"`{item}`" for item in test["target_files"]) or "no direct target"
            lines.append(f"- `{test['path']}` -> {targets}")
    else:
        lines.append("- No direct tests were mapped for this context.")

    lines.extend(["", "## Unknowns"])
    for unknown in context_pack["unknowns"] or ["No major unknown recorded by the context pack."]:
        lines.append(f"- {unknown}")

    lines.extend(["", "## Suggested Next Checks"])
    for command in context_pack["runtime_commands"][:3]:
        lines.append(f"- `{command['command']}` ({command['purpose']})")
    return "\n".join(lines) + "\n"


def generate_impact_answer(context_pack: dict[str, Any], target: str) -> str:
    lines = [
        "# Impact Analysis",
        "",
        f"Target: `{target}`",
        "",
        "## Likely Blast Radius",
    ]
    if context_pack["graph_slice"]:
        for edge in context_pack["graph_slice"][:18]:
            lines.append(f"- `{edge['source']}` --{edge['type']}--> `{edge['target']}`")
    else:
        lines.append("- No graph edges matched the target; impact confidence is low.")

    lines.extend(["", "## Files To Inspect"])
    for file_node in context_pack["relevant_files"]:
        lines.append(f"- `{file_node['path']}`")

    lines.extend(["", "## Tests To Run"])
    if context_pack["tests"]:
        for test in context_pack["tests"]:
            lines.append(f"- `{test['path']}`")
    else:
        lines.append("- No mapped tests found; add or locate tests before patching.")

    lines.extend(["", "## Validation Commands"])
    for command in context_pack["runtime_commands"][:3]:
        lines.append(f"- `{command['command']}`")

    lines.extend(["", "## Caveats"])
    for unknown in context_pack["unknowns"] or ["Impact analysis uses static evidence only."]:
        lines.append(f"- {unknown}")
    return "\n".join(lines) + "\n"
