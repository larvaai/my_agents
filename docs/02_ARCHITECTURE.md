# Architecture

## Agent Kernel Architecture

Project now has an explicit core boundary:

```text
User / Orchestrator / Agent
  -> core.capabilities.call_tool()
  -> core.AgentKernel
  -> core.CapabilityRegistry
  -> feature adapter
  -> concrete tool backend
```

The current concrete adapter is `features/mcp_tools.MCPToolAdapter`, which routes to
the existing MCP client and MCP servers.

```text
core/
  kernel.py       minimal living core
  registry.py     capability/feature registry
  events.py       in-process event bus
  state.py        in-memory state manager
  schemas.py      task/tool/feature contracts
  ports/          stable capability interfaces

features/
  mcp_tools/      adapter feature for existing MCP servers
  nulls.py        null fallback implementations

config/
  features.yaml
```

Design rule: core may know ports and feature descriptors, but it should not know
browser/RAG/Docker/PDF implementation details. Those stay behind adapters.

Smoke:

```powershell
python run_kernel_smoke.py
python run_feature_tests.py
```

## General Multi-Agent Path

Stage 1-6 is implemented. The tracking doc is
`docs/17_GENERAL_MULTI_AGENT_ROADMAP.md`.

```text
User request
  -> orchestration/global_supervisor.py
  -> orchestration/intent_router.py
  -> Safety Department when repo/code/web/agent-factory risk exists
  -> GENERAL_KNOWLEDGE -> Knowledge Department
  -> CODE_TASK -> existing Coding Department / Company Agents
  -> AGENT_CREATION -> Agent Factory path
  -> RESEARCH_REQUIRED -> Research Department
  -> MIXED_TASK -> sequential execution plan across departments
  -> Final Synthesis Agent
```

## High-Level Map

Project có hai đường chạy chính:

```text
Single-agent path:
main.py
  -> orchestrator.py
  -> agents/tool_agent.py
  -> llm.py
  -> JsonGate
  -> core.capabilities.call_tool()
  -> core.AgentKernel
  -> features/mcp_tools.MCPToolAdapter
  -> features/mcp_tools/client.py
  -> MCP server
  -> tool result
  -> orchestrator loop
```

```text
LangGraph path:
main_langgraph.py
  -> orchestration/langgraph_orchestrator.py
  -> research -> planner -> architect -> code -> test -> review -> ledger -> final
                                   \       ^       /
                                    -> tool node ->
                                       MCP servers
```

```text
Software Factory v0.7 path:
run_software_factory_demo.py
  -> orchestration/software_factory_orchestrator.py
  -> Intake Protocol -> Vision -> BRD -> PRD -> Story -> AC
  -> Product validation/critique
  -> Domain Analysis -> Business Logic Model/Validation
  -> Technical Analysis -> Pattern Decision
  -> Implementation Spec -> Code Handoff Packet
  -> Docs Orchestrator -> Repo Scanner -> API Extractor -> ADR -> Docs Writer -> Docs Verifier
  -> Final
  -> handoff to run_company_agents_demo.py --real
```

Single-agent path vẫn hữu ích cho prompt đơn giản và backward compatibility. LangGraph path là hướng coding-agent chính.

## User Agent Control Plane

The root single-agent path now has a live user control plane:

```text
User live input / control inbox
  -> agents/user_agent.py
  -> orchestrator.py checkpoint poll
  -> USER AGENT LIVE DIRECTIVES prompt block
  -> tool_agent follows latest accepted directive
```

If a directive arrives while the LLM call is running, the returned agent output
is marked stale and the next agent call receives the directive. This is a
checkpoint interrupt, not yet hard HTTP cancellation.

Full guide:

```text
docs/19_USER_AGENT_CONTROL.md
```

## Process Dashboard UI

The local UI starts and observes agent processes:

```text
run_process_ui.py
  -> static dashboard in ui/process_dashboard/
  -> subprocess main.py or main_langgraph.py
  -> var/agent_runs/<run_id>/events.jsonl
  -> User Agent control inbox for root runs
```

It is a process manager and run viewer. It does not replace the orchestrators;
it reads their event logs and writes user directives into the selected run's
control inbox.

Guide:

```text
docs/20_PROCESS_DASHBOARD_UI.md
```

## Core Layers

### Entry Points

| File | Vai trò |
|---|---|
| `main.py` | Đọc prompt và chạy `run_orchestrator()` |
| `main.py --interactive-user-agent ...` | Chạy root orchestrator với live User Agent directives |
| `main_langgraph.py` | Đọc prompt và chạy LangGraph orchestrator |
| `run_software_factory_demo.py` | Chay Software Factory v0.7 artifact-first spec pipeline |
| `run_process_ui.py` | Local web UI for process/state/log/User Agent control |
| `run_all_cases.py` | Prompt-based test runner |
| `run_langgraph_smoke.py` | Deterministic LangGraph smoke |
| `run_json_gate_smoke.py` | Deterministic JsonGate smoke |
| `run_agent_role_smoke.py` | Role/tool/lens permission smoke |

