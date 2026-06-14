from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def module_name_from_path(path: str) -> str:
    rel = Path(path)
    without_suffix = rel.with_suffix("")
    return ".".join(without_suffix.parts)


def format_args(args: ast.arguments) -> str:
    parts = [arg.arg for arg in args.posonlyargs + args.args]
    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    parts.extend(arg.arg for arg in args.kwonlyargs)
    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")
    return ", ".join(parts)


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
        return node.attr
    if isinstance(node, ast.Call):
        return call_name(node.func)
    return None


def extract_imports(tree: ast.AST) -> list[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = "." * node.level + module
            imports.add(module)
    return sorted(imports)


def extract_calls(node: ast.AST) -> list[str]:
    calls: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = call_name(child.func)
            if name:
                calls.add(name)
    return sorted(calls)


def function_signature(name: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    return f"{name}({format_args(node.args)})"


def symbol_node(
    *,
    name: str,
    qualified_name: str,
    kind: str,
    file_path: str,
    node: ast.AST,
    signature: str,
    calls: list[str],
) -> dict[str, Any]:
    return {
        "id": f"symbol:{qualified_name}",
        "name": name,
        "qualified_name": qualified_name,
        "kind": kind,
        "file": file_path,
        "line_start": getattr(node, "lineno", None),
        "line_end": getattr(node, "end_lineno", getattr(node, "lineno", None)),
        "signature": signature,
        "docstring": ast.get_docstring(node) if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) else "",
        "calls": calls,
        "confidence": 0.9,
    }


def extract_file_symbols(repo_path: Path, file_node: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    path = repo_path / file_node["path"]
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=file_node["path"])
    module_name = module_name_from_path(file_node["path"])
    symbols: list[dict[str, Any]] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            qualified = f"{module_name}.{node.name}"
            symbols.append(
                symbol_node(
                    name=node.name,
                    qualified_name=qualified,
                    kind="class",
                    file_path=file_node["path"],
                    node=node,
                    signature=f"class {node.name}",
                    calls=extract_calls(node),
                )
            )
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_qualified = f"{qualified}.{child.name}"
                    symbols.append(
                        symbol_node(
                            name=child.name,
                            qualified_name=method_qualified,
                            kind="method",
                            file_path=file_node["path"],
                            node=child,
                            signature=function_signature(child.name, child),
                            calls=extract_calls(child),
                        )
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qualified = f"{module_name}.{node.name}"
            symbols.append(
                symbol_node(
                    name=node.name,
                    qualified_name=qualified,
                    kind="function",
                    file_path=file_node["path"],
                    node=node,
                    signature=function_signature(node.name, node),
                    calls=extract_calls(node),
                )
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: list[str] = []
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        targets.append(target.id)
            elif isinstance(node.target, ast.Name) and node.target.id.isupper():
                targets.append(node.target.id)
            for target_name in targets:
                qualified = f"{module_name}.{target_name}"
                symbols.append(
                    symbol_node(
                        name=target_name,
                        qualified_name=qualified,
                        kind="constant",
                        file_path=file_node["path"],
                        node=node,
                        signature=target_name,
                        calls=[],
                    )
                )

    return symbols, extract_imports(tree)


def extract_python_symbols(repo_path: Path, file_map: list[dict[str, Any]]) -> dict[str, Any]:
    symbols: list[dict[str, Any]] = []
    file_imports: dict[str, list[str]] = {}
    parse_errors: list[dict[str, str]] = []

    for file_node in file_map:
        if file_node["language"] != "python":
            continue
        try:
            file_symbols, imports = extract_file_symbols(repo_path, file_node)
        except Exception as exc:
            parse_errors.append({"path": file_node["path"], "error": str(exc)})
            continue
        symbols.extend(file_symbols)
        file_imports[file_node["path"]] = imports

    return {
        "symbols": sorted(symbols, key=lambda item: item["qualified_name"]),
        "file_imports": file_imports,
        "parse_errors": parse_errors,
    }
