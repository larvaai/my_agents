# Business Requirements Document

## 1. Executive Summary

`my_agents` cần trở thành một local coding-agent framework có khả năng nhận yêu
cầu tự nhiên, dùng LLM để lập bước, gọi tool an toàn, sửa code có audit, chạy
validation thật, review kết quả, ghi log/memory và báo cáo final có evidence.

Điểm khác biệt kinh doanh/kỹ thuật của sản phẩm là: không tối ưu cho "chat cho
vui", mà tối ưu cho quy trình làm phần mềm có kiểm soát.

## 2. Business Problem

Người dùng muốn tự xây agent, hiểu từng tầng, và kiểm soát được thay vì dùng
một black-box coding assistant.

Các vấn đề cần giải:

- Từ prompt đến code thường thiếu contract rõ.
- LLM dễ sinh output không parse được.
- Tool call dễ sai hoặc nguy hiểm.
- Code change dễ không được test.
- Prompt business/product dài làm coding-agent nhảy thẳng vào code sai.
- Không có audit trail để học/debug.
- Multi-agent nếu không có route contract sẽ khó kiểm soát.

## 3. Business Goals

| ID | Goal |
|---|---|
| BG-01 | Xây local coding-agent chạy được trên máy cá nhân |
| BG-02 | Mọi tool action phải có schema, policy và log |
| BG-03 | Mọi code change phải có validation evidence hoặc blocker rõ |
| BG-04 | Cho phép phân vai agent để Code/Test/Review/Ledger không lẫn trách nhiệm |
| BG-05 | Cho phép prompt product/business dài đi qua BRD/PRD/domain/business logic trước khi code |
| BG-06 | Cho phép rebuild từ zero theo tầng, mỗi tầng test được |
| BG-07 | Giữ local-first, dễ đọc, dễ sửa, không phụ thuộc UI lớn |

## 4. Stakeholders

| Stakeholder | Nhu cầu |
|---|---|
| Chủ repo / builder | Hiểu hệ thống, kiểm soát từng tầng, rebuild được |
| Developer future | Biết module nào làm gì, thêm tool/agent/test không phá runtime |
| Agent operator | Chạy prompt, xem log, biết vì sao agent fail/pass |
| QA/reviewer | Có evidence, test result, diff/risk rõ |
| Product/spec owner | Có BRD/PRD/story/AC/domain logic trước khi code |

## 5. Business Scope

### In Scope

- Local CLI coding-agent runtime.
- OpenAI-compatible LLM adapter.
- JSON-only agent action protocol.
- Tool execution qua kernel/capability registry.
- MCP client/server integration.
- Workspace sandbox.
- File edit, Python run, lint/test, terminal safe runner.
- RAG local bằng Qdrant.
- Search/fetch/document/ledger/issue/browser helper.
- Role-based agent orchestration.
- Software Factory artifact pipeline.
- Event logs và test harness.
- Docs hướng dẫn rebuild.

### Out Of Scope Hiện Tại

- Cloud-hosted SaaS.
- Multi-user auth/tenant.
- Full web UI production.
- Agent tự commit/push mặc định.
- Full arbitrary shell.
- Autonomous unbounded agents.
- Production secrets management.

## 6. Business Capabilities

| Capability | Mô tả | Trạng thái repo |
|---|---|---|
| Prompt execution | Chạy prompt file qua CLI | Đã có |
| JSON discipline | Ép action/final JSON | Đã có |
| Tool sandbox | Tool không vượt workspace/policy | Đã có nhiều lớp |
| Code edit | Sửa/tạo file qua File Editor MCP | Đã có |
| Validation | Python/lint/test/smoke validation | Đã có |
| Event audit | events.jsonl + summary | Đã có |
| Role ownership | Code/Test/Review/Ledger/Final | Đã có |
| Product spec room | Vision/BRD/PRD/story/AC/domain/spec | Đã có v0.7 |
| General routing | Knowledge/research/code/factory routing | Đã có deterministic |
| UI viewer | Xem run bằng UI | Chưa có |
| Persistent MCP sessions | Pool server lâu dài | Chưa có |

## 7. Success Metrics

| Metric | Target rebuild |
|---|---|
| JSON parse pass rate | Agent output qua JsonGate ổn định trên smoke |
| Tool schema failures | Có retry message rõ, không crash |
| Code change validation | 100% code task có validation hoặc blocker |
| Sandbox escape | Bị chặn ở JsonGate và MCP server |
| Regression smoke | `run_dev_checks.py --quick` pass |
| Product spec completeness | Software Factory sinh đủ required artifacts |
| Auditability | Mỗi run có event log và summary |

## 8. Business Rules

- Không có validation evidence thì không được claim "done" cho code task.
- Code Agent không tự approve.
- Test Agent không edit source.
- Review Agent không mutate git.
- Ledger không lưu secrets.
- Prompt business/product dài không được nhảy thẳng vào code nếu thiếu spec.
- Pattern decision phải có change hotspot evidence.
- Tool call phải qua schema/policy, không dựa vào prompt rule.

## 9. Assumptions

- User chạy local trên Windows/PowerShell.
- Python 3.11+ có sẵn.
- LM Studio hoặc OpenAI-compatible endpoint có thể chạy local.
- Docker chỉ cần cho Qdrant/RAG.
- Network tools là optional và phải dùng khi cần thông tin hiện tại.

## 10. Business Risks

| Risk | Impact | Mitigation |
|---|---|---|
| LLM output không parse được | Runtime fail | JsonGate + retry + compact payload |
| Tool call nguy hiểm | File/repo damage | Role allowlist + policy + sandbox |
| Agent claim pass giả | Sai niềm tin | Finish gate + validation evidence |
| Prompt quá dài | JSON/tool payload vỡ | Artifact protocol |
| Multi-agent khó debug | Không kiểm soát | Route contract + event logs |
| Docs lệch code | Người đọc hiểu sai | Traceability + docs verification |

## 11. Business Milestones Khi Rebuild

1. Có single-agent loop chạy prompt và final JSON.
2. Có tool call tối thiểu file/python với log.
3. Có JsonGate và schema.
4. Có Agent Kernel/capability envelope.
5. Có MCP adapter và local MCP servers.
6. Có validation/finish gate.
7. Có role split Code/Test/Review/Ledger.
8. Có Software Factory artifacts.
9. Có Global Supervisor route.

