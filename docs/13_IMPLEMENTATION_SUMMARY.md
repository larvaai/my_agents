# Implementation Summary

Tài liệu này tổng hợp các hạng mục chính đã triển khai trong quá trình nâng project thành coding-agent local.

## 1. Bài Học Từ OpenHands

Các điểm đã học và đưa vào project:

- Tool protocol phải rõ, có schema cứng.
- File editor nên tách khỏi terminal.
- Terminal cần metadata rủi ro.
- Agent loop phải có ReAct rõ ràng.
- Coding-agent không được dừng ở “đã viết code”.
- Phải chạy test, đọc lỗi, sửa tiếp.
- Cần context condenser.
- Khi test fail, agent nên chạy probe nhỏ hoặc patch nhỏ.
- Cần finish gate.
- Cần phân vai rõ giữa code, test, review, final.

## 2. MCP Expansion

Đã triển khai và nối vào config/schema/prompt:

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
- File Editor MCP mở rộng với `file_editor_write_lines`.
- Terminal MCP với argv-only và risk metadata.

Các MCP đều đi qua:

```text
tools/mcp_config.py
tools/mcp_client.py
tools/tool_schemas.py
tools/tool_policy.py
```

## 3. Tool Protocol And Schema

Đã thêm schema cứng cho các nhóm tool quan trọng:

- filesystem
- git
- context7
- python
- terminal
- file_editor
- code_index
- lint_test
- docker
- obsidian
- issue
- rag
- fetch
- search
- document
- ledger
- playwright

Schema bao gồm:

- input args
- output shape
- error fields
- metadata

## 4. JsonGate

Đã triển khai `output_gate/`.

Files:

- `output_gate/json_gate.py`
- `output_gate/repair_rules.py`
- `output_gate/repair_loop.py`

JsonGate làm:

- Extract JSON.
- Repair deterministic lỗi nhỏ.
- Validate action schema.
- Resolve tool/alias.
- Validate tool args.
- Dry-run safety.
- Trả structured error cho agent sửa lại.

Smoke:

```powershell
python run_json_gate_smoke.py
```

## 5. Single-Agent Orchestrator

`orchestrator.py` đã được nối JsonGate.

Nó hiện có:

- JSON gate.
- Tool repetition guard.
- Context condenser.
- Finish gate sau code edit.
- Event log.
- Tool result condensation.

## 6. LangGraph Orchestrator

Đã thêm:

- `orchestration/agent_state.py`
- `orchestration/langgraph_orchestrator.py`
- `main_langgraph.py`
- `run_langgraph_smoke.py`

Pipeline:

```text
research -> planner -> architect -> code -> test -> review -> ledger -> final
```

Đã có:

- Tool node chung.
- Role budgets.
- Subtask budgets.
- Required file tracking.
- Missing file tracking.
- Forced test action cho test file.
- Finish gate.
- Failed-test repair routing.
- Whole-file rewrite guard trong repair mode.
- Failure summary extraction.

Smoke:

```powershell
python run_langgraph_smoke.py
python run_all_cases.py --group langgraph --timeout 180 --fail-fast
```

## 7. BaseAgent And Role Agents

Đã thêm:

- `agents/base_agent.py`
- `agents/role_agents.py`

Role agents:

- Research
- Planner
- Architect
- Code
- Test
- Review
- Ledger
- Final
- Tool Agent backward-compatible

Mỗi role có:

- `name`
- `role`
- `system_prompt`
- `allowed_tools`
- `allowed_skills`
- optional `department`
- optional `lenses`

Smoke:

```powershell
python run_agent_role_smoke.py
```

## 8. Department Agents And Lenses

Đã triển khai v0.1 cho 4 agent:

### Code Agent

Department: Engineering.

Lenses:

- implementation
- integration
- defensive_coding
- refactor_discipline
- developer_experience

### Test Agent

Department: QA / Test Council.

Lenses:

- logic
- critical_thinking
- experienced_qa
- regression
- purpose_alignment
- test_executor

### Review Agent

Department: Senior Review Board.

Lenses:

- senior_engineer
- scope_diff
- security_review
- maintainability
- release_risk

### Ledger Agent

Department: Secretary / Audit / Operations.

Lenses:

