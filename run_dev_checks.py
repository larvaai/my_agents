from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from core.runtime_paths import PROJECT_DIR, ensure_runtime_dirs


SOURCE_DIRS = [
    "core",
    "features",
    "agents",
    "orchestration",
    "output_gate",
    "mcp_servers",
    "tools",
]

ENTRYPOINTS = [
    "main.py",
    "main_langgraph.py",
    "orchestrator.py",
    "run_agent_role_smoke.py",
    "run_feature_tests.py",
    "run_json_gate_smoke.py",
    "run_kernel_smoke.py",
    "run_langgraph_smoke.py",
    "run_mcp_chain_smoke.py",
    "run_dev_checks.py",
]

QUICK_CHECKS = [
    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    [sys.executable, "run_feature_tests.py"],
    [sys.executable, "run_kernel_smoke.py"],
    [sys.executable, "run_json_gate_smoke.py"],
    [sys.executable, "run_agent_role_smoke.py"],
    [sys.executable, "run_langgraph_smoke.py"],
]

FULL_ONLY_CHECKS = [
    [sys.executable, "run_mcp_chain_smoke.py"],
    [sys.executable, "run_capability_suite.py"],
]


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    returncode: int
    duration_seconds: float


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("ORCH_MAX_STEPS", "20")
    return env


def _existing_paths(paths: list[str]) -> list[str]:
    return [path for path in paths if (PROJECT_DIR / path).exists()]


def _run(name: str, command: list[str], timeout: int) -> CheckResult:
    print(f"[RUN] {name}: {' '.join(command)}", flush=True)
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=str(PROJECT_DIR),
        env=_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    duration = round(time.monotonic() - started, 2)
    status = "PASS" if result.returncode == 0 else "FAIL"
    print(f"[{status}] {name} ({duration}s)", flush=True)
    return CheckResult(
        name=name,
        ok=result.returncode == 0,
        returncode=result.returncode,
        duration_seconds=duration,
    )


def _compile_command() -> list[str]:
    targets = _existing_paths(SOURCE_DIRS + ENTRYPOINTS)
    return [sys.executable, "-m", "compileall", "-q", *targets]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic development checks.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true", help="Run quick checks only. This is the default.")
    mode.add_argument("--full", action="store_true", help="Run quick checks plus MCP/capability suite.")
    parser.add_argument("--timeout", type=int, default=420, help="Timeout per non-compile check.")
    parser.add_argument("--compile-timeout", type=int, default=180, help="Timeout for compileall.")
    args = parser.parse_args()

    ensure_runtime_dirs()
    checks = QUICK_CHECKS + (FULL_ONLY_CHECKS if args.full else [])

    results = [
        _run("compileall", _compile_command(), timeout=args.compile_timeout),
    ]
    for command in checks:
        results.append(_run(Path(command[-1]).stem, command, timeout=args.timeout))

    print()
    print("SUMMARY")
    print("=" * 80)
    for item in results:
        status = "PASS" if item.ok else "FAIL"
        print(f"{status:4} {item.name:28} {item.duration_seconds:>6.2f}s rc={item.returncode}")

    if all(item.ok for item in results):
        print("DEV_CHECKS_OK")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