### LLM Layer

`llm.py` gọi LM Studio hoặc OpenAI-compatible API.

Mặc định project hướng tới local model:

```text
base_url = http://localhost:1234/v1
```

### Output Gate Layer

`output_gate/` là cổng kiểm mọi action JSON từ agent.

Files:

- `output_gate/json_gate.py`
- `output_gate/repair_rules.py`
- `output_gate/repair_loop.py`

Nhiệm vụ:

- Extract JSON từ raw output.
- Repair deterministic lỗi phổ biến.
- Validate action schema.
- Resolve tool name và alias.
- Validate tool args theo `features/mcp_tools/schemas.py`.
- Dry-run safety: path, terminal argv, git policy, content size.

Nếu fail, JsonGate trả lỗi có stage:

```text
parse
action_schema
tool_resolve
tool_args
dry_run
```

Orchestrator gửi lỗi đó về agent để sửa đúng chỗ.

### Agent Layer

Files:

- `agents/base_agent.py`
- `agents/role_agents.py`
- `agents/role_config.py`
- `config/agents.yaml`
- `config/roles/*.yaml`
- `agents/tool_agent.py`
- `agents/user_agent.py`
- `agents/lenses/`

`BaseAgent`:

- Build system prompt.
- Gắn role, department, lenses.
- Gắn allowed tools và skills.
- Guard output ngoài allowlist.

`role_agents.py` chỉ load config. Role permissions, allowed tools, allowed
skills, route permissions, test ownership, và lens group nằm trong
`config/roles/*.yaml`.

Các role hiện có:

- Research
- Planner
- Architect
- Code
- Test
- Review
- Ledger
- Final
- Tool Agent backward-compatible

### Department Lens Layer

`agents/lenses/` contains role lenses for all core departments:

```text
Research Department
  -> source_scout
  -> source_credibility
  -> fact_check
  -> synthesis
  -> knowledge_curator

Planning Department
  -> product_manager
  -> project_manager
  -> dependency_planner
  -> risk_manager
  -> scope_control

Architecture Department
  -> system_architect
  -> data_architect
  -> api_contract
  -> security_architect
  -> scalability

Engineering Department
  -> implementation
  -> integration
  -> defensive_coding
  -> refactor_discipline
  -> developer_experience

QA Department
  -> logic
  -> critical_thinking
  -> experienced_qa
  -> regression
  -> edge_case
  -> purpose_alignment
  -> test_executor

Senior Review Board
  -> senior_engineer
  -> scope_diff
  -> security_review
  -> maintainability
  -> release_risk

Ledger / Audit / Operations
  -> historian
  -> task_state
  -> decision_record
  -> auditor
  -> incident_tracker

Final / Communication
  -> executive_summary
  -> technical_writer
  -> user_facing_explanation
  -> limitation_disclosure
  -> next_step_recommendation
```

Lens hiện là prompt/spec layer. Chúng không tự chạy tool, không tự loop, không tự quyết định.

### MCP Layer

Files:

- `core/`
- `features/mcp_tools/`
- `features/mcp_tools/config.py`
- `features/mcp_tools/client.py`
- `features/mcp_tools/schemas.py`
- `features/mcp_tools/policy.py`
- `mcp_servers/`

Kernel/tool path lam:

1. `core.capabilities.call_tool()` asks the default kernel to execute a tool.
2. `core.AgentKernel.execute_tool()` emits events and asks the registry for an
   executor.
3. `core.CapabilityRegistry` returns an exact capability, fallback adapter, or
   null tool.
4. `features.mcp_tools.MCPToolAdapter` delegates to the existing MCP client.
5. Kernel returns a pure `CapabilityResult` envelope.

Capability result schema:

```text
ok: bool
capability: str
feature: str | None
data: dict
error: str | None
metadata: dict
```

Tool-specific payload such as stdout, text, hits, results, or path lives under
`data`. Request ids, executor names, and adapter metadata live under
`metadata`.

MCP client sau do lam:

1. Resolve alias hoặc `server.tool`.
2. Validate args theo schema cứng.
3. Check policy.
4. Start MCP server qua stdio.
5. Call tool.
6. Normalize result về dict.

### Event Log Layer

Files:

- `tools/event_log.py`
- `tools/event_reader.py`
- `inspect_runs.py`

Logs:

```text
var/agent_runs/<run_id>/events.jsonl
var/agent_runs/<run_id>/summary.json
var/test_runs/<timestamp>/
```

Event types:

- `MessageEvent`
- `ActionEvent`
- `ObservationEvent`
- `StateEvent`
- `ErrorEvent`

## LangGraph State

`orchestration/agent_state.py` định nghĩa shared state.

Các field quan trọng:

