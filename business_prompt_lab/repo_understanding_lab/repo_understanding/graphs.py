from __future__ import annotations

from pathlib import Path
from typing import Any


COMMON_UNRESOLVED_CALLS = {
    "bool",
    "dict",
    "float",
    "int",
    "isinstance",
    "len",
    "list",
    "lower",
    "max",
    "min",
    "open",
    "print",
    "range",
    "set",
    "sorted",
    "str",
    "sum",
    "tuple",
}


def add_edge(edges: list[dict[str, Any]], source: str, target: str, edge_type: str, evidence: dict[str, Any], confidence: float) -> None:
    edges.append(
        {
            "source": source,
            "target": target,
            "type": edge_type,
            "evidence": evidence,
            "confidence": confidence,
        }
    )


def build_symbol_lookup(symbols: list[dict[str, Any]]) -> dict[str, str]:
    names: dict[str, list[str]] = {}
    for symbol in symbols:
        names.setdefault(symbol["name"], []).append(symbol["id"])
        names.setdefault(symbol["qualified_name"], []).append(symbol["id"])
    return {name: ids[0] for name, ids in names.items() if len(ids) == 1}


def resolve_call(call: str, lookup: dict[str, str]) -> str:
    last = call.rsplit(".", 1)[-1]
    if last in COMMON_UNRESOLVED_CALLS:
        return f"call:{call}"
    if call in lookup:
        return lookup[call]
    if last in lookup:
        return lookup[last]
    return f"call:{call}"


def build_graph(file_map: list[dict[str, Any]], symbol_index: dict[str, Any], docs: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    symbols = symbol_index["symbols"]
    lookup = build_symbol_lookup(symbols)

    for file_node in file_map:
        nodes.append({"id": file_node["id"], "kind": "file", "label": file_node["path"]})
    for symbol in symbols:
        nodes.append({"id": symbol["id"], "kind": "symbol", "label": symbol["qualified_name"]})
        add_edge(
            edges,
            f"file:{symbol['file']}",
            symbol["id"],
            "defines",
            {"file": symbol["file"], "line": symbol["line_start"]},
            0.95,
        )

    for file_path, imports in symbol_index["file_imports"].items():
        for imported in imports:
            if not imported:
                continue
            add_edge(
                edges,
                f"file:{file_path}",
                f"module:{imported}",
                "imports",
                {"file": file_path},
                0.8,
            )

    for symbol in symbols:
        for call in symbol.get("calls", []):
            add_edge(
                edges,
                symbol["id"],
                resolve_call(call, lookup),
                "calls",
                {"file": symbol["file"], "line": symbol["line_start"], "call": call},
                0.62,
            )

    for doc in docs:
        doc_text = f"{doc['title']}\n{doc['summary']}\n{doc.get('content', '')}".lower()
        for symbol in symbols:
            if symbol["name"].lower() in doc_text or symbol["qualified_name"].lower() in doc_text:
                add_edge(
                    edges,
                    f"doc:{doc['path']}",
                    symbol["id"],
                    "documents",
                    {"file": doc["path"]},
                    0.55,
                )

    return {"nodes": nodes, "edges": edges}


def build_test_map(file_map: list[dict[str, Any]], symbol_index: dict[str, Any]) -> list[dict[str, Any]]:
    files_by_stem: dict[str, list[dict[str, Any]]] = {}
    for file_node in file_map:
        files_by_stem.setdefault(Path(file_node["path"]).stem.lower(), []).append(file_node)

    symbols_by_file: dict[str, list[str]] = {}
    for symbol in symbol_index["symbols"]:
        symbols_by_file.setdefault(symbol["file"], []).append(symbol["qualified_name"])

    test_items: list[dict[str, Any]] = []
    for file_node in file_map:
        if not file_node["is_test"]:
            continue
        test_stem = Path(file_node["path"]).stem.lower()
        candidates = []
        if test_stem.startswith("test_"):
            candidates.append(test_stem.removeprefix("test_"))
        if test_stem.endswith("_test"):
            candidates.append(test_stem.removesuffix("_test"))

        target_files: set[str] = set()
        target_symbols: set[str] = set()
        for candidate in candidates:
            for target in files_by_stem.get(candidate, []):
                if not target["is_test"]:
                    target_files.add(target["path"])
                    target_symbols.update(symbols_by_file.get(target["path"], []))

        for imported in symbol_index["file_imports"].get(file_node["path"], []):
            import_tail = imported.rsplit(".", 1)[-1].lower()
            for target in files_by_stem.get(import_tail, []):
                if not target["is_test"]:
                    target_files.add(target["path"])
                    target_symbols.update(symbols_by_file.get(target["path"], []))

        test_items.append(
            {
                "test_id": file_node["path"],
                "path": file_node["path"],
                "test_type": "unit",
                "target_files": sorted(target_files),
                "target_symbols": sorted(target_symbols),
                "last_status": "unknown",
                "reason": "matched by test filename and imports" if target_files else "no direct target detected",
            }
        )
    return sorted(test_items, key=lambda item: item["path"])


def build_external_test_map(
    *,
    repo_path: Path,
    project_dir: Path,
    file_map: list[dict[str, Any]],
    symbol_index: dict[str, Any],
) -> list[dict[str, Any]]:
    repo_path = repo_path.resolve()
    project_dir = project_dir.resolve()
    tests_dir = project_dir / "tests"
    if repo_path == project_dir or not tests_dir.exists():
        return []
    try:
        package_name = repo_path.relative_to(project_dir).as_posix().replace("/", ".")
    except ValueError:
        return []

    source_files = [node for node in file_map if node["language"] == "python" and not node["is_test"]]
    symbols_by_file: dict[str, list[str]] = {}
    for symbol in symbol_index["symbols"]:
        symbols_by_file.setdefault(symbol["file"], []).append(symbol["qualified_name"])

    external_tests: list[dict[str, Any]] = []
    for path in sorted(tests_dir.rglob("test*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if package_name not in text:
            continue

        target_files: set[str] = set()
        target_symbols: set[str] = set()
        for node in source_files:
            module_path = f"{package_name}.{Path(node['path']).with_suffix('').as_posix().replace('/', '.')}"
            basename = Path(node["path"]).name
            stem = Path(node["path"]).stem
            if module_path in text or stem in text or basename in text:
                target_files.add(node["path"])
                target_symbols.update(symbols_by_file.get(node["path"], []))

        if not target_files:
            for node in source_files:
                if node["role"] == "entrypoint":
                    target_files.add(node["path"])
                    target_symbols.update(symbols_by_file.get(node["path"], []))

        rel_path = path.relative_to(project_dir).as_posix()
        external_tests.append(
            {
                "test_id": rel_path,
                "path": rel_path,
                "test_type": "external_workspace",
                "target_files": sorted(target_files),
                "target_symbols": sorted(target_symbols),
                "last_status": "unknown",
                "reason": f"external test mentions package {package_name}",
            }
        )
    return external_tests
