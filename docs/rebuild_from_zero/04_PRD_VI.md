# Product Requirements Document

## 1. Product Vision

Xây một framework local cho coding-agent có thể chuyển từ yêu cầu tự nhiên sang
hành động có kiểm soát: đọc/sửa file, chạy validation, dùng tools, sinh spec,
ghi audit và báo cáo final dựa trên evidence.

## 2. Personas

| Persona | Mục tiêu |
|---|---|
| Builder | Muốn hiểu và rebuild từng tầng |
| Agent operator | Muốn chạy prompt và nhận kết quả có evidence |
| Developer | Muốn thêm MCP/agent/skill/test dễ dàng |
| Reviewer | Muốn biết thay đổi gì, test gì, rủi ro gì |
| Product planner | Muốn BRD/PRD/story/AC trước khi code |

## 3. Functional Requirements

### FR-01 CLI Prompt Runner

User có thể chạy:

```powershell
python main.py prompts/user_prompt.md
```

Acceptance:

- Đọc prompt file hoặc prompt mặc định.
- In final result.
- Không crash khi prompt path hợp lệ.

### FR-02 LLM Adapter

System gọi được OpenAI-compatible chat completions API.

Acceptance:

- Có default LM Studio config.
- Env override được model/base URL/token/timeout.
- Lỗi LLM được wrap thành message rõ.

### FR-03 JSON Action Protocol

Agent chỉ trả một JSON object:

- `action=tool`
- `action=final`

Acceptance:

- Không cần markdown.
- Parse bằng `json.loads` sau JsonGate.
- Có retry khi invalid.

### FR-04 JsonGate

System validate output trước khi gọi tool.

Acceptance:

- Repair được fenced JSON/trailing comma/Python literal/unquoted simple key.
- Chặn unknown tool.
- Chặn missing/wrong args.
- Chặn unsafe path.
- Chặn terminal không phải argv.
- Chặn git mutation theo policy.

### FR-05 Agent Kernel

Tool execution đi qua kernel.

Acceptance:

- `call_tool()` trả CapabilityResult envelope.
- Feature disable không làm kernel crash.
- Unknown tool trả structured error.

### FR-06 MCP Tool Integration

Agent gọi tools qua MCP adapter.

Acceptance:

- Resolve alias và server-qualified name.
- Validate schema.
- Normalize result.
- Có metadata risk/category.

### FR-07 Workspace Sandbox

File tools chỉ thao tác trong workspace.

Acceptance:

- Relative path resolve vào workspace.
- `..`, absolute drive path, path ngoài workspace bị chặn.
- Python/RAG/document/ledger/issue tự enforce sandbox.

### FR-08 File Editing

Agent edit file qua File Editor MCP.

Acceptance:

- View line-numbered file.
- Create/write_lines file.
- str_replace có expected replacement count.
- insert theo line.
- Không cần terminal để edit.

### FR-09 Validation

System hỗ trợ validation có cấu trúc.

Acceptance:

- Chạy Python workspace file.
- Compile Python project path.
- Run selected Python file.
- Ruff check optional, báo dependency failure nếu thiếu.
- Smoke suite chạy được.

### FR-10 Finish Gate

Coding task không final success nếu chưa validate.

Acceptance:

- Sau code change, pending validation bật.
- Validation pass tắt pending.
- Final bị block nếu còn pending, trừ blocker rõ.

### FR-11 Event Logging

Mỗi run có audit log.

Acceptance:

- Ghi MessageEvent, ActionEvent, ObservationEvent, StateEvent/ErrorEvent.
- Có summary JSON.
- Có CLI inspect/search.

### FR-12 Role-Based Agents

System có role agents với tool allowlist.

Acceptance:

- Research/Planner/Architect/Code/Test/Review/Ledger/Final.
- Role không gọi tool ngoài quyền.
- Role prompt ghi rõ trách nhiệm.

### FR-13 LangGraph Orchestration

System chạy được pipeline role-based.

Acceptance:

- State có required/missing files, tests_run, last_failure, repair_attempts.
- Tool node tập trung thực thi.
- Failed test route về Code.
- Budget/repeated tool guard hoạt động.

### FR-14 Company Agents v0.5

System có deterministic department contract runner.

Acceptance:

- Department result có `agent`, `version`, `lens_results`, `synthesis`, `records`, `route`.
- Code/Test cycle route rõ.
- Review/Ledger/Final gate rõ.
- Smoke pass.

### FR-15 Software Factory v0.7

System sinh artifact spec trước khi code.

Acceptance:

- Sinh Protocol Strategy, Vision, BRD, PRD, Epics/Stories, AC.
- Sinh Product Validation/Critique.
- Sinh Domain Analysis, Business Logic Model/Validation.
- Sinh Technical Analysis, Pattern Decision.
- Sinh Implementation Spec, Code Handoff Packet.
- Sinh Docs Plan, Repo Scan, API Inventory, ADR Candidates, Docs Package, Docs Verification, Final.

### FR-16 Global Supervisor

System route request tổng quát.

Acceptance:

- Classify knowledge/research/code/product-build/mixed/agent-creation.
- Safety Department chạy khi cần repo/code/web.
- Final Synthesis là owner final answer.
- Product-build route sang Software Factory.

## 4. Non-Functional Product Requirements

Tóm tắt; chi tiết ở `05_NFR_SECURITY_RISK_VI.md`.

- Local-first.
- Deterministic smoke tests.
- Strict schema boundaries.
- No broad shell access.
- Auditability.
- Extensibility bằng feature/port/adapter.
- Graceful dependency failure.

## 5. Key User Journeys

### Journey A: Chạy một code task nhỏ

```text
User prompt
  -> main.py
  -> Tool Agent
  -> file read/edit
  -> validation
  -> final with evidence
```

### Journey B: Multi-agent code task

```text
User prompt
  -> LangGraph
  -> Research/Planner/Architect
  -> Code edit
  -> Test validation
  -> Review
  -> Ledger
  -> Final
```

### Journey C: Product build lớn

```text
User product prompt
  -> Global Supervisor
  -> Software Factory
  -> implementation spec + handoff packet
  -> Company/LangGraph real coding path
```

### Journey D: Research/current-info

```text
User asks current/source-backed question
  -> Intent Router
  -> Safety
  -> Research Department
  -> Search/Fetch/PDF/Citation
  -> Final Synthesis
```

## 6. Product Backlog Summary

| Priority | Item |
|---|---|
| P0 | Rebuild minimal CLI + JSON loop |
| P0 | Kernel + capability envelope |
| P0 | File/Python tools + workspace sandbox |
| P0 | JsonGate + schemas |
| P0 | Validation + finish gate |
| P1 | MCP adapter/server set |
| P1 | Event log and inspect CLI |
| P1 | Role agents + allowlists |
| P1 | LangGraph repair path |
| P2 | Software Factory artifacts |
| P2 | Global Supervisor |
| P3 | UI run viewer |
| P3 | Persistent MCP server pool |
| P3 | RAG reranker/line ranges |

