from __future__ import annotations

import os
import py_compile
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from core.runtime_paths import PROJECT_DIR, WORKSPACE_DIR

from mcp.server.fastmcp import FastMCP


MAX_FILES = 1000
MAX_TIMEOUT_SECONDS = 120
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
    "var",
    "workspace",
}

mcp = FastMCP(
    "lint-test-server",
    instructions=(
        "Structured lint/test runner. Runs allowlisted compile, ruff, and Python "
        "test commands without arbitrary shell."
    ),
)


class LintTestError(ValueError):
    pass


def _safe_project_path(raw_path: str = ".") -> Path:
    path = Path(raw_path or ".")
    if not path.is_absolute():
        path = PROJECT_DIR / path

    resolved = path.resolve()
    project = PROJECT_DIR.resolve()
    if resolved != project and not resolved.is_relative_to(project):
        raise LintTestError(f"Path is outside project: {raw_path}")
    return resolved


def _rel(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_DIR.resolve())).replace("\\", "/")


def _is_excluded(path: Path) -> bool:
    try:
        parts = set(path.resolve().relative_to(PROJECT_DIR.resolve()).parts)
    except ValueError:
        return True
    return bool(parts & EXCLUDED_DIRS)


def _python_files(root: Path, max_files: int) -> tuple[list[Path], bool]:
    if root.is_file():
        return ([root] if root.suffix.lower() == ".py" else []), False

    files: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        if len(files) >= max_files:
            return files, True
        if not path.is_file():
            continue
        if _is_excluded(path):
            continue
        files.append(path)
    return files, False


def _creationflags() -> int:
    if sys.platform.startswith("win"):
        return subprocess.CREATE_NO_WINDOW
    return 0


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = os.pathsep.join([str(PROJECT_DIR), str(WORKSPACE_DIR), env.get("PYTHONPATH", "")])
    return env


