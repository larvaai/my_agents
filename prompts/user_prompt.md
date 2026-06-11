Hãy bổ sung thêm vào docs trong thư mục ./docs/rebuild_from_zero những điểm còn thiếu dưới đây:

**Kết luận: đủ để bắt đầu rebuild repo từ số 0. Nhưng chưa đủ để giao cho người khác tự implement trơn tru mà không hỏi lại.**

Tôi chấm bộ docs hiện tại: **8/10**.

Nó đã đủ phần xương sống:

| Mảng docs               |       Trạng thái | Nhận xét                                                                                                                                       |
| ----------------------- | ---------------: | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Index / thứ tự đọc      |               Đủ | Có luồng đọc rõ từ repo understanding → architecture → BRD/PRD → roadmap/playbook.                                                             |
| BRD                     |          Đủ mạnh | Nêu đúng business problem: JSON lỗi, tool nguy hiểm, code không test, thiếu audit, multi-agent thiếu contract.                                 |
| PRD                     |          Đủ mạnh | Có FR-01 đến FR-16, bao phủ CLI, LLM, JSON, JsonGate, Kernel, MCP, sandbox, validation, role, LangGraph, Software Factory, Global Supervisor.  |
| Architecture            | Đủ để định hướng | Có luồng tổng thể User → CLI → Orchestrator → LLM → JsonGate → Kernel → MCP → Event log.                                                       |
| NFR / Security / Risk   |          Khá tốt | Có security model nhiều lớp: role allowlist → JsonGate → schema → policy → MCP sandbox → timeout → event log.                                  |
| Epics / Stories / AC    |  Đủ để chia task | Có epic cho runtime, JSON safety, kernel, safe tools, finish gate, role, factory, supervisor, observability.                                   |
| Domain / Business Logic |               Đủ | Có entity, state machine, rule JSON/tool/file/validation/role/factory.                                                                         |
| Implementation Layers   |          Rất tốt | Có Layer 0 → Layer 17, mỗi layer có mục tiêu, files, quality gate.                                                                             |
| Roadmap                 |              Tốt | Có milestone M0 → M14, nguyên tắc không nhảy vào multi-agent/factory quá sớm.                                                                  |
| Traceability            |              Tốt | Map BG → PRD → Epic/Story → Code Modules → Tests/Smoke.                                                                                        |
| ADR                     |              Khá | Có quyết định kiến trúc chính: JSON-only, CapabilityResult, MCP removable, Finish Gate, Role Ownership, Artifact-first.                        |
| Test Strategy           |              Tốt | Có test pyramid, gate từng tầng, lệnh quick/full, assert cho JsonGate/tools/orchestrator/role/factory.                                         |
| Playbook                |      Rất hữu ích | Có checklist thao tác từng tầng, lệnh check, pass condition, và “không làm gì” ở từng tầng.                                                    |

## Phần còn thiếu quan trọng

### 1. Thiếu `00_VISION_VI.md` riêng

Hiện Vision nằm rải trong Index/BRD/PRD, nhưng khi bắt đầu repo mới nên có một file cực ngắn trả lời:

```text
Repo này sinh ra để làm gì?
Không làm gì?
Triết lý vận hành là gì?
Ưu tiên số 1 là gì?
```

Ví dụ nên có:

```text
Ưu tiên 1: local-first.
Ưu tiên 2: tool safety.
Ưu tiên 3: validation evidence.
Ưu tiên 4: readability.
Không ưu tiên: UI, SaaS, autonomous unbounded agent, shell tự do.
```

### 2. Thiếu `14_ENV_SETUP_VI.md`

Bộ docs nói Python 3.11+, LM Studio/OpenAI-compatible, Docker optional cho Qdrant/RAG, nhưng chưa có một file setup chuẩn cho máy mới. BRD đã ghi assumptions này, nhưng chưa biến thành hướng dẫn cài đặt. 

Cần thêm:

```text
Python version
venv
requirements.txt
.env.example
LM Studio config
OpenAI-compatible endpoint
Windows PowerShell notes
Mac/Linux notes
Docker optional
Qdrant optional
Ruff optional
Playwright optional
```

### 3. Thiếu `15_REPO_STRUCTURE_TARGET_VI.md`

Implementation Layers có liệt kê files theo tầng, nhưng chưa có cây thư mục đích cuối cùng. Cần một file kiểu:

```text
my_agents/
  main.py
  llm.py
  orchestrator.py
  core/
  features/
  mcp_servers/
  output_gate/
  agents/
  orchestration/
  skills/
  prompts/
  tests/
  docs/
  var/
```

Mỗi folder cần có:

```text
folder làm gì
folder không được chứa gì
module nào được import module nào
```

Đây là rất quan trọng để rebuild không loạn.

### 4. Thiếu `16_CONTRACTS_VI.md`

Architecture có core data contracts cho Agent Action, Capability Result, Department Result, Software Factory Stage Result, nhưng mới ở mức ví dụ. 

Cần tách thành file contract riêng, ghi **schema chuẩn tuyệt đối**:

```text
AgentAction schema
FinalAction schema
ToolAction schema
CapabilityResult schema
Event schema
ToolError schema
ValidationEvidence schema
RouteDecision schema
ArtifactRef schema
DepartmentResult schema
FactoryStageResult schema
```

