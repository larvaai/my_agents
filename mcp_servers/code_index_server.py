from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


PROJECT_DIR = Path(__file__).resolve().parent.parent
MAX_FILES = 1000
MAX_RESULTS = 500
CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "agent_runs",
    "node_modules",
    "OpenHands",
    "openhands-workspace",
    "qdrant_storage",
    "test_runs",
}

mcp = FastMCP(
    "code-index-server",
    instructions=(
        "Read-only project code index. Finds symbols, imports, references, "
        "and lightweight dependency graph without scanning the whole repo by hand."
    ),
)


class CodeIndexError(ValueError):
    pass


def _safe_project_path(raw_path: str = ".") -> Path:
    path = Path(raw_path or ".")
    if not path.is_absolute():
        path = PROJECT_DIR / path

    resolved = path.resolve()
    project = PROJECT_DIR.resolve()
    if resolved != project and not resolved.is_relative_to(project):
        raise CodeIndexError(f"Path is outside project: {raw_path}")
    return resolved


def _rel(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_DIR.resolve())).replace("\\", "/")


def _is_excluded(path: Path) -> bool:
    try:
        parts = set(path.resolve().relative_to(PROJECT_DIR.resolve()).parts)
    except ValueError:
        return True
    return bool(parts & EXCLUDED_DIRS)


def _code_files(root: Path, max_files: int) -> tuple[list[Path], bool]:
    if root.is_file():
        files = [root] if root.suffix.lower() in CODE_EXTENSIONS and not _is_excluded(root) else []
        return files[:max_files], len(files) > max_files

    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if len(files) >= max_files:
            return files, True
        if not path.is_file():
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        if _is_excluded(path):
            continue
        files.append(path)
    return files, False


def _range(node: ast.AST) -> dict[str, int | None]:
    return {
        "lineno": getattr(node, "lineno", None),
        "end_lineno": getattr(node, "end_lineno", None),
        "col_offset": getattr(node, "col_offset", None),
        "end_col_offset": getattr(node, "end_col_offset", None),
    }


class _PythonIndexVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.class_stack: list[str] = []
        self.symbols: list[dict[str, Any]] = []
        self.imports: list[dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.symbols.append(
            {
                "type": "class",
                "name": ".".join([*self.class_stack, node.name]),
                "file": _rel(self.file_path),
                **_range(node),
            }
        )
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self._visit_function(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self._visit_function(node, "async_function")

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, fallback_type: str) -> None:
        symbol_type = "method" if self.class_stack else fallback_type
        name = ".".join([*self.class_stack, node.name]) if self.class_stack else node.name
        self.symbols.append(
            {
                "type": symbol_type,
                "name": name,
                "file": _rel(self.file_path),
                **_range(node),
            }
        )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            self.imports.append(
                {
                    "type": "import",
                    "module": alias.name,
                    "alias": alias.asname,
                    "file": _rel(self.file_path),
                    **_range(node),
                }
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        self.imports.append(
            {
                "type": "from_import",
                "module": node.module or "",
                "names": [alias.name for alias in node.names],
                "level": node.level,
                "file": _rel(self.file_path),
                **_range(node),
            }
        )


JS_CLASS_RE = re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)")
JS_FUNC_RE = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)")
JS_CONST_FUNC_RE = re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>")
JS_IMPORT_RE = re.compile(r"^\s*import\s+(?:.+?\s+from\s+)?[\"']([^\"']+)[\"']")


def _index_python(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=str(path))
    visitor = _PythonIndexVisitor(path)
    visitor.visit(tree)
    return visitor.symbols, visitor.imports, []


