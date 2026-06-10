# Code/Test Agents v0.5

This document describes the direct v0.5 implementation for the Code Agent and Test Agent department loop.

The project skipped the earlier staged rollout in the pasted reference and implemented the complete v0.5 behavior directly:

- Code Agent has engineering lenses, synthesis, a gated executor, ledger/issue recording, and route decisions.
- Test Agent has QA lenses, synthesis, an allowlisted test executor, ledger/issue recording, and route decisions.
- A small `CodeTestOrchestrator` routes between the two departments by reading each agent result.
- The runner is separate from the main LangGraph path so it can be tested safely before broader integration.

## Files

| File | Purpose |
|---|---|
| `agents/code_agent.py` | Code Agent v0.5 runtime |
| `agents/test_agent.py` | Test Agent v0.5 runtime |
| `orchestration/code_test_orchestrator.py` | Code/Test v0.5 route loop |
| `run_code_test_agents_demo.py` | Manual demo runner |
| `run_code_test_agents_smoke.py` | Deterministic smoke test |
| `agents/lenses/base_lens.py` | Shared `LensResult` and JSON lens helpers |

## Why Deterministic By Default

The runner defaults to deterministic lenses instead of LLM lens calls.

Reason:

- It gives a fast, stable smoke test.
- It avoids local-model JSON drift while validating the architecture.
- It still preserves the v0.5 contract: lens output, synthesis, executor plan, tool execution, ledger/issue recording, and route decision.

To experiment with actual LLM lens calls:

```powershell
python run_code_test_agents_demo.py --version v0.5 --agent orchestrator --use-llm
```

## Code Agent v0.5 Flow

```text
task
  -> engineering lenses
  -> synthesis
  -> code_executor plan
  -> file_editor tool execution
  -> ledger append
  -> optional issue create on failure
  -> route decision
```

Code executor allowed tools:

```text
file_editor.file_editor_write_lines
file_editor.file_editor_create
```

Default route rules:

| Condition | Next |
|---|---|
| synthesis is blocked or needs info | `planner_agent` |
| executor failed | `code_agent` |
| executor passed | `test_agent` |

## Test Agent v0.5 Flow

```text
code_result
  -> QA lenses
  -> test synthesis
  -> allowlisted test executor
  -> ledger append
  -> optional issue create on failure
  -> route decision
```

Test executor allowed tools:

```text
python.run_python
lint_test.lint_compile
lint_test.lint_ruff_check
lint_test.lint_ruff_format_check
lint_test.test_python_file
filesystem.read_file
filesystem.read_text_file
git.git_diff_unstaged
code_index.code_index
code_index.code_find_symbol
code_index.code_find_references
```

Default route rules:

| Condition | Next |
|---|---|
| no validation plan | `planner_agent` |
| validation failed | `code_agent` |
| validation passed | `review_agent` |

## Orchestrator v0.5 Flow

```text
Code Agent
  route: test_agent
Test Agent
  pass -> review_agent
  fail -> code_agent
  blocked -> planner_agent
```

The v0.5 orchestrator stops with:

- `ready_for_review` when QA passes.
- `blocked_needs_planning` when a department cannot proceed.
- `blocked_after_code` when Code Agent routes somewhere unexpected.
- `max_cycles_reached` when repeated Code/Test repair cycles do not converge.

## Commands

Run the stable smoke:

```powershell
python run_code_test_agents_smoke.py
```

Expected marker:

```text
CODE_TEST_AGENTS_V05_SMOKE_OK
```

Run the demo:

```powershell
python run_code_test_agents_demo.py --version v0.5 --agent orchestrator --max-cycles 2
```

Run only Code Agent:

```powershell
python run_code_test_agents_demo.py --version v0.5 --agent code
```

Run Code plus Test Agent:

```powershell
python run_code_test_agents_demo.py --version v0.5 --agent test
```

Use a task file:

```powershell
python run_code_test_agents_demo.py --version v0.5 --task-file prompts/user_prompt.md
```

## Current Scope

The direct v0.5 layer is intentionally narrow.

It currently handles small Python file generation and validation well. It is a proving ground for the department routing model, not yet a replacement for the main LangGraph coding pipeline.

Next integration step:

```text
main_langgraph.py
  -> optional Code/Test v0.5 department runtime
  -> existing Review/Ledger/Final path
```

Keep this step separate until the v0.5 smoke and the existing LangGraph smoke both stay green.
