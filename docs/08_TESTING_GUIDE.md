# Testing Guide

## Test Layers

Project có nhiều lớp test, từ deterministic đến LLM-driven.

| Layer | Runner | Phụ thuộc LLM | Mục tiêu |
|---|---|---|---|
| Compile | `python -m py_compile ...` | Không | Bắt lỗi syntax/import |
| JsonGate | `run_json_gate_smoke.py` | Không | Kiểm JSON repair, schema, dry-run |
| Role permission | `run_agent_role_smoke.py` | Không | Kiểm role allowlist và department lenses |
| Company v0.5 | `run_company_agents_smoke.py` | Không | Kiểm full Research/Planner/Architect/Code/Test/Review/Ledger/Final chain |
| LangGraph compile | `run_langgraph_smoke.py` | Không | Build graph, repair guard, failure capture |
| MCP chain | `run_mcp_chain_smoke.py` | Không | Test tool chain thật không qua LLM |
| Prompt cases | `run_all_cases.py` | Có | Test agent thật qua prompt |
| Generated artifact | `workspace/society_sim/test_society_sim.py` | Không | Test artifact sinh từ prompt lớn |

## Quick Smoke

Chạy sau khi sửa core:

```powershell
python run_json_gate_smoke.py
python run_agent_role_smoke.py
python run_company_agents_smoke.py
python run_langgraph_smoke.py
```

Chạy group LangGraph:

```powershell
python run_all_cases.py --group langgraph --timeout 180 --fail-fast
```

Nếu sửa MCP:

```powershell
python run_mcp_chain_smoke.py
```

Nếu sửa artifact `society_sim`:

```powershell
python .\workspace\society_sim\test_society_sim.py
```

## JsonGate Tests

`run_json_gate_smoke.py` kiểm:

- Fenced JSON + trailing comma.
- Unquoted keys.
- Safe aliases.
- Unsafe path blocked.
- Terminal command string rejected.
- Git mutation policy blocked.
- Final message accepted.

Expected marker:

```text
JSON_GATE_SMOKE_OK
```

## Role And Lens Tests

`run_agent_role_smoke.py` kiểm:

- Research không edit.
- Planner không edit source.
- Code edit được nhưng không validate trong LangGraph split.
- Test validate được nhưng không edit.
- Review diff được nhưng không commit.
- Ledger ghi memory được nhưng không terminal.
- Final read-only.
- All core roles có đúng lens:
- Code: implementation, integration, defensive_coding, refactor_discipline, developer_experience
- Test: logic, critical_thinking, experienced_qa, regression, edge_case, purpose_alignment, test_executor
- Review: senior_engineer, scope_diff, security_review, maintainability, release_risk
- Ledger: historian, task_state, decision_record, auditor, incident_tracker
- Research: source_scout, source_credibility, fact_check, synthesis, knowledge_curator
- Planner: product_manager, project_manager, dependency_planner, risk_manager, scope_control
- Architect: system_architect, data_architect, api_contract, security_architect, scalability
- Final: executive_summary, technical_writer, user_facing_explanation, limitation_disclosure, next_step_recommendation

## Company v0.5 Tests

`run_company_agents_smoke.py` kiểm:

- Research routes to Planner.
- Planner routes to Architect.
- Architect routes to Code.
- Code writes a scoped Python artifact through File Editor.
- Test runs `python.run_python` and checks stdout.
- Review approves only after QA passes.
- Ledger records the approved run.
- Final routes to `done`.

Expected marker:

```text
COMPANY_AGENTS_V05_SMOKE_OK
```

For a real prompt run through the full company pipeline:

```powershell
python run_company_agents_demo.py --real --task-file prompts/the_sims_prompt.md --real-max-steps 260
```

The real mode requires LM Studio/OpenAI-compatible server to be running.

## LangGraph Tests

`run_langgraph_smoke.py` kiểm:

- Graph compile.
- State keys đầy đủ.
- Repair guard chặn whole-file rewrite khi đang repair failed test.
- Failure capture tạo `last_failure` và `repair_attempts`.

Expected markers:

```text
LANGGRAPH_COMPILE_OK
LANGGRAPH_REPAIR_GUARD_OK
LANGGRAPH_FAILURE_CAPTURE_OK
```

## Prompt Test Runner

