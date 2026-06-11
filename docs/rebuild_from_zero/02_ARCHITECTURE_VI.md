# Architecture

## High-Level Architecture

```text
User / prompt file
  -> CLI entrypoint
  -> orchestrator / supervisor
  -> agent role
  -> LLM adapter
  -> JSON action
  -> JsonGate
  -> Agent Kernel
  -> Capability Registry
  -> feature adapter
  -> MCP client
  -> MCP server
  -> sandboxed side effect or read
  -> normalized CapabilityResult
  -> event log
  -> next agent step or final
```

## Kiến Trúc Theo Tầng

### 1. Interface Layer

Entry points:

- `main.py`: chạy single-agent orchestrator.
- `main_langgraph.py`: chạy LangGraph multi-agent pipeline.
- `run_*_smoke.py`: deterministic smoke runners.
- `run_*_demo.py`: manual demo runners.
- `run_all_cases.py`: prompt-based test runner.

Tầng này không nên chứa logic agent phức tạp. Nó chỉ đọc prompt, cấu hình
encoding/env, gọi runtime và in kết quả.

### 2. LLM Adapter Layer

File:

- `llm.py`

Trách nhiệm:

- Bọc OpenAI-compatible API.
- Mặc định trỏ tới LM Studio `http://localhost:1234/v1`.
- Cho phép override bằng env: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`,
  `LLM_TIMEOUT`, `LLM_MAX_TOKENS`.

Không nên để tool policy hoặc orchestration ở tầng này.

### 3. Agent Prompt And Role Layer

Files:

- `agents/base_agent.py`
- `agents/role_agents.py`
- `agents/lenses/`
- `prompts/system_prompt.md`
- `tools/prompt_loader.py`
- `tools/skill_loader.py`

Trách nhiệm:

- Render system prompt.
- Gắn tool prompt và skill prompt.
- Gắn role boundary và tool allowlist.
- Chặn output gọi tool ngoài quyền role.

Role chính:

- Research
- Planner
- Architect
- Code
- Test
- Review
- Ledger
- Final
- Tool Agent legacy

### 4. Output Gate Layer

Files:

- `output_gate/json_gate.py`
- `output_gate/repair_rules.py`
- `output_gate/repair_loop.py`

Trách nhiệm:

- Extract JSON từ raw LLM output.
- Repair deterministic lỗi phổ biến.
- Validate action schema.
- Resolve tool alias.
- Validate tool args theo schema.
- Dry-run safety cho path, terminal, git mutation, content size.

JsonGate là contract gate trước khi tool chạy thật.

### 5. Orchestration Layer

Files:

- `orchestrator.py`
- `orchestration/langgraph_orchestrator.py`
- `orchestration/company_orchestrator.py`
- `orchestration/software_factory_orchestrator.py`
- `orchestration/global_supervisor.py`
- `orchestration/intent_router.py`

Runtime hiện có:

```text
single-agent:
main.py -> orchestrator.py -> Tool Agent -> tool loop

langgraph:
main_langgraph.py -> research -> planner -> architect -> code -> test -> review -> ledger -> final

company v0.5:
ResearchAgent -> PlannerAgent -> ArchitectAgent -> CodeAgent -> TestAgent -> ReviewAgent -> LedgerAgent -> FinalAgent

software factory v0.7:
Vision -> BRD -> PRD -> Stories -> AC -> Domain -> Business Logic -> Technical -> Pattern -> Implementation Spec -> Handoff -> Docs

global supervisor:
IntentRouter -> Safety -> selected department(s) -> FinalSynthesisAgent
```

### 6. Agent Kernel Layer

Files:

- `core/kernel.py`
- `core/registry.py`
- `core/capabilities.py`
- `core/schemas.py`
- `core/bootstrap.py`
- `core/events.py`
- `core/state.py`
- `core/ports/`

Contract:

```text
core.capabilities.call_tool()
  -> AgentKernel.execute_tool()
  -> CapabilityRegistry.resolve_tool()
  -> ToolPort.execute()
  -> CapabilityResult envelope
