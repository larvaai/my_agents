# Domain And Business Logic

## Domain Cốt Lõi

Domain của repo là "agent runtime for controlled software work".

Các khái niệm chính:

| Entity | Ý nghĩa |
|---|---|
| User Task | Yêu cầu gốc từ user/prompt file |
| Agent | Vai trò LLM hoặc deterministic department |
| Action | JSON object agent trả về |
| Tool Request | Tool name + args sau khi parse |
| Capability | Một khả năng thực thi qua kernel |
| Feature | Module cung cấp capabilities |
| MCP Server | Backend tool thực tế |
| Tool Result | Kết quả raw/normalized từ tool |
| CapabilityResult | Envelope chuẩn của kernel |
| Event | Log của message/action/tool/state/error |
| Artifact | File dài chứa analysis/spec/docs |
| Route Decision | Quyết định next agent/department |
| Validation Evidence | Kết quả test/probe chứng minh |
| Ledger Entry | Memory/audit JSONL |
| Issue | Task/bug/risk trong SQLite |

## State Machine Cơ Bản

### Single-Agent

```text
START
  -> LLM_CALL
  -> JSON_GATE
  -> if final: FINISH_GATE
  -> if tool: TOOL_CALL
  -> TOOL_RESULT
  -> CONTEXT_UPDATE
  -> LLM_CALL
```

### Code Task Finish Gate

```text
NO_CODE_CHANGE
  -> code edit tool
  -> PENDING_VALIDATION
  -> validation fail
  -> PENDING_VALIDATION
  -> validation pass
  -> VALIDATED
  -> final success allowed
```

### Failed-Test Repair

```text
Test fails
  -> extract last_failure
  -> increment repair_attempts[signature]
  -> route Code
  -> Code patch small span
  -> route Test
  -> pass or repeat until budget/blocker
```

## Business Rules

### JSON And Tool Rules

- Agent output must be one JSON object.
- Tool action must include server-qualified tool name where possible.
- Tool args must be object.
- Unknown tool is not recoverable by execution; agent must correct name.
- Missing args must be corrected, not retried unchanged.

### File Rules

- Existing file should be read/viewed before edit.
- File mutation should use File Editor MCP.
- Generated long file should use `file_editor_write_lines`.
- Repair mode should patch, not rewrite whole failing file.

### Validation Rules

- Code change requires validation.
- Validation can be Python, lint_test, or narrow terminal validation.
- If validation cannot run due dependency/environment, final must say blocker.
- Test Agent owns validation in role split.

### Role Rules

| Role | Can | Cannot |
|---|---|---|
| Research | gather/read evidence | edit source |
| Planner | plan/update issues/ledger | implement |
| Architect | write design docs | implement |
| Code | edit/create files | approve final |
| Test | run validation | edit source |
| Review | inspect diff/risk | mutate git/edit |
| Ledger | record audit/issues | run terminal/edit code |
| Final | synthesize user answer | mutate project |

### Software Factory Rules

- No Protocol Strategy -> no product analysis.
- No Vision -> no BRD.
- No BRD -> no PRD.
- No Story + AC -> no technical design.
- No Business Logic Model -> no technical analysis.
- No Domain Analysis + Change Hotspots -> no pattern decision.
- No Pattern Decision evidence -> no code handoff.
- No Docs Verification -> not done.

## Business Logic For Product-Build Prompts

Software Factory converts ambiguous prompt into executable intent:

```text
User idea
  -> Vision
  -> Business requirements
  -> Product requirements
  -> Stories
  -> Acceptance criteria
  -> Domain objects/workflows/hotspots
  -> Business invariants/decision table/state transitions
  -> Technical boundaries
  -> Pattern decisions with evidence
  -> Implementation spec
  -> Code handoff packet
```

Điều quan trọng: pattern không được chọn ở PRD. Pattern chỉ được chọn sau khi
có hotspot evidence.

## Invariants Của Hệ Thống Agent

- Tool side effect phải trace được từ event log.
- Capability result phải giữ shape ổn định.
- Core không phụ thuộc backend implementation cụ thể.
- Role không được bypass allowlist.
- Final success cho code phải có validation evidence.
- Long analysis phải nằm trong artifact, không nhồi vào JSON tool payload.
- Dependency failure không được gọi là code logic failure.