def _index_js_like(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    symbols: list[dict[str, Any]] = []
    imports: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        for regex, symbol_type in ((JS_CLASS_RE, "class"), (JS_FUNC_RE, "function"), (JS_CONST_FUNC_RE, "function")):
            match = regex.search(line)
            if match:
                symbols.append({"type": symbol_type, "name": match.group(1), "file": _rel(path), "lineno": lineno})
                break
        import_match = JS_IMPORT_RE.search(line)
        if import_match:
            imports.append({"type": "import", "module": import_match.group(1), "file": _rel(path), "lineno": lineno})
    return symbols, imports, []


def _index_file(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if path.suffix.lower() == ".py":
        return _index_python(path)
    return _index_js_like(path)


@mcp.tool()
def code_index(path: str = ".", max_files: int = 300) -> dict[str, Any]:
    """
    Index code files and return symbols/imports.
    """
    try:
        max_files = max(1, min(int(max_files), MAX_FILES))
        root = _safe_project_path(path)
        files, truncated = _code_files(root, max_files)
        symbols: list[dict[str, Any]] = []
        imports: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for file_path in files:
            try:
                file_symbols, file_imports, file_errors = _index_file(file_path)
                symbols.extend(file_symbols)
                imports.extend(file_imports)
                errors.extend(file_errors)
            except SyntaxError as exc:
                errors.append({"file": _rel(file_path), "error": str(exc), "type": "syntax_error"})
            except Exception as exc:
                errors.append({"file": _rel(file_path), "error": str(exc), "type": "index_error"})

        return {
            "ok": True,
            "tool": "code_index",
            "path": path,
            "files_count": len(files),
            "truncated": truncated,
            "symbols_count": len(symbols),
            "imports_count": len(imports),
            "symbols": symbols[:MAX_RESULTS],
            "imports": imports[:MAX_RESULTS],
            "errors": errors[:100],
        }
    except Exception as exc:
        return {"ok": False, "tool": "code_index", "path": path, "error": str(exc)}


@mcp.tool()
def code_find_symbol(name: str, path: str = ".", max_files: int = 300, max_results: int = 50) -> dict[str, Any]:
    """
    Find functions/classes/methods by partial case-insensitive name.
    """
    result = code_index(path=path, max_files=max_files)
    if not result.get("ok"):
        return result

    query = name.lower()
    max_results = max(1, min(int(max_results), MAX_RESULTS))
    matches = [
        symbol
        for symbol in result.get("symbols", [])
        if query in str(symbol.get("name", "")).lower()
    ][:max_results]
    return {
        "ok": True,
        "tool": "code_find_symbol",
        "name": name,
        "count": len(matches),
        "matches": matches,
    }


@mcp.tool()
def code_find_references(name: str, path: str = ".", max_files: int = 300, max_results: int = 100) -> dict[str, Any]:
    """
    Find line-based references to a name.
    """
    try:
        max_files = max(1, min(int(max_files), MAX_FILES))
        max_results = max(1, min(int(max_results), MAX_RESULTS))
        root = _safe_project_path(path)
        files, truncated = _code_files(root, max_files)
        references: list[dict[str, Any]] = []

        for file_path in files:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if name in line:
                    references.append({"file": _rel(file_path), "lineno": lineno, "line": line.strip()[:300]})
                    if len(references) >= max_results:
                        return {
                            "ok": True,
                            "tool": "code_find_references",
                            "name": name,
                            "count": len(references),
                            "truncated": True,
                            "references": references,
                        }

        return {
            "ok": True,
            "tool": "code_find_references",
            "name": name,
            "count": len(references),
            "truncated": truncated,
            "references": references,
        }
    except Exception as exc:
        return {"ok": False, "tool": "code_find_references", "name": name, "error": str(exc)}


@mcp.tool()
def code_dependency_graph(path: str = ".", max_files: int = 300) -> dict[str, Any]:
    """
    Return a lightweight import graph keyed by file.
    """
    result = code_index(path=path, max_files=max_files)
    if not result.get("ok"):
        return result

    graph: dict[str, list[str]] = {}
    for item in result.get("imports", []):
        file_name = item.get("file")
        module = item.get("module")
        if not file_name or not module:
            continue
        graph.setdefault(str(file_name), [])
        if str(module) not in graph[str(file_name)]:
            graph[str(file_name)].append(str(module))

    return {
        "ok": True,
        "tool": "code_dependency_graph",
        "path": path,
        "files_count": result.get("files_count", 0),
        "graph": graph,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