```

Core không biết chi tiết browser, RAG, Docker, PDF, Obsidian. Những thứ đó nằm
sau feature adapter.

### 7. Feature Adapter Layer

Files:

- `features/loader.py`
- `features/contracts.py`
- `features/mcp_tools/`
- `config/features.yaml`

Hiện chỉ có feature chính:

- `mcp_tools`: routes kernel tool request sang MCP client/server.

Thiết kế đúng:

- Feature có descriptor.
- Feature khai báo capabilities.
- Feature khai báo tests.
- Feature removable.
- Nếu disable feature, kernel vẫn boot và trả missing capability thay vì crash.

### 8. MCP Tool Layer

Files:

- `features/mcp_tools/config.py`
- `features/mcp_tools/client.py`
- `features/mcp_tools/schemas.py`
- `features/mcp_tools/policy.py`
- `mcp_servers/*.py`

Luồng:

```text
tool name
  -> resolve alias/server.tool
  -> validate schema
  -> policy check
  -> normalize path/env
  -> start MCP stdio server
  -> call tool
  -> normalize result
```

MCP servers hiện có:

| Server | Vai trò |
|---|---|
| filesystem | External MCP, thao tác workspace |
| file_editor | edit có audit |
| python | chạy Python trong workspace |
| terminal | argv-only validation/probe |
| lint_test | compile/ruff/run file/smoke suite |
| git | git read-only, mutation bị block |
| code_index | index symbol/reference/import graph |
| rag | Qdrant ingest/search |
| fetch/search | web retrieval |
| document/pdf_text_extraction | document extraction/writing |
| ledger | JSONL audit memory |
| issue | SQLite issue tracker |
| docker | Docker status/logs, mutation opt-in |
| obsidian | local markdown vault |
| playwright | browser text/screenshot |
| context7 | library docs |

### 9. Persistence And Runtime Data Layer

Runtime directories:

- `var/workspace/`: sandbox workspace.
- `var/agent_runs/`: event logs.
- `var/test_runs/`: test run logs.
- `var/qdrant_storage/`: local Qdrant storage if configured.
- `workspace/`: legacy/generated workspace artifacts still present.

Artifact outputs:

- Software Factory: `var/workspace/factory_runs/<run_id>/`.
- Ledger: `var/workspace/ledger/ledger.jsonl` by default.
- Issues: `var/workspace/issues/issues.db` by default.

### 10. Quality Layer

Files:

- `run_dev_checks.py`
- `run_capability_suite.py`
- `run_all_cases.py`
- `tests/`
- `run_*_smoke.py`

Quality gates:

- compileall
- kernel contract tests
- feature contract tests
- JsonGate smoke
- role permission smoke
- MCP chain smoke
- LangGraph smoke
- Code/Test v0.5 smoke
- Company v0.5 smoke
- Software Factory smoke
- Global Supervisor smoke

## Core Data Contracts

### Agent Action

```json
{
  "action": "tool",
  "plan": "brief observable plan",
  "tool": "server.tool_name",
  "args": {}
}
```

```json
{
  "action": "final",
  "finish_reason": "validated|handoff|blocker|dependency_failure",
  "message": "..."
}
```

### Capability Result

```json
{
  "ok": true,
  "capability": "python.run_python",
  "feature": "mcp_tools",
  "data": {},
  "error": null,
  "metadata": {}
}
```

### Department Result v0.5

```json
{
  "agent": "code_agent",
  "version": "v0.5",
  "lens_results": [],
  "synthesis": {},
  "records": {},
  "route": {
    "next_agent": "test_agent",
    "reason": "Implementation is ready for QA validation."
  }
}
```

### Software Factory Stage Result

```json
{
  "agent": "BRD Agent",
  "department": "Business Analysis Department",
  "version": "v0.7",
  "ok": true,
  "decision": "artifact_created",
  "artifact_refs": [],
  "missing_inputs": [],
  "route": {
    "next_agent": "PRD Agent"
  }
}
```

## Các Boundary Quan Trọng

- Prompt rule không phải security boundary.
- JsonGate là contract gate, nhưng tool server vẫn phải tự sandbox.
- Code Agent được edit nhưng không tự approve.
- Test Agent validate nhưng không edit.
- Review Agent review nhưng không mutate git.
- Ledger ghi memory/audit nhưng không chạy code.
- Software Factory tạo spec, không claim đã implement.
- Global Supervisor route request, không tự bypass safety.

## Architecture Khi Rebuild

Khi viết lại repo mới, architecture đích nên giữ cùng boundary nhưng triển khai
ít hơn trước:

```text
Phase 1: CLI + LLM + JSON action
Phase 2: Event log + run summary
Phase 3: Kernel + capability result
Phase 4: File/Python tools tối thiểu
Phase 5: JsonGate
Phase 6: MCP adapter + schemas + policy
Phase 7: Test harness
Phase 8: Role agents
Phase 9: LangGraph/company orchestration
Phase 10: Software Factory artifacts
Phase 11: Global Supervisor
```

