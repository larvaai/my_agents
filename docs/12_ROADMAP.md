# Roadmap

Roadmap này ưu tiên làm project thành coding-agent ổn định trước khi thêm nhiều capability mới.

## Done

### Protocol And Safety

- JSON-only agent protocol.
- JsonGate deterministic repair.
- Action schema validation.
- Tool resolve and alias repair.
- Tool args schema validation.
- Dry-run safety check.
- Git mutation policy.
- Terminal argv-only policy.

### MCP System

- MCP stdio client.
- Hard schemas in `tools/tool_schemas.py`.
- Filesystem MCP.
- File Editor MCP.
- Python Sandbox MCP.
- Terminal MCP with risk metadata.
- Git MCP.
- Context7 MCP.
- RAG MCP.
- Fetch MCP.
- Search MCP.
- Document MCP.
- Ledger MCP.
- Playwright MCP.
- Code Index MCP.
- Lint/Test MCP.
- Docker MCP.
- Obsidian MCP.
- Issue Tracker MCP.

### Agent System

- BaseAgent.
- Role registry.
- Research, Planner, Architect, Code, Test, Review, Ledger, Final agents.
- Role tool allowlists.
- Department model for 4 core agents:
  - Engineering
  - QA
  - Senior Review
  - Ledger/Ops
- Department lenses v0.1.
- Code/Test Department runtime v0.5:
  - lens results
  - synthesis
  - gated executor
  - ledger/issue integration
  - route decision

### Orchestration

- Single-agent ReAct orchestrator.
- LangGraph role pipeline.
- Tool node.
- Role budgets.
- Subtask budgets.
- Required/missing file tracking.
- Failed-test repair loop.
- Finish gate.
- Context condenser.

### Testing And Logs

- `run_all_cases.py`.
- `run_json_gate_smoke.py`.
- `run_agent_role_smoke.py`.
- `run_langgraph_smoke.py`.
- `run_mcp_chain_smoke.py`.
- Event logs.
- Inspect CLI.
- `society_sim` generated artifact test.

### Docs

- Full docs tree.
- ADRs.
- MCP docs.
- Agent docs.
- Workflows/templates.
- Department lenses docs.

## Historical Plan: v0.2-v0.4

The sections below are preserved as historical staged-plan notes. The project
has already implemented a direct Code/Test v0.5 runner, so future work should
focus on integrating that v0.5 layer into LangGraph instead of replaying each
older intermediate version.

## Next: v0.2

### Better Department Lens Execution

Current lenses are prompt/spec only. Next:

- Let Test Agent synthesize explicit `department_report`.
- Let Code Agent include compact engineering lens notes before edit.
- Let Review Agent output structured review board decision.
- Let Ledger Agent audit consistency automatically.

Keep lens execution bounded. Do not let lenses become free-running agents yet.

### Better Handoff Schema

Add common department report schema:

```json
{
  "department_report": {
    "agent": "test_agent",
    "lens_results": [],
    "decision": "approve|request_changes|blocked|needs_more_info",
    "confidence": "low|medium|high",
    "required_next_actions": []
  }
}
```

### Test Council v0.2

- QA lenses produce a test plan.
- Test Executor runs validation.
- Test Agent returns structured classification:
  - code logic failure
  - test gap
  - dependency failure
  - environment/tool failure
  - blocker

### Ledger/Ops v0.2

- Auto-record run summaries when task touches code.
- Create issue for repeated failure signatures.
- Audit mismatch: final success but tests failed.

## Next: v0.3

### Sub-Agent Lens Calls

Move selected lenses from prompt-only to bounded LLM calls:

- No tools for reasoning lenses.
- Strict JSON schema.
- Max one call per lens.
- Department agent synthesizes.

Start with QA:

- logic
- critical_thinking
- experienced_qa
- purpose_alignment

Keep `test_executor` as the only tool-running QA component.

### Context Condenser v2

Improve context selection:

- Keep file diffs.
- Keep last failure summary.
- Keep validation output tail.
- Drop repeated tool schemas.
- Keep only active task files.

### Patch Planner

After failed test:

- Generate one repair hypothesis.
- Patch smallest span.
- Test again.
- Stop after repair budget and report blocker.

## Next: v0.4

### UI And Run Viewer

- View `agent_runs`.
- View tool timeline.
- View current `AgentState`.
- View role budgets and repair attempts.
- View ledger/issues.

### Permission Matrix UI

- Inspect allowed tools per role.
- Inspect lens list per department.
- Explain why a tool was blocked.

### MCP Process Pooling

Current stdio startup is simple but can be slow. Later:

- Pool long-lived MCP server processes.
- Keep same schema/policy boundaries.

## Later

- Workspace snapshots/rollback.
- Multi-agent scheduler.
- Planner/Research/Architect lenses.
- RAG reranker and metadata filters.
- Better issue/task queue.
- Human approval gate for high-risk actions.
- Local browser UI for agent status.

## Not A Priority Now

- Agent auto commit/push.
- Full shell access.
- Many autonomous sub-agents without strict schema.
- Network-heavy tools without source/policy discipline.
- Large UI before core loop is stable.

## Guiding Principle

Make the agent boringly reliable before making it flashy.

Reliability means:

- Tool calls are valid.
- Edits are auditable.
- Tests run.
- Failures route to the right role.
- Final answer has evidence.

## Current: Code/Test v0.5 Implemented

The project now includes a direct v0.5 Code/Test department loop:

- `agents/code_agent.py`
- `agents/test_agent.py`
- `orchestration/code_test_orchestrator.py`
- `run_code_test_agents_demo.py`
- `run_code_test_agents_smoke.py`

This skips the older staged rollout and implements the full v0.5 behavior:

- lens results
- synthesis
- gated executor
- ledger/issue integration
- route decision

The v0.5 layer is still separate from the main LangGraph path. Keep it that way
until the dedicated smoke and existing LangGraph smoke stay stable together.
