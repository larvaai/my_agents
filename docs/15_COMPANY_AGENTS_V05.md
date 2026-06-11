# Company Agents v0.5

This document describes the full department-style v0.5 runtime.

The project now has a complete local coding-agent company chain:

```text
Research Agent
  -> Planner Agent
  -> Architect Agent
  -> Code Agent
  -> Test Agent
  -> Review Agent
  -> Ledger Agent
  -> Final Agent
```

The goal is not to create many free-running agents. The goal is to make each
role accountable, bounded, testable, and easy to inspect.

## Files

| File | Purpose |
|---|---|
| `agents/department_v05.py` | Shared helpers for v0.5 department runtimes |
| `agents/research_agent.py` | Research Department runtime |
| `agents/planner_agent.py` | Planning Department runtime |
| `agents/architect_agent.py` | Architecture Department runtime |
| `agents/code_agent.py` | Engineering Department runtime |
| `agents/test_agent.py` | QA Department runtime |
| `agents/review_agent.py` | Senior Review Board runtime |
| `agents/ledger_agent.py` | Ledger / Audit / Operations runtime |
| `agents/final_agent.py` | Communication Department runtime |
| `orchestration/company_orchestrator.py` | Full company v0.5 route chain |
| `run_company_agents_demo.py` | Manual runner with JSON output |
| `run_company_agents_smoke.py` | Stable deterministic smoke |

## Core Contract

Every department runtime returns the same shape:

```json
{
  "agent": "research_agent",
  "version": "v0.5",
  "lens_results": [],
  "synthesis": {
    "decision": "ready_for_planning"
  },
  "records": {},
  "route": {
    "next_agent": "planner_agent",
    "reason": "Research context is ready for planning."
  }
}
```

The orchestrator routes by `route.next_agent`. It does not infer state from
prose.

## Department Lenses

Research:

- `source_scout`
- `source_credibility`
- `fact_check`
- `synthesis`
- `knowledge_curator`

Planning:

- `product_manager`
- `project_manager`
- `dependency_planner`
- `risk_manager`
- `scope_control`

Architecture:

- `system_architect`
- `data_architect`
- `api_contract`
- `security_architect`
- `scalability`

Engineering:

- `implementation`
- `integration`
- `defensive_coding`
- `refactor_discipline`
- `developer_experience`

QA:

- `logic`
- `critical_thinking`
- `experienced_qa`
- `regression`
- `edge_case`
- `purpose_alignment`
- `test_executor`

Review:

- `senior_engineer`
- `scope_diff`
- `security_review`
- `maintainability`
- `release_risk`

Ledger/Ops:

- `historian`
- `task_state`
- `decision_record`
- `auditor`
- `incident_tracker`

Final/Communication:

- `executive_summary`
- `technical_writer`
- `user_facing_explanation`
- `limitation_disclosure`
- `next_step_recommendation`

Rule:

```text
Lenses suggest.
Department agents synthesize.
Executor tools perform actions.
The orchestrator routes.
The finish gate requires evidence.
```

## Route Gates

Default successful path:

```text
research_agent -> planner_agent
planner_agent -> architect_agent
architect_agent -> code_agent
code_agent -> test_agent
test_agent -> review_agent
review_agent -> ledger_agent
ledger_agent -> final_agent
final_agent -> done
```

Repair path:

```text
test_agent fail -> code_agent
review_agent request_changes -> code_agent
```

Blocked path:

```text
research/planner/architect/test can route to planner_agent when scope or validation is missing
```

## Why Deterministic By Default

The full v0.5 runner defaults to deterministic lens results.

Reasons:

- Smoke tests do not depend on local LLM stability.
- The route contract can be tested quickly.
- Ledger/issue/tool behavior can be verified before adding model variance.
- You can still pass `--use-llm` to experiment with model-generated lens JSON.

## Commands

Run the full stable smoke:

```powershell
python run_company_agents_smoke.py
```

Expected marker:

```text
COMPANY_AGENTS_V05_SMOKE_OK
```

Run the full demo and inspect JSON:

```powershell
python run_company_agents_demo.py --version v0.5 --max-cycles 2
```

Run with a task file:

```powershell
python run_company_agents_demo.py --version v0.5 --task-file prompts/auto_cases/test_company_agents_v05.md
```

Experiment with LLM lens calls:

```powershell
python run_company_agents_demo.py --version v0.5 --task-file prompts/auto_cases/test_company_agents_v05.md --use-llm
```

Run the real company pipeline through LangGraph, MCP tools, JsonGate, repair
routing, and finish gates:

```powershell
python run_company_agents_demo.py --real --task-file prompts/the_sims_prompt.md --real-max-steps 260
```

Use `--real` for real prompt execution. Without `--real`, the runner stays in
deterministic contract-smoke mode.

## Smoke Behavior

The smoke asks the company chain to create:

```text
var/workspace/code/company_v05_smoke.py
```

The generated file prints:

```text
COMPANY_AGENTS_V05_OK
```

QA runs the generated Python file through `python.run_python` and checks stdout.
Review approves only after QA passes. Ledger records the approved run. Final
returns `done`.

## Current Scope

This v0.5 runtime proves the full company architecture. It is intentionally
small and stable.

It is good for:

- verifying role boundaries
- verifying department lenses
- verifying Code/Test executor gates
- verifying review/ledger/final route gates
- inspecting full-chain JSON logs

It is not yet the replacement for every large autonomous coding prompt. The main
LangGraph pipeline is still the primary LLM-driven path for broad tasks, while
this v0.5 runtime is the clean contract target.

## Pass Criteria

A full company run is successful only when:

- Code Agent writes the scoped artifact through File Editor.
- Test Agent runs real validation.
- Review Agent approves based on passing evidence.
- Ledger Agent records the final state.
- Final Agent routes to `done`.

No department should claim success without the downstream gate that owns that
responsibility.