- historian
- task_state
- decision_record
- auditor
- incident_tracker

Rule:

```text
Lenses suggest.
Department agents decide.
Orchestrator routes.
Only executor tools perform actions.
```

## 9. Failed-Test Repair

Đã triển khai repair loop:

```text
Test fail
  -> extract last_failure
  -> increment repair_attempts
  -> route to Code
  -> Code patch small
  -> route to Test
```

Blocked behavior:

- Code Agent không được rewrite nguyên file đang fail.
- Whole-file write bị block bằng `repair_requires_patch_tool`.

## 10. Long File Write Protocol

Đã thêm:

```text
file_editor.file_editor_write_lines
```

Mục tiêu:

- Tránh agent nhồi file dài vào JSON multiline string.
- Viết file bằng JSON `lines` array.
- Giảm lỗi parse JSON khi generated file dài.

## 11. Context And Logs

Đã có:

- Event logs trong `agent_runs/`.
- Test logs trong `test_runs/`.
- `inspect_runs.py`.
- Tool result condenser.
- Compact state brief trong LangGraph.

Logs giúp đọc:

- Agent raw output.
- Tool calls.
- Tool results.
- JSON gate errors.
- Finish gate blocks.
- Budget blocks.
- Repair attempts.

## 12. Testing Infrastructure

Đã có:

- `run_json_gate_smoke.py`
- `run_agent_role_smoke.py`
- `run_langgraph_smoke.py`
- `run_mcp_chain_smoke.py`
- `run_all_cases.py`
- prompt cases trong `prompts/auto_cases/`
- skill cases trong `prompts/skill_cases/`
- `workspace/society_sim/test_society_sim.py`

Các command hay chạy:

```powershell
python run_json_gate_smoke.py
python run_agent_role_smoke.py
python run_langgraph_smoke.py
python run_all_cases.py --group langgraph --timeout 180 --fail-fast
python .\workspace\society_sim\test_society_sim.py
```

## 13. Docs

Đã có docs theo nhóm:

- Start here.
- Overview.
- Architecture.
- Setup.
- Agent protocol.
- MCP system.
- Skills.
- RAG.
- Testing.
- Debugging.
- Security.
- Contributing.
- Roadmap.
- ADRs.
- MCP docs.
- Agent docs.
- Workflows.
- Templates.

## 14. Current Status

Project hiện đã có nền coding-agent khá đầy đủ:

- Có tool layer.
- Có schema.
- Có role boundaries.
- Có LangGraph orchestration.
- Có JsonGate.
- Có repair loop.
- Có test runner.
- Có logs.
- Có docs.

Điểm còn đang v0.1:

- Department lenses chưa là sub-agent LLM riêng.
- Test Council chưa synthesize structured report bắt buộc.
- Planner/Research/Architect chưa có lens.
- Context condenser chưa dùng diff-aware memory sâu.
- UI run viewer chưa có.

## 15. North Star

Hướng đi tiếp theo:

```text
Reliable local coding-agent
  -> clear protocol
  -> safe tools
  -> role ownership
  -> real tests
  -> auditable logs
  -> bounded multi-agent reasoning
```

## Code/Test Department v0.5

Da trien khai truc tiep v0.5 cho Code Agent va Test Agent, bo qua cac stage cu
v0.1-v0.4 trong ban tham khao.

Files moi:

- `agents/code_agent.py`
- `agents/test_agent.py`
- `orchestration/code_test_orchestrator.py`
- `run_code_test_agents_demo.py`
- `run_code_test_agents_smoke.py`
- `docs/14_CODE_TEST_V05.md`

Code Agent v0.5:

- tao engineering lens results
- synthesize implementation decision
- tao executor plan
- chi execute qua allowlist file editor
- append ledger
- create issue neu execution fail
- route sang `test_agent`, `code_agent`, hoac `planner_agent`

Test Agent v0.5:

- tao QA lens results
- synthesize validation plan
- chi execute validation/read tools trong allowlist
- check expected stdout token neu co
- append ledger
- create issue neu quality gate fail
- route sang `review_agent`, `code_agent`, hoac `planner_agent`

Smoke:

```powershell
python run_code_test_agents_smoke.py
```

Expected:

```text
CODE_TEST_AGENTS_V05_SMOKE_OK
```
