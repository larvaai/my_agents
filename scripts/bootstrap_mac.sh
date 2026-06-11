#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This bootstrap is intended for macOS. Continuing anyway."
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh, then rerun this script."
  exit 1
fi

brew bundle check >/dev/null 2>&1 || brew bundle

PYTHON_BIN="${PYTHON_BIN:-python3.11}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m playwright install chromium

mkdir -p var/workspace var/agent_runs var/test_runs var/qdrant_storage
if [[ ! -f .env ]]; then
  cp .env.example .env
fi

python run_dev_checks.py --quick

echo
echo "Bootstrap complete."
echo "Next: edit .env if your LLM endpoint/model differs, then run: make full"
