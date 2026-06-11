PYTHON_BIN ?= python3.11
VENV_PYTHON := .venv/bin/python
VENV_PIP := .venv/bin/pip

.PHONY: bootstrap install doctor quick full dev qdrant-up qdrant-down qdrant-health lm-health clean

bootstrap:
	bash scripts/bootstrap_mac.sh

install:
	$(PYTHON_BIN) -m venv .venv
	$(VENV_PIP) install --upgrade pip setuptools wheel
	$(VENV_PIP) install -r requirements.txt
	$(VENV_PYTHON) -m playwright install chromium
	mkdir -p var/workspace var/agent_runs var/test_runs var/qdrant_storage
	test -f .env || cp .env.example .env

doctor:
	bash scripts/mac_doctor.sh

quick:
	$(VENV_PYTHON) run_dev_checks.py --quick

full:
	$(VENV_PYTHON) run_dev_checks.py --full

dev: quick

qdrant-up:
	docker compose up -d qdrant

qdrant-down:
	docker compose down

qdrant-health:
	curl -fsS http://localhost:6333/collections

lm-health:
	curl -fsS "$${LLM_BASE_URL:-http://localhost:1234/v1}/models"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache
