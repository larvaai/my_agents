from __future__ import annotations

import subprocess
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"
MAX_TIMEOUT_SECONDS = 30

mcp = FastMCP(
    "python-sandbox",
    instructions=(
        "Run Python files inside the project workspace only. "
        "Use run_python to execute a .py file and inspect stdout, stderr, and returncode."
    ),
)


class SandboxError(ValueError):
    pass


def _safe_workspace_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = WORKSPACE_DIR / path

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise SandboxError(f"Path is outside workspace: {raw_path}")

    return resolved


@mcp.tool()
def run_python(path: str, timeout: int = 10) -> dict[str, Any]:
    """
    Execute a Python file from the workspace and return stdout, stderr, and exit code.
    """
    file_path = _safe_workspace_path(path)

    if not file_path.exists():
        return {
            "ok": False,
            "error": "Python file does not exist.",
            "path": str(file_path),
            "stdout": "",
            "stderr": "",
            "returncode": None,
        }

    if not file_path.is_file():
        return {
            "ok": False,
            "error": "Path is not a file.",
            "path": str(file_path),
            "stdout": "",
            "stderr": "",
            "returncode": None,
        }

    if file_path.suffix != ".py":
        return {
            "ok": False,
            "error": "Only .py files can be executed.",
            "path": str(file_path),
            "stdout": "",
            "stderr": "",
            "returncode": None,
        }

    timeout = max(1, min(int(timeout), MAX_TIMEOUT_SECONDS))

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(WORKSPACE_DIR)

    command = [
    sys.executable,
    "-u",
    str(file_path),
    ]

    creationflags = 0

    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            command,
            cwd=str(WORKSPACE_DIR),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"Python execution timed out after {timeout} seconds.",
            "path": str(file_path),
            "command": command,
            "python_executable": sys.executable,
            "cwd": str(WORKSPACE_DIR),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "returncode": None,
        }

    return {
        "ok": result.returncode == 0,
        "path": str(file_path),
        "timeout": timeout,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

@mcp.tool()
def python_probe(timeout: int = 10) -> dict[str, Any]:
    """
    Probe whether child Python subprocess can start and exit.
    """
    timeout = max(1, min(int(timeout), MAX_TIMEOUT_SECONDS))

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    command = [
        sys.executable,
        "-u",
        "-c",
        "import sys, os; print('PYTHON_PROBE_OK'); print(sys.executable); print(os.getcwd())",
    ]

    creationflags = 0

    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            command,
            cwd=str(WORKSPACE_DIR),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"Python probe timed out after {timeout} seconds.",
            "command": command,
            "python_executable": sys.executable,
            "cwd": str(WORKSPACE_DIR),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "returncode": None,
        }

    return {
        "ok": result.returncode == 0,
        "command": command,
        "python_executable": sys.executable,
        "cwd": str(WORKSPACE_DIR),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