def _run(command: list[str], timeout: int, cwd: Path | None = None) -> dict[str, Any]:
    timeout = max(1, min(int(timeout), MAX_TIMEOUT_SECONDS))
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd or PROJECT_DIR),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=_env(),
            creationflags=_creationflags(),
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "dependency_failure": True,
            "error": f"Command not found: {command[0]}",
            "command": command,
            "stdout": "",
            "stderr": "",
            "returncode": None,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"Command timed out after {timeout} seconds.",
            "command": command,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "returncode": None,
            "duration_seconds": round(time.monotonic() - started, 3),
        }

    return {
        "ok": result.returncode == 0,
        "command": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def _ruff_available(timeout: int = 10) -> tuple[bool, str]:
    result = _run([sys.executable, "-m", "ruff", "--version"], timeout=timeout)
    if result.get("ok"):
        return True, (result.get("stdout") or "").strip()
    return False, (result.get("stderr") or result.get("error") or "ruff is not installed").strip()


def _ruff_exclude_args() -> list[str]:
    args: list[str] = ["--force-exclude"]
    for folder in sorted(EXCLUDED_DIRS):
        args.extend(["--exclude", folder])
    return args


@mcp.tool()
def lint_compile(path: str = ".", timeout: int = 30) -> dict[str, Any]:
    """
    Compile Python files under a safe project path. Root excludes fixture/heavy dirs.
    """
    started = time.monotonic()
    try:
        max_files = MAX_FILES
        root = _safe_project_path(path)
        files, truncated = _python_files(root, max_files=max_files)
        failures: list[dict[str, Any]] = []

        for file_path in files:
            try:
                py_compile.compile(str(file_path), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append({"file": _rel(file_path), "error": str(exc)})

        return {
            "ok": not failures,
            "tool": "lint_compile",
            "path": path,
            "checked_files": len(files),
            "truncated": truncated,
            "failures": failures[:100],
            "duration_seconds": round(time.monotonic() - started, 3),
            "metadata": {
                "summary": "Compile Python files",
                "security_risk": "low",
                "validation": True,
            },
        }
    except Exception as exc:
        return {"ok": False, "tool": "lint_compile", "path": path, "error": str(exc)}


@mcp.tool()
def lint_ruff_check(path: str = ".", timeout: int = 30) -> dict[str, Any]:
    """
    Run ruff check if ruff is installed.
    """
    try:
        available, detail = _ruff_available()
        if not available:
            return {
                "ok": False,
                "tool": "lint_ruff_check",
                "dependency_failure": True,
                "error": "ruff is not available",
                "detail": detail,
            }

        target = _safe_project_path(path)
        command = [sys.executable, "-m", "ruff", "check", *_ruff_exclude_args(), str(target)]
        result = _run(command, timeout=timeout)
        result["tool"] = "lint_ruff_check"
        result["metadata"] = {"summary": "Run ruff check", "security_risk": "low", "validation": True}
        return result
    except Exception as exc:
        return {"ok": False, "tool": "lint_ruff_check", "path": path, "error": str(exc)}


@mcp.tool()
def lint_ruff_format_check(path: str = ".", timeout: int = 30) -> dict[str, Any]:
    """
    Run ruff format --check if ruff is installed.
    """
    try:
        available, detail = _ruff_available()
        if not available:
            return {
                "ok": False,
                "tool": "lint_ruff_format_check",
                "dependency_failure": True,
                "error": "ruff is not available",
                "detail": detail,
            }

        target = _safe_project_path(path)
        command = [sys.executable, "-m", "ruff", "format", "--check", *_ruff_exclude_args(), str(target)]
        result = _run(command, timeout=timeout)
        result["tool"] = "lint_ruff_format_check"
        result["metadata"] = {"summary": "Run ruff format --check", "security_risk": "low", "validation": True}
        return result
    except Exception as exc:
        return {"ok": False, "tool": "lint_ruff_format_check", "path": path, "error": str(exc)}


@mcp.tool()
def test_python_file(path: str, timeout: int = 30) -> dict[str, Any]:
    """
    Run one Python file from the project.
    """
    try:
        target = _safe_project_path(path)
        if not target.exists():
            return {"ok": False, "tool": "test_python_file", "path": path, "error": "File does not exist."}
        if not target.is_file():
            return {"ok": False, "tool": "test_python_file", "path": path, "error": "Path is not a file."}
        if target.suffix.lower() != ".py":
            return {"ok": False, "tool": "test_python_file", "path": path, "error": "Only .py files can be executed."}

        result = _run([sys.executable, "-u", str(target)], timeout=timeout)
        result["tool"] = "test_python_file"
        result["path"] = _rel(target)
        result["metadata"] = {"summary": f"Run Python file {_rel(target)}", "security_risk": "medium", "validation": True}
        return result
    except Exception as exc:
        return {"ok": False, "tool": "test_python_file", "path": path, "error": str(exc)}


@mcp.tool()
def test_smoke_suite(timeout: int = 60) -> dict[str, Any]:
    """
    Run a small default validation suite for this project.
    """
    results: list[dict[str, Any]] = []
    for path in ("agents", "mcp_servers", "tools"):
        results.append(lint_compile(path=path, timeout=timeout))

    for path in ("main.py", "orchestrator.py", "run_mcp_chain_smoke.py", str(WORKSPACE_DIR / "code" / "project_smoke_test.py")):
        target = Path(path)
        if not target.is_absolute():
            target = PROJECT_DIR / target
        if target.exists():
            if target.suffix == ".py" and target.resolve().is_relative_to(WORKSPACE_DIR.resolve()):
                results.append(test_python_file(path=str(target), timeout=timeout))
            else:
                results.append(lint_compile(path=str(target), timeout=timeout))

    passed = all(item.get("ok") for item in results)
    return {
        "ok": passed,
        "tool": "test_smoke_suite",
        "results": results,
        "metadata": {
            "summary": "Run project smoke validation suite",
            "security_risk": "medium",
            "validation": True,
        },
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")

