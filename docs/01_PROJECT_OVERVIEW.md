# Project Overview

## Mục Tiêu

Project này xây dựng một local coding-agent có thể làm việc giống một đội phần mềm nhỏ:

- Nhận yêu cầu bằng prompt.
- Phân vai thành các agent có trách nhiệm rõ.
- Gọi tool qua MCP schema.
- Sửa file có audit.
- Chạy test thật.
- Debug từ lỗi thật.
- Ghi ledger và issue để giữ memory.
- Báo cáo final có bằng chứng.

Đây không phải chatbot hỏi đáp chung. Đây là nền agent để đọc repo, sửa code, kiểm thử, review, ghi log và lặp lại đến khi pass hoặc báo blocker rõ.

## Những Gì Đã Triển Khai

### 1. Orchestrator JSON-only

`orchestrator.py` là loop single-agent:

```text
user prompt
  -> tool_agent
  -> JsonGate
  -> tool call
  -> tool result
  -> context update
  -> final hoặc tiếp tục
```

Nó có:

- JSON-only protocol.
- Tool call repetition guard.
- Condensed tool result.
- Finish gate sau code change.
- Event log.
- JsonGate trước khi gọi tool.

### 2. LangGraph Multi-Agent Pipeline

`orchestration/langgraph_orchestrator.py` là pipeline role-based:

```text
research
  -> planner
  -> architect
  -> code
  -> test
  -> review
  -> ledger
  -> final
```

Tool execution tập trung ở `tool` node. Role node không trực tiếp chạy tool, mà trả JSON action.

Đã có:

- `AgentState` shared state.
- Role budgets.
- Subtask budgets.
- Required/missing files tracking.
- Failed-test repair mode.
- Finish gate.
- JsonGate integration.
- Context condenser.

### 3. Department Agents Và Role Lenses

Bốn agent lõi đã được nâng thành mô hình phòng ban:

| Agent | Department | Trách nhiệm |
|---|---|---|
| Code Agent | Engineering Department | Implement code, repair lỗi hẹp, hand off QA |
| Test Agent | QA Department / Test Council | Thiết kế validation, chạy test, phân loại lỗi |
| Review Agent | Senior Review Board | Review scope, correctness, security, maintainability |
| Ledger Agent | Ledger / Audit / Operations | Ghi memory, task state, decision, incident |

Mỗi department có role lenses trong `agents/lenses/`.

Nguyên tắc:

```text
Lens đề xuất.
Agent lớn quyết định.
Orchestrator điều phối.
Tool executor mới thực thi.
```

### 4. JsonGate

`output_gate/` kiểm mọi output của agent trước khi orchestrator dùng.

Pipeline:

```text
raw output
  -> extract JSON
  -> deterministic repair
  -> action schema check
  -> tool resolve
  -> tool args schema check
  -> dry-run safety check
  -> pass hoặc structured retry error
```

JsonGate sửa được lỗi máy móc như:

- Markdown fence.
- Text thừa trước/sau JSON.
- Trailing comma.
- Python literal `True`/`False`/`None`.
- Unquoted key đơn giản.
- Alias an toàn như `tool_name` -> `tool`, `arguments` -> `args`.

JsonGate không execute tool thật.

### 5. MCP System

MCP servers nội bộ đang có:

- Filesystem
- File Editor
- Python Sandbox
- Terminal
- Git
- Context7
- RAG
- Fetch
- Search
- Document
- Ledger
- Playwright
- Code Index
- Lint/Test
- Docker
- Obsidian
- Issue Tracker

MCP client có:

- Tool alias resolution.
- Schema validation.
- Policy check.
- Stdio server execution.
- Result normalization.

### 6. Skills

Skills là hướng dẫn Markdown, không phải tool:

- `project-plan`
- `code-edit`
- `debug-traceback`
- `run-test`
- `git-review`

Skills giúp agent chọn workflow đúng, còn MCP cung cấp capability thật.

### 7. RAG

RAG dùng Qdrant và local ingest/search:

- `rag.rag_health`
- `rag.rag_ingest`
- `rag.rag_search`

RAG chỉ làm việc trong workspace sandbox và có health gate.

### 8. Test System

Test hiện có nhiều lớp:

- Compile/smoke deterministic.
- MCP chain smoke.
- JsonGate smoke.
- Role permission smoke.
- LangGraph smoke.
- Prompt-based cases trong `run_all_cases.py`.
- Skill cases trong `prompts/skill_cases/`.
- Generated e2e artifact như `workspace/society_sim/`.

Các lệnh quan trọng:

```powershell
python run_json_gate_smoke.py
python run_agent_role_smoke.py
python run_langgraph_smoke.py
python run_all_cases.py --group langgraph --timeout 180 --fail-fast
python .\workspace\society_sim\test_society_sim.py
```

## Tinh Thần Thiết Kế

Project ưu tiên:

- Rõ protocol hơn thông minh mơ hồ.
- Tool có schema hơn shell tự do.
- File edit có audit hơn terminal edit.
- Test thật hơn nói “đã xong”.
- Failure có route rõ hơn retry tùy hứng.
- Local-first, LM Studio friendly.
- Dễ đọc, dễ chỉnh, dễ thêm MCP/agent/skill.

## Những Gì Chưa Phải Là Final

Một số phần đã có nền nhưng còn có thể nâng cấp:

- Lens hiện là prompt/spec layer, chưa là sub-agent LLM riêng.
- Test Council chưa chạy parallel reasoning thật.
- Planner/Research/Architect chưa có lens riêng.
- Context condenser còn có thể thông minh hơn theo file diff.
- Full e2e prompt lớn như `the_sims_prompt.md` vẫn cần tối ưu thêm budget và routing.
