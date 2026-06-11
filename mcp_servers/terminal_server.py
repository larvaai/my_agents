from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from core.runtime_paths import PROJECT_DIR, WORKSPACE_DIR

from mcp.server.fastmcp import FastMCP


MAX_TIMEOUT_SECONDS = 120

mcp = FastMCP(
    "terminal-server",
    instructions=(
        "Run non-interactive allowlisted commands without invoking a shell. "
        "Every result includes command summary and security_risk metadata."
    ),
)


SHELL_EXECUTABLES = {"cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe", "bash", "sh"}
DESTRUCTIVE_EXECUTABLES = {"rm", "del", "erase", "rmdir", "remove-item"}
GIT_MUTATIONS = {"add", "commit", "push", "reset", "checkout", "switch", "branch", "merge", "rebase", "clean"}
SHELL_TOKENS = {"&&", "||", "|", ";", ">", "<", "`"}


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_cwd(raw_cwd: str | None) -> Path:
    if not raw_cwd:
        return PROJECT_DIR
    path = Path(raw_cwd)
    if not path.is_absolute():
        path = PROJECT_DIR / path

    resolved = path.resolve()
    project = PROJECT_DIR.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if (
        resolved != project
        and resolved != workspace
        and not resolved.is_relative_to(project)
    ):
        raise ValueError(f"cwd is outside project: {raw_cwd}")
    return resolved


def _exe_name(argv: list[str]) -> str:
    return Path(argv[0]).name.lower() if argv else ""


def _has_shell_tokens(argv: list[str]) -> bool:
    return any(any(token in arg for token in SHELL_TOKENS) for arg in argv)


def _is_python(argv: list[str]) -> bool:
    exe = _exe_name(argv)
    return exe in {"python", "python.exe", "py", "py.exe"} or Path(argv[0]).resolve() == Path(sys.executable).resolve()


def _summarize(argv: list[str]) -> str:
    if not argv:
        return "empty command"
    if _is_python(argv):
        if len(argv) >= 3 and argv[1] == "-m" and argv[2] == "py_compile":
            return "Compile Python files"
        if len(argv) >= 2 and argv[1] == "-c":
            return "Run small Python probe"
        if len(argv) >= 2:
            script = Path(argv[1]).name
            return f"Run Python script {script}"
    exe = _exe_name(argv)
    if exe in {"node", "node.exe", "npm", "npm.cmd", "npx", "npx.cmd"} and any(arg in {"-v", "--version"} for arg in argv[1:]):
        return f"Check {exe} version"
    if exe in {"git", "git.exe"} and len(argv) >= 2:
        return f"Run git {argv[1]}"
    return "Run non-interactive command"


def _classify(argv: list[str]) -> dict[str, Any]:
    reasons: list[str] = []
    allowed = True
    risk = "low"

    if not argv:
        return {
            "allowed": False,
            "security_risk": "blocked",
            "summary": "empty command",
            "reasons": ["argv is required"],
        }

    exe = _exe_name(argv)
    if exe in SHELL_EXECUTABLES:
        allowed = False
        risk = "blocked"
        reasons.append("shell executables are not allowed; pass argv directly")

    if exe in DESTRUCTIVE_EXECUTABLES:
        allowed = False
        risk = "blocked"
        reasons.append("destructive filesystem command")

    if _has_shell_tokens(argv):
        allowed = False
        risk = "blocked"
        reasons.append("shell control/redirection tokens are not allowed")

    if exe in {"git", "git.exe"} and len(argv) >= 2 and argv[1].lower() in GIT_MUTATIONS:
        allowed = False
        risk = "blocked"
        reasons.append("mutating git commands must use Git MCP policy path")

    if _is_python(argv):
        if len(argv) >= 3 and argv[1] == "-m" and argv[2] == "py_compile":
            risk = "low"
            reasons.append("python compile validation")
        elif len(argv) >= 2 and argv[1] == "-c":
            risk = "medium"
            reasons.append("small Python probe")
        else:
            risk = "medium"
            reasons.append("Python script execution")
    elif exe in {"node", "node.exe", "npm", "npm.cmd", "npx", "npx.cmd"} and any(arg in {"-v", "--version"} for arg in argv[1:]):
        risk = "low"
        reasons.append("version check")
    elif exe in {"git", "git.exe"}:
        risk = "low"
        reasons.append("read-only git command")
    elif allowed:
        risk = "high"
        reasons.append("command is outside the default allowlist")

    if risk == "high" and not _truthy_env("AGENT_ALLOW_HIGH_RISK_TERMINAL"):
        allowed = False
        risk = "blocked"
        reasons.append("set AGENT_ALLOW_HIGH_RISK_TERMINAL=1 to allow high-risk commands")

    return {
        "allowed": allowed,
        "security_risk": risk,
        "summary": _summarize(argv),
        "reasons": reasons,
    }


@mcp.tool()
def terminal_run(
    argv: list[str],
    timeout: int = 10,
    cwd: str | None = None,
    purpose: str = "",
) -> dict[str, Any]:
    """
    Run a non-interactive command as argv without shell expansion.
    """
    started = time.monotonic()
    try:
        if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
            return {
                "ok": False,
                "tool": "terminal_run",
                "error": "argv must be a list of strings.",
                "command_metadata": {
                    "summary": "invalid command",
                    "security_risk": "blocked",
                    "reasons": ["invalid argv type"],
                },
            }

        timeout = max(1, min(int(timeout), MAX_TIMEOUT_SECONDS))
        workdir = _safe_cwd(cwd)
        metadata = _classify(argv)
        metadata["purpose"] = purpose

        if not metadata["allowed"]:
            return {
                "ok": False,
                "tool": "terminal_run",
                "blocked": True,
                "error": "Terminal command blocked by risk policy.",
                "argv": argv,
                "cwd": str(workdir),
                "command_metadata": metadata,
            }

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"

        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            argv,
            cwd=str(workdir),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            creationflags=creationflags,
        )
        return {
            "ok": result.returncode == 0,
            "tool": "terminal_run",
            "argv": argv,
            "cwd": str(workdir),
            "timeout": timeout,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_seconds": round(time.monotonic() - started, 3),
            "command_metadata": metadata,
        }
    except subprocess.TimeoutExpired as exc:
        metadata = _classify(argv if isinstance(argv, list) else [])
        return {
            "ok": False,
            "tool": "terminal_run",
            "argv": argv,
            "timeout": timeout,
            "error": f"Command timed out after {timeout} seconds.",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "returncode": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "command_metadata": metadata,
        }
    except Exception as exc:
        return {
            "ok": False,
            "tool": "terminal_run",
            "argv": argv,
            "error": str(exc),
            "duration_seconds": round(time.monotonic() - started, 3),
            "command_metadata": {
                "summary": "terminal command failed before execution",
                "security_risk": "unknown",
                "reasons": [str(exc)],
                "purpose": purpose,
            },
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")

