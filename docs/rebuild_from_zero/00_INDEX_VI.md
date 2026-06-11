# Rebuild From Zero - Documentation Index

## Mục Đích

Bộ tài liệu này là bản đọc hiểu và rebuild `my_agents` từ số 0.
Nó không thay thế ngay các docs cũ trong repo; nó gom lại một cách có hệ thống
những gì repo hiện đang thể hiện qua code, docs, runners, tests và MCP servers.

Mục tiêu là giúp bạn:

- Hiểu ý nghĩa thật của repo hiện tại.
- Biết vì sao từng thành phần tồn tại.
- Có BRD, PRD, architecture, epic, story, acceptance criteria và các tài liệu còn thiếu.
- Có lộ trình triển khai theo tầng để viết lại repo mới từng bước, kiểm soát được.

## Thứ Tự Đọc

1. `01_REPO_UNDERSTANDING_VI.md` - repo này là gì, giải quyết vấn đề gì.
2. `02_ARCHITECTURE_VI.md` - kiến trúc hiện tại theo tầng và luồng chạy.
3. `03_BRD_VI.md` - Business Requirements Document.
4. `04_PRD_VI.md` - Product Requirements Document.
5. `05_NFR_SECURITY_RISK_VI.md` - yêu cầu phi chức năng, security, risk.
6. `06_EPICS_STORIES_AC_VI.md` - epic, user story, acceptance criteria.
7. `07_DOMAIN_BUSINESS_LOGIC_VI.md` - domain model và business logic của agent system.
8. `08_IMPLEMENTATION_LAYERS_VI.md` - các tầng cần triển khai để đạt trạng thái repo hiện tại.
9. `09_REBUILD_ROADMAP_VI.md` - kế hoạch rebuild repo mới theo milestone.
10. `10_TRACEABILITY_MATRIX_VI.md` - map BRD -> PRD -> Epic -> Story -> Code -> Test.
11. `11_ADR_BACKLOG_VI.md` - decision log/backlog kiến trúc cần giữ.
12. `12_TEST_STRATEGY_VI.md` - chiến lược test và quality gate.
13. `13_REBUILD_PLAYBOOK_VI.md` - playbook thao tác trực tiếp khi bắt đầu repo mới.

## Tóm Tắt Một Câu

`my_agents` là một local coding-agent framework chạy bằng CLI, dùng LLM
OpenAI-compatible, ép output JSON, route tool qua Agent Kernel và MCP servers,
có sandbox, RAG, JsonGate, role-based agents, Software Factory artifacts,
event logs và test harness để biến prompt thành thay đổi code có kiểm chứng.

## Cách Dùng Bộ Docs Này Khi Rebuild

Không nên bắt đầu bằng multi-agent hoặc Software Factory. Repo mới nên đi theo
tầng:

```text
CLI + LLM adapter
  -> JSON protocol
  -> event log
  -> kernel + capability result envelope
  -> file/python tools tối thiểu
  -> JsonGate
  -> tool schema + policy
  -> MCP adapter
  -> testing harness
  -> role agents
  -> LangGraph/company pipeline
  -> Software Factory artifacts
  -> global supervisor
```

Mỗi tầng phải có smoke test riêng trước khi xây tầng kế tiếp.
