# Setup And Run

This page is the supported setup path for a fresh clone on macOS Apple Silicon
(MacBook M1/M2/M3). Windows commands are still listed where they differ.

## Mac Quick Start

```bash
git clone <repo-url> my_agents
cd my_agents

brew bundle
make bootstrap
make doctor
make quick
```

`make bootstrap` creates `.venv`, installs Python dependencies, installs
Playwright Chromium, creates `.env` from `.env.example` when missing, creates
`var/*`, and runs `python run_dev_checks.py --quick`.

If you do not want Make:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m playwright install chromium
mkdir -p var/workspace var/agent_runs var/test_runs var/qdrant_storage
cp .env.example .env
python run_dev_checks.py --quick
```

## Required Tools

- Python 3.11+.
- Node.js/npx for Filesystem MCP and Context7 MCP.
- LM Studio or another OpenAI-compatible endpoint for LLM runs.
- Docker Desktop if you use Qdrant/RAG or Docker MCP.
- Homebrew is optional but recommended on macOS.

The repo includes a `Brewfile` for macOS:

```bash
brew bundle
```

The Brewfile installs command-line tools plus Docker Desktop and LM Studio.
Open Docker Desktop and LM Studio once after installation to finish their
first-run setup.

## Environment

Copy the example file once:

```bash
cp .env.example .env
```

The most common values:

```text
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=qwen3.5-9b-claude-4.6-opus-uncensored-distilled
QDRANT_URL=http://localhost:6333
SEARCH_PROVIDER=duckduckgo
```

`.env` is loaded by `core.runtime_paths` and `llm.py`. Runtime paths default to
`var/*`, so generated data stays outside source code:

| Path | Purpose |
|---|---|
| `var/workspace/` | Sandbox workspace for filesystem, Python, documents, browser, RAG |
| `var/agent_runs/` | Agent event logs and run summaries |
| `var/test_runs/` | Test runner logs and summaries |
| `var/qdrant_storage/` | Local Qdrant storage mounted by Docker Compose |

## Dev Gate

Use one entrypoint for local and CI checks:

```bash
python run_dev_checks.py --quick
python run_dev_checks.py --full
```

Equivalent Make targets on macOS:

```bash
make quick
make full
```

`--quick` runs compile, unit tests, feature tests, kernel smoke, JsonGate smoke,
role smoke, and LangGraph smoke. `--full` adds the MCP chain smoke and the
capability suite.

## Run Agents

Single-agent orchestrator:

```bash
source .venv/bin/activate
python main.py prompts/auto_cases/test_project_00_python_probe.md
```

LangGraph role orchestrator:

```bash
source .venv/bin/activate
python main_langgraph.py prompts/auto_cases/test_langgraph_01_smoke.md
```

For longer LangGraph runs:

```bash
LANGGRAPH_MAX_STEPS=80 python main_langgraph.py prompts/the_sims_prompt.md
```

## Qdrant/RAG

Start Qdrant:

```bash
docker compose up -d qdrant
curl -fsS http://localhost:6333/collections
```

Stop it:

```bash
docker compose down
```

The compose file mounts `./var/qdrant_storage` into the container.

## MCP Portability Notes

- Python MCP servers are launched with `sys.executable`, so a Mac clone uses
  `.venv/bin/python` after activation instead of a random system interpreter.
- Node MCP servers use `npx` directly on macOS/Linux. On Windows the same config
  still wraps `npx` with `cmd /c`.
- Override `NPX_COMMAND` in `.env` only if your Node install exposes `npx` in a
  non-standard location.

## Windows Notes

PowerShell install path:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
python run_dev_checks.py --quick
```

Health checks:

```powershell
docker compose up -d qdrant
Invoke-RestMethod http://localhost:6333/collections
```

## Troubleshooting

- `npx not found`: install Node with `brew install node`, then open a new shell.
- `docker not found`: install/start Docker Desktop, then rerun the Qdrant command.
- `LLM request failed`: start LM Studio's local server and verify
  `curl http://localhost:1234/v1/models`.
- Playwright errors: run `python -m playwright install chromium` inside `.venv`.
- Import errors after clone: rerun `make bootstrap` or reinstall with
  `python -m pip install -r requirements.txt`.