`run_all_cases.py` chạy prompt qua orchestrator.

List case:

```powershell
python run_all_cases.py --list
```

Run group:

```powershell
python run_all_cases.py --group project --fail-fast
python run_all_cases.py --group chain --fail-fast
python run_all_cases.py --group mcp_ext --fail-fast
python run_all_cases.py --group rag --fail-fast
python run_all_cases.py --group langgraph --fail-fast
python run_all_cases.py --group skill --fail-fast
```

Run one case:

```powershell
python run_all_cases.py --case agent_01_fix_small_bug --fail-fast
```

Logs:

```text
test_runs/<timestamp>/<case>.log
test_runs/<timestamp>/summary.md
test_runs/<timestamp>/summary.json
```

## How To Test A User Prompt Manually

1. Viết prompt vào file:

```text
prompts/user_prompt.md
```

2. Chạy single-agent:

```powershell
python main.py prompts/user_prompt.md
```

3. Chạy LangGraph:

```powershell
python main_langgraph.py prompts/user_prompt.md
```

4. Đọc event log:

```powershell
python inspect_runs.py list
python inspect_runs.py events latest --limit 50
```

## Test Matrix

| Khi sửa | Test tối thiểu |
|---|---|
| `output_gate/*` | `run_json_gate_smoke.py` |
| `agents/base_agent.py` | `run_agent_role_smoke.py` |
| `agents/role_agents.py` | `run_agent_role_smoke.py` |
| `agents/lenses/*` | `run_agent_role_smoke.py` |
| `orchestrator.py` | Prompt case nhỏ + JsonGate smoke |
| `orchestration/langgraph_orchestrator.py` | `run_langgraph_smoke.py`, `--group langgraph` |
| `tools/tool_schemas.py` | `run_json_gate_smoke.py`, affected MCP case |
| `tools/mcp_client.py` | `run_mcp_chain_smoke.py` |
| `mcp_servers/file_editor_server.py` | direct tool smoke + role smoke |
| `mcp_servers/lint_test_server.py` | `--group mcp_ext`, `run_langgraph_smoke.py` |
| `mcp_servers/rag_server.py` | `--group rag` |
| Docs only | no compile required, but run nearby smoke if command examples changed |

## Pass Criteria For Coding-Agent Behavior

Một run tốt phải có:

- Tool call JSON qua JsonGate.
- File edit qua File Editor MCP hoặc allowed filesystem tool.
- Test Agent chạy validation thật.
- Nếu test fail, Code Agent repair hẹp.
- Review Agent xem evidence.
- Ledger Agent ghi nếu có giá trị audit.
- Final Agent chỉ báo pass khi finish gate có evidence.

## Common Failure Classes

| Failure | Cách đọc |
|---|---|
| `JSON_GATE_FAILED` | Agent output sai contract |
| `schema_error` | Tool args sai schema |
| `policy_blocked` | Tool bị hard policy chặn |
| `repair_requires_patch_tool` | Code Agent cố rewrite file khi đang repair |
| `finish_gate_blocked` | Agent muốn final khi thiếu validation |
| `dependency_failure` | Tool ngoài thiếu dependency |
| `agent_stuck` | Tool call lặp quá nhiều |

## Before Merging A Change

Tối thiểu:

```powershell
python -m py_compile agents\base_agent.py agents\role_agents.py orchestration\langgraph_orchestrator.py output_gate\json_gate.py tools\tool_schemas.py
python run_json_gate_smoke.py
python run_agent_role_smoke.py
python run_company_agents_smoke.py
python run_langgraph_smoke.py
```

Nếu change động tới MCP:

```powershell
python run_mcp_chain_smoke.py
```

Nếu change động tới prompt runner:

```powershell
python run_all_cases.py --group langgraph --timeout 180 --fail-fast
```

## Code/Test v0.5 Tests

The Code/Test v0.5 layer has its own deterministic smoke.

```powershell
python run_code_test_agents_smoke.py
```

Expected marker:

```text
CODE_TEST_AGENTS_V05_SMOKE_OK
```

Manual demo:

```powershell
python run_code_test_agents_demo.py --version v0.5 --agent orchestrator --max-cycles 2
```

This runner does not require LLM by default. Add `--use-llm` only when you want
to experiment with model-generated lens output.