| Field | Ý nghĩa |
|---|---|
| `messages` | Lịch sử hội thoại/tool result đã nén |
| `next_agent` | Node tiếp theo |
| `last_agent` | Role vừa chạy |
| `required_files` | File prompt yêu cầu |
| `missing_files` | File còn thiếu |
| `files_modified` | File đã thay đổi |
| `tests_run` | Validation evidence |
| `last_failure` | Tóm tắt failure mới nhất |
| `repair_attempts` | Đếm repair theo signature |
| `role_visits` | Budget theo role |
| `subtask_visits` | Budget theo subtask |
| `repeated_tool_calls` | Guard lặp tool call |
| `json_retries` | Retry output JSON lỗi |

## Repair Mode Sau Failed Test

Khi Test Agent chạy validation fail:

```text
tool_result ok=false
  -> extract traceback/error
  -> last_failure = {file, line, function, error, stderr_tail}
  -> repair_attempts[signature] += 1
  -> route back to Code
```

Khi Code Agent đang ở repair mode:

- Được patch file lỗi bằng `file_editor.file_editor_str_replace` hoặc `file_editor.file_editor_insert`.
- Bị chặn nếu cố rewrite nguyên file đang fail bằng `filesystem.write_file`, `file_editor_create`, hoặc `file_editor_write_lines`.

Mục tiêu: sửa theo giả thuyết nhỏ, không viết lại đại trà.

## Finish Gate

Coding task không được final “xong” nếu chưa có validation evidence.

Rule:

```text
code changed
  -> validation required
  -> pass: có thể final
  -> fail: route về Code hoặc báo blocker rõ
```

Prompt có sentinel như `SOCIETY_SIM_TESTS_OK` hoặc `LANGGRAPH_SMOKE_OK` thì finish gate yêu cầu stdout chứa token đó.

## Context Condenser

Tool result lớn không được nhồi nguyên vào prompt.

Orchestrator chỉ giữ:

- `ok`
- `tool`
- `path`
- `stdout/stderr` đã cắt
- `error`
- `metadata`
- vài item đầu của list lớn

Full data vẫn nằm trong event log.

## Design Principles

- Tool schema là contract, không phải gợi ý.
- Terminal chỉ dùng validation/probe, không edit file.
- File Editor MCP là đường edit chính.
- Test Agent sở hữu validation.
- Code Agent không tự approve.
- Review Agent không edit.
- Ledger Agent ghi và audit, không thực thi code.
- JsonGate chặn output sai trước khi tool chạy.
- Logs phải đủ để replay/debug run.

## Code/Test Department v0.5 Path

The project also has a focused Code/Test v0.5 path:

```text
run_code_test_agents_demo.py
  -> orchestration/code_test_orchestrator.py
  -> agents/code_agent.py
  -> agents/test_agent.py
  -> core.capabilities.call_tool()
  -> MCP tools
```

This path does not replace the main LangGraph pipeline yet. It is a small
department-level proving ground for route decisions.

v0.5 behavior:

- Code Agent runs engineering lenses, synthesizes an implementation decision,
  executes through a gated file-editor executor, records ledger/issue data, and
  routes to Test Agent.
- Test Agent runs QA lenses, synthesizes a validation plan, executes only
  allowlisted validation/read tools, records ledger/issue data, and routes to
  Review Agent or back to Code Agent.
- The orchestrator reads `route.next_agent` from each result instead of relying
  on free-form prose.

Smoke:

```powershell
python run_code_test_agents_smoke.py
```

Full guide:

```text
docs/14_CODE_TEST_V05.md
```

## Full Company Agents v0.5 Path

The project also has a deterministic full-company v0.5 path:

```text
run_company_agents_demo.py
  -> orchestration/company_orchestrator.py
  -> ResearchAgent
  -> PlannerAgent
  -> ArchitectAgent
  -> CodeAgent
  -> TestAgent
  -> ReviewAgent
  -> LedgerAgent
  -> FinalAgent
```

This path uses the same department principle as LangGraph, but keeps the runtime
small and directly testable. Each department returns:

```text
agent + version + lens_results + synthesis + records + route
```

Smoke:

```powershell
python run_company_agents_smoke.py
```

Full guide:

```text
docs/15_COMPANY_AGENTS_V05.md
```

## Software Factory v0.7 Path

Complex product prompts should not jump directly from user idea to code. v0.7
adds an artifact-first specification room:

```text
Intake Protocol -> Vision -> BRD -> PRD -> Epic/Story -> Acceptance Criteria
  -> Product Spec Validator/Critic
  -> Domain Analysis + Change Hotspots
  -> Business Logic Model + Business Logic Validation
  -> Technical Analysis
  -> Pattern Decision with evidence
  -> Implementation Spec + Code Handoff Packet
  -> Documentation verification
```

The important protocol change is that long analysis is stored in artifacts:

```text
var/workspace/factory_runs/<run_id>/*.md
var/workspace/factory_runs/<run_id>/*.json
```

The JSON envelope stays small:

```text
agent + decision + route + artifact_refs + missing_inputs + metadata
```

This adapts the strict JSON protocol to business/domain work without weakening
the coding/tool-call protocol.

Smoke:

```powershell
python run_software_factory_smoke.py
```

Full guide:

```text
docs/16_SOFTWARE_FACTORY_V06.md
```
