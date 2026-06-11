#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

failures=0

ok() {
  printf '[OK] %s\n' "$1"
}

warn() {
  printf '[WARN] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
  failures=$((failures + 1))
}

need_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$cmd: $(command -v "$cmd")"
  else
    fail "$cmd not found"
  fi
}

if [[ "$(uname -s)" == "Darwin" ]]; then
  ok "macOS $(sw_vers -productVersion) / $(uname -m)"
else
  warn "not running on macOS: $(uname -s)"
fi

need_cmd git
need_cmd node
need_cmd npx
need_cmd curl

if command -v docker >/dev/null 2>&1; then
  ok "docker: $(docker --version)"
else
  warn "docker not found; RAG/Qdrant and Docker MCP will be unavailable"
fi

PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
    warn ".venv missing; using $PYTHON_BIN for diagnostics"
  else
    fail "no .venv/bin/python and no python3 on PATH"
  fi
fi

if [[ -n "${PYTHON_BIN:-}" ]]; then
  ok "python: $("$PYTHON_BIN" --version)"
  "$PYTHON_BIN" - <<'PY'
import importlib
import sys

modules = [
    "openai",
    "mcp",
    "dotenv",
    "yaml",
    "qdrant_client",
    "fastembed",
    "pypdf",
    "docx",
    "playwright",
    "langgraph",
]

missing = []
for module in modules:
    try:
        importlib.import_module(module)
    except Exception as exc:
        missing.append(f"{module}: {exc}")

if missing:
    print("[FAIL] missing Python dependencies:")
    for item in missing:
        print(f"  - {item}")
    sys.exit(1)

print("[OK] Python dependencies import")
PY
fi

if [[ -f .env ]]; then
  ok ".env present"
else
  warn ".env missing; copy .env.example to .env"
fi

mkdir -p var/workspace var/agent_runs var/test_runs var/qdrant_storage
ok "runtime directories present under var/"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  "$PYTHON_BIN" -m compileall -q core features agents orchestration output_gate mcp_servers tools main.py main_langgraph.py run_dev_checks.py \
    && ok "source compile check" \
    || fail "source compile check failed"
fi

if [[ "$failures" -gt 0 ]]; then
  echo
  echo "Doctor found $failures blocking issue(s)."
  exit 1
fi

echo
echo "Doctor passed. Run: make quick"
