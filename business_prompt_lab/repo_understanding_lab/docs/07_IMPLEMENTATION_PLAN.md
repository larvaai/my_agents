# Implementation Plan

This plan starts with simple stdlib code. Heavy code-intelligence tools should
be optional later.

## Step 1 - Scaffold Runtime

Add:

```text
main.py
repo_understanding/
  __init__.py
  schemas.py
  scanner.py
  manifests.py
  symbols.py
  graphs.py
  context_pack.py
```

CLI:

```powershell
python business_prompt_lab/repo_understanding_lab/main.py --help
python business_prompt_lab/repo_understanding_lab/main.py --mock baseline
```

## Step 2 - File Scanner

Build:

- ignore rules
- file inventory
- language guess
- role guess
- hash

Avoid scanning:

- `.git`
- `__pycache__`
- `node_modules`
- `.venv`
- large binary files
- runtime output under `var/`

## Step 3 - Manifest Reader

Support first:

- `requirements.txt`
- `pyproject.toml`
- `package.json`
- `docker-compose.yml`
- `.github/workflows/*.yml`

Return structured findings and confidence.

## Step 4 - Python Symbol Extractor

Use stdlib `ast` first.

Extract:

- imports
- classes
- functions
- methods
- decorators
- constant assignments
- call-like names

Limitations should be explicit in output.

## Step 5 - Graph Builder

Build a simple JSON graph:

- file defines symbol
- file imports package/module
- symbol calls name
- test file likely tests source file
- docs mention file/symbol

Do not pretend the graph is perfect.

## Step 6 - Context Packer

Input:

- question
- maps
- route
- entity hits

Output:

- bounded `ContextPack`
- evidence summaries
- unknowns

## Step 7 - Observer

Start deterministic:

- check final answer citations
- check unsupported strong words
- check missing tests when a code symbol is discussed
- check whether docs/code conflict was acknowledged

Later add LLM observer through `llm.py`.

## Step 8 - Registry

Register only after the mock runner and tests exist:

```text
tools/mini_repo_registry.py
tests/test_mini_repo_registry.py
```

Suggested command:

```powershell
python main.py lab repo-understanding --mock ask "Where is the entrypoint?"
```

## Step 9 - Graduation

If useful, graduate stable pieces into:

- `tools/` for reusable scanners/indexers
- `orchestration/` for LangGraph integration
- `ui/` for process dashboard visibility
- `agents/` for official role prompts

