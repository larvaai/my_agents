# 04 External Project Files

This file maps files outside `experiments/self_eval_qa_lab/` that are still
needed to run, test, or configure the mini repo.

## Required Runtime Files

| Path | Why it matters |
|---|---|
| `main.py` | Root CLI entrypoint. It recognizes `python main.py lab ...`. |
| `tools/mini_repo_registry.py` | Registers `self_eval_qa_lab` and maps commands to mini repo scripts. |
| `core/runtime_paths.py` | Defines project root and runtime dirs. The registry imports `PROJECT_DIR` from here. |
| `llm.py` | Shared OpenAI-compatible LLM client used by local/server providers. |
| `tools/env_loader.py` | Loads `.env` from project root before `llm.py` reads provider settings. |
| `requirements.txt` | Python dependencies needed by root project and mini repo. |
| `.env.example` | Template for LM Studio/local/server model environment variables. |

## `main.py`

Used when running:

```powershell
python main.py lab self_eval_qa_lab ...
```

It delegates to the mini-repo registry. If you bypass it and run the mini repo
script directly, this file is not used.

## `tools/mini_repo_registry.py`

Defines the `self_eval_qa_lab` registry entry:

```text
id: self_eval_qa_lab
root: experiments/self_eval_qa_lab
aliases: self-eval, qa-lab, selfeval
default command: run
commands:
  run     -> experiments/self_eval_qa_lab/main.py
  dataset -> experiments/self_eval_qa_lab/dataset_runner.py
```

The registry changes cwd to project root while executing the selected script.
This is why output defaults to:

```text
var/self_eval_qa_lab/
```

instead of being relative to the docs folder or the shell's previous directory.

## `core/runtime_paths.py`

Defines:

```text
PROJECT_DIR
VAR_DIR
WORKSPACE_DIR
AGENT_RUNS_DIR
TEST_RUNS_DIR
QDRANT_STORAGE_DIR
```

For this mini repo, the most important value is `PROJECT_DIR`, used by the
registry to locate scripts and run from the correct cwd.

## `llm.py`

Shared LLM client.

Defaults:

```text
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=qwen3.5-9b-claude-4.6-opus-uncensored-distilled
LLM_TIMEOUT=600
LLM_MAX_TOKENS=2048
```

It uses the `openai` Python package against any OpenAI-compatible endpoint.

Local model path:

```text
SelfEvalLab -> call_model() -> llm.call_llm() -> LM Studio/OpenAI-compatible local server
```

Server path:

```text
SelfEvalLab -> call_model() -> llm.call_llm(base_url=..., api_key=..., model=...) -> server
```

## `.env` And `.env.example`

`.env.example` documents the variables. `.env` is optional and should live at
project root.

Local LM Studio settings:

```text
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=<loaded model name>
LLM_TIMEOUT=600
LLM_MAX_TOKENS=2048
```

Server provider settings:

```text
SELF_EVAL_SERVER_URL=https://your-server.example/v1
SELF_EVAL_SERVER_API_KEY=...
SELF_EVAL_SERVER_MODEL=your-model
```

Fallback server env names also work:

```text
LLM_SERVER_URL
LLM_SERVER_API_KEY
LLM_SERVER_MODEL
```

## `requirements.txt`

Relevant dependencies for this mini repo:

```text
openai         LLM client.
python-dotenv  Load root .env.
PyYAML         Read config.yaml, routing_policy.yaml, rubrics.
```

Other dependencies in `requirements.txt` support the larger repo, but they are
not central to this mini repo.

## External Tests

Tests live outside the mini repo:

| Path | Purpose |
|---|---|
| `tests/test_self_eval_qa_lab.py` | Core single-run routing, trace health, repairs, artifact checks. |
| `tests/test_self_eval_qa_lab_dataset.py` | Dataset loader, parser, review cadence, batch policy. |
| `tests/test_self_eval_qa_lab_real_llm.py` | Opt-in real LLM smoke test. |
| `tests/test_mini_repo_registry.py` | Ensures registry aliases and command dispatch work. |

Run fast tests:

```powershell
python -m unittest tests.test_self_eval_qa_lab tests.test_self_eval_qa_lab_dataset tests.test_mini_repo_registry
```

Run all tests:

```powershell
python -m unittest discover -s tests
```

Run opt-in real LLM test:

```powershell
$env:RUN_SELF_EVAL_REAL_LLM="1"
python -m unittest tests.test_self_eval_qa_lab_real_llm
```

## External Network Dependency

Dataset download uses Hugging Face raw URLs from:

```text
experiments/self_eval_qa_lab/datasets/logikon_bench_manifest.json
```

Network is only needed when the dataset file is not already cached, or when
`--refresh-dataset` is used.

Cache path:

```text
var/self_eval_qa_lab/datasets/logikon-bench/
```

## External Files Not Required For This Mini Repo

These folders are part of the larger project but are not required for normal
`self_eval_qa_lab` runs:

```text
agents/
business_prompt_lab/
features/
mcp_servers/
orchestration/
output_gate/
skills/
```

They can coexist with the mini repo. The registry only touches them when running
other mini repos or the older root orchestrator path.
