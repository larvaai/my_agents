# Architecture

## High-Level Map

Project có hai đường chạy chính:

```text
Single-agent path:
main.py
  -> orchestrator.py
  -> agents/tool_agent.py
  -> llm.py
  -> JsonGate
  -> tools/tool_registry.py
  -> tools/mcp_client.py
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

Single-agent path vẫn hữu ích cho prompt đơn giản và backward compatibility. LangGraph path là hướng coding-agent chính.

## Core Layers

### Entry Points

| File | Vai trò |
|---|---|
| `main.py` | Đọc prompt và chạy `run_orchestrator()` |
| `main_langgraph.py` | Đọc prompt và chạy LangGraph orchestrator |
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
- Validate tool args theo `tools/tool_schemas.py`.
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
- `agents/tool_agent.py`
- `agents/lenses/`

`BaseAgent`:

- Build system prompt.
- Gắn role, department, lenses.
- Gắn allowed tools và skills.
- Guard output ngoài allowlist.

`role_agents.py` khai báo:

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

`agents/lenses/` chứa role lenses cho 4 department đầu tiên:

```text
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
```

Lens hiện là prompt/spec layer. Chúng không tự chạy tool, không tự loop, không tự quyết định.

### MCP Layer

Files:

- `tools/mcp_config.py`
- `tools/mcp_client.py`
- `tools/tool_registry.py`
- `tools/tool_schemas.py`
- `tools/tool_policy.py`
- `mcp_servers/`

MCP client làm:

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
agent_runs/<run_id>/events.jsonl
agent_runs/<run_id>/summary.json
test_runs/<timestamp>/
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
  -> tools/tool_registry.py
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