Mỗi schema nên có:

```text
required fields
optional fields
example pass
example fail
ai retry message
```

### 5. Thiếu `17_TOOL_CATALOG_VI.md`

NFR có phân nhóm risk theo tool, Implementation Layers có thứ tự implement MCP server, nhưng chưa có catalog đầy đủ từng tool.  

Cần bảng:

| Tool | Args | Result | Risk | Role allowed | Sandbox rule | Smoke |
| ---- | ---- | ------ | ---- | ------------ | ------------ | ----- |

Ví dụ:

```text
file_editor.view
file_editor.write_lines
file_editor.str_replace
python.run_python
lint_test.compile_project
terminal.run_argv
git.diff
code_index.find_symbol
ledger.write_entry
issue.create
rag.search
search.query
fetch.url
playwright.page_text
```

### 6. Thiếu `18_ROLE_PERMISSION_MATRIX_VI.md`

PRD có role agents và NFR có role allowlist, nhưng chưa có ma trận quyền chi tiết.  

Cần bảng:

| Role | Read repo | Edit file | Run test | Git read | Git mutate | Ledger | Web | Final |
| ---- | --------: | --------: | -------: | -------: | ---------: | -----: | --: | ----: |

Và rule rõ:

```text
Code Agent: edit được, không final approve.
Test Agent: run validation, không edit.
Review Agent: đọc diff/risk, không mutate.
Ledger Agent: ghi audit, không chạy terminal.
Final Agent: chỉ tổng hợp, không tool mutation.
```

### 7. Thiếu `19_LOGGING_SPEC_VI.md`

Bạn từng nói log fail đọc chưa dễ hiểu. Bộ docs có Event Logging và Test Strategy, nhưng chưa có thiết kế UX log mới.

Cần một file riêng:

```text
Event types
Run summary format
Human-readable failure summary
Timeline view
Tool call compact view
Validation evidence block
Repeated failure block
Final evidence block
```

Ví dụ log nên có 2 tầng:

```text
machine/events.jsonl
human/summary.md
```

### 8. Thiếu `20_ERROR_TAXONOMY_VI.md`

Hiện có nói graceful failure, dependency_failure, invalid JSON, unsafe path, nhưng chưa gom thành taxonomy chuẩn. 

Cần phân loại lỗi:

```text
PARSE_ERROR
SCHEMA_ERROR
POLICY_BLOCK
SANDBOX_ESCAPE_BLOCKED
TOOL_NOT_FOUND
DEPENDENCY_FAILURE
VALIDATION_FAILURE
LLM_FAILURE
TIMEOUT
REPEATED_TOOL_LOOP
PROMPT_INJECTION_BLOCKED
FINAL_GATE_BLOCKED
```

Mỗi lỗi cần:

```text
ai được retry không
user cần làm gì
có được final blocker không
có ghi ledger không
```

### 9. Thiếu `21_PROMPT_AND_SKILL_SPEC_VI.md`

Implementation Layers có Layer 11 Skills, nhưng chưa có spec chi tiết cho prompt/skill. 

Cần định nghĩa:

```text
system prompt format
tool prompt format
role prompt format
skill loading order
skill không phải tool
skill conflict resolution
max prompt size
context condenser rule
```

### 10. Thiếu `22_RELEASE_AND_GIT_WORKFLOW_VI.md`

Nếu repo rebuild từ zero, cần biết:

```text
branch main/dev
commit convention
tag version v0.1.0
khi nào release
khi nào chạy quick/full checks
không commit var/
không commit .env
```

## Kết luận thực dụng

**Bộ hiện tại đủ để bạn bắt đầu code Layer 0 → Layer 8 ngay.** Đặc biệt phần Implementation Layers, Roadmap, Playbook, Test Strategy và Traceability đang rất tốt để chống “nhảy cóc”.     

**Nhưng trước khi build tới Role Agents / LangGraph / Software Factory, nên bổ sung ít nhất 5 file sau:**

```text
14_ENV_SETUP_VI.md
15_REPO_STRUCTURE_TARGET_VI.md
16_CONTRACTS_VI.md
17_TOOL_CATALOG_VI.md
18_ROLE_PERMISSION_MATRIX_VI.md
```

Nếu muốn hệ thống thật dễ debug, thêm tiếp:

```text
19_LOGGING_SPEC_VI.md
20_ERROR_TAXONOMY_VI.md
21_PROMPT_AND_SKILL_SPEC_VI.md
22_RELEASE_AND_GIT_WORKFLOW_VI.md
```

## Thứ tự làm tiếp

Không cần viết thêm quá nhiều lý thuyết. Nên làm như sau:

```text
Bước 1: Thêm 14_ENV_SETUP_VI.md
Bước 2: Thêm 15_REPO_STRUCTURE_TARGET_VI.md
Bước 3: Thêm 16_CONTRACTS_VI.md
Bước 4: Thêm 17_TOOL_CATALOG_VI.md
Bước 5: Thêm 18_ROLE_PERMISSION_MATRIX_VI.md
Bước 6: Bắt đầu code Layer 0
```

Đánh giá cuối: **docs hiện tại đủ làm “bản đồ rebuild”, chưa đủ làm “bộ spec đóng băng để implement không hỏi lại”.**
