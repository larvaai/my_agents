from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from core.runtime_paths import PROJECT_DIR
from mcp.server.fastmcp import FastMCP


MAX_TIMEOUT_SECONDS = 180
SERVICE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

mcp = FastMCP(
    "docker-server",
    instructions=(
        "Safe Docker MCP. Read container/service status and logs. Compose up/stop "
        "are guarded; destructive image, volume, and container deletion is not exposed."
    ),
)


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _metadata(summary: str, risk: str, allowed: bool, reasons: list[str] | None = None) -> dict[str, Any]:
    return {
        "summary": summary,
        "security_risk": risk,
        "allowed": allowed,
        "reasons": reasons or [],
    }


def _validate_service(service: str | None) -> str | None:
    if service is None or service == "":
        return None
    if not SERVICE_RE.match(service):
        raise ValueError("Invalid docker compose service name.")
    return service


def _creationflags() -> int:
    if sys.platform.startswith("win"):
        return subprocess.CREATE_NO_WINDOW
    return 0


def _run(command: list[str], timeout: int, metadata: dict[str, Any]) -> dict[str, Any]:
    timeout = max(1, min(int(timeout), MAX_TIMEOUT_SECONDS))
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_DIR),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
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
            "command_metadata": metadata,
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
            "command_metadata": metadata,
        }

    return {
        "ok": result.returncode == 0,
        "command": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "command_metadata": metadata,
    }


@mcp.tool()
def docker_health(timeout: int = 20) -> dict[str, Any]:
    """
    Check Docker CLI availability.
    """
    result = _run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        timeout=timeout,
        metadata=_metadata("Check Docker engine availability", "low", True, ["read-only docker version check"]),
    )
    result["tool"] = "docker_health"
    return result


@mcp.tool()
def docker_ps(all: bool = True, timeout: int = 20) -> dict[str, Any]:
    """
    List Docker containers.
    """
    command = ["docker", "ps"]
    if all:
        command.append("-a")
    result = _run(
        command,
        timeout=timeout,
        metadata=_metadata("List Docker containers", "low", True, ["read-only docker ps"]),
    )
    result["tool"] = "docker_ps"
    return result


@mcp.tool()
def docker_compose_ps(timeout: int = 20) -> dict[str, Any]:
    """
    List services from this project's docker-compose.yml.
    """
    result = _run(
        ["docker", "compose", "ps"],
        timeout=timeout,
        metadata=_metadata("List Docker Compose services", "low", True, ["read-only compose ps"]),
    )
    result["tool"] = "docker_compose_ps"
    return result


@mcp.tool()
def docker_compose_logs(service: str | None = None, tail: int = 100, timeout: int = 30) -> dict[str, Any]:
    """
    Read bounded Docker Compose logs.
    """
    try:
        service = _validate_service(service)
        tail = max(1, min(int(tail), 1000))
        command = ["docker", "compose", "logs", "--no-color", "--tail", str(tail)]
        if service:
            command.append(service)
        result = _run(
            command,
            timeout=timeout,
            metadata=_metadata("Read Docker Compose logs", "low", True, ["read-only compose logs"]),
        )
        result["tool"] = "docker_compose_logs"
        result["service"] = service
        result["tail"] = tail
        return result
    except Exception as exc:
        return {"ok": False, "tool": "docker_compose_logs", "error": str(exc)}


@mcp.tool()
def docker_compose_up(service: str | None = None, timeout: int = 120) -> dict[str, Any]:
    """
    Run docker compose up -d. Disabled unless DOCKER_MCP_ALLOW_MUTATION=1.
    """
    try:
        service = _validate_service(service)
        metadata = _metadata(
            "Start Docker Compose service(s)",
            "medium",
            _truthy_env("DOCKER_MCP_ALLOW_MUTATION"),
            ["compose up is a state-changing operation"],
        )
        if not metadata["allowed"]:
            return {
                "ok": False,
                "tool": "docker_compose_up",
                "blocked": True,
                "error": "Docker mutation blocked. Set DOCKER_MCP_ALLOW_MUTATION=1 to allow compose up.",
                "command_metadata": metadata,
            }

        command = ["docker", "compose", "up", "-d"]
        if service:
            command.append(service)
        result = _run(command, timeout=timeout, metadata=metadata)
        result["tool"] = "docker_compose_up"
        result["service"] = service
        return result
    except Exception as exc:
        return {"ok": False, "tool": "docker_compose_up", "error": str(exc)}


@mcp.tool()
def docker_compose_stop(service: str | None = None, timeout: int = 60) -> dict[str, Any]:
    """
    Run docker compose stop. Disabled unless DOCKER_MCP_ALLOW_MUTATION=1.
    """
    try:
        service = _validate_service(service)
        metadata = _metadata(
            "Stop Docker Compose service(s)",
            "medium",
            _truthy_env("DOCKER_MCP_ALLOW_MUTATION"),
            ["compose stop is a state-changing operation"],
        )
        if not metadata["allowed"]:
            return {
                "ok": False,
                "tool": "docker_compose_stop",
                "blocked": True,
                "error": "Docker mutation blocked. Set DOCKER_MCP_ALLOW_MUTATION=1 to allow compose stop.",
                "command_metadata": metadata,
            }

        command = ["docker", "compose", "stop"]
        if service:
            command.append(service)
        result = _run(command, timeout=timeout, metadata=metadata)
        result["tool"] = "docker_compose_stop"
        result["service"] = service
        return result
    except Exception as exc:
        return {"ok": False, "tool": "docker_compose_stop", "error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
