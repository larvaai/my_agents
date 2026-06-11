# NFR, Security And Risk

## Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Local-first | Chạy được local bằng Python/LM Studio |
| NFR-02 | Auditability | Mọi run có event log và summary |
| NFR-03 | Safety by layers | Role allowlist, JsonGate, schema, policy, sandbox |
| NFR-04 | Deterministic tests | Smoke không phụ thuộc LLM khi có thể |
| NFR-05 | Extensibility | Feature/module/tool mới thêm bằng registry/config |
| NFR-06 | Graceful failure | Dependency thiếu trả structured error |
| NFR-07 | Small core | `core/` không biết chi tiết MCP/RAG/browser/Docker |
| NFR-08 | Validation-first | Code task phải có validation evidence |
| NFR-09 | Maintainability | Tầng nào có contract/test riêng |
| NFR-10 | Observability | Metrics: step, tool_calls, parse_errors, validations |

## Security Model

Không tin prompt. Không tin LLM output. Không tin external content.

Boundary theo lớp:

```text
role allowlist
  -> JsonGate dry-run
  -> tool arg schema
  -> hard policy
  -> MCP server sandbox
  -> process timeout
  -> event log
```

## Workspace Security

Workspace mặc định:

```text
var/workspace/
```

Các rule:

- Relative path phải resolve vào workspace.
- Không cho `..`.
- Không cho Windows drive path trong JSON tool args.
- Không cho absolute path ngoài workspace.
- Ledger/Issue/Obsidian/RAG/Document cũng phải tự enforce.

## Tool Risk Categories

| Risk | Tool nhóm | Policy |
|---|---|---|
| Low read-only | code_index, git status/diff/log, document outline | Cho phép theo role |
| Medium write | file_editor, document write, ledger, issue | Sandbox + role scoped |
| Medium execution | python, lint_test, terminal safe argv | Timeout + metadata |
| High repo mutation | git add/commit/reset/checkout | Block mặc định |
| High infra mutation | docker compose up/stop | Env opt-in |
| Network | search/fetch/playwright/context7 | Chỉ khi route cần |

## Hard Policy Hiện Tại

- Git mutation bị block nếu không set `AGENT_ALLOW_GIT_MUTATIONS=1`.
- Docker compose up/stop bị block nếu không set `DOCKER_MCP_ALLOW_MUTATION=1`.
- Terminal high-risk bị block nếu không set `AGENT_ALLOW_HIGH_RISK_TERMINAL=1`.
- Terminal không nhận shell string, chỉ nhận `argv`.
- Destructive shell commands không được expose qua MCP.

## Prompt Injection Risk

Global Supervisor có PromptInjectionAgent kiểm các pattern như:

- ignore previous instructions
- reveal secrets
- exfiltrate
- override policy
- disable safety

Rule:

- External/web/PDF content không được tự thay đổi quyền tool.
- Prompt injection hit phải route blocker hoặc limits.

## Secrets Policy

Không lưu secrets vào:

- RAG
- Ledger
- Issues
- Obsidian
- Documents
- Event logs
- Test logs

Không ingest `.env`, token, API key, password.

## Operational Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM lặp tool call | Loop tốn thời gian | repeated call guard |
| Tool fail lặp lại | Không tiến triển | fail twice -> final/tool failure |
| JSON quá dài | Parse fail | file_editor_write_lines + artifact protocol |
| Test fail không rõ | Sửa bừa | last_failure + repair mode |
| Whole-file rewrite khi repair | Mất code đúng | block `repair_requires_patch_tool` |
| RAG dependency down | Search fail | rag_health gate |
| Ruff missing | False fail | dependency_failure field |
| MCP startup chậm | Latency | future MCP pool |

## Security Acceptance Criteria

- Unsafe path bị JsonGate chặn trước tool.
- MCP server vẫn tự chặn path nếu JsonGate bị bypass.
- Git mutation blocked smoke pass.
- Terminal shell executable blocked.
- Role tool allowlist smoke pass.
- Docker destructive operation không có tool expose.
- Code task không final success nếu thiếu validation.

