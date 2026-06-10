# Contributing

## Nguyên Tắc

- Sửa nhỏ, đúng phạm vi task.
- Đọc file liên quan trước khi sửa.
- Không refactor rộng nếu user không yêu cầu.
- Không format/churn unrelated files.
- Không commit/push/reset/checkout trừ khi user yêu cầu rõ.
- MCP mới phải có schema, docs, test.
- Agent mới phải có role, allowed tools, forbidden tools, input/output.
- Thay đổi orchestrator phải có regression test.

## Quy Trình Đóng Góp

1. Đọc `docs/00_START_HERE.md`.
2. Xác định phạm vi thay đổi.
3. Nếu task lớn, tạo issue bằng Issue Tracker MCP.
4. Sửa file hẹp nhất.
5. Chạy validation hẹp nhất.
6. Chạy test group liên quan.
7. Cập nhật docs nếu behavior thay đổi.
8. Review diff bằng Git MCP hoặc `git diff`.

## Khi Thêm MCP

Theo workflow:

```text
docs/workflows/add-new-mcp.md
```

Checklist:

- Server nhỏ, một trách nhiệm.
- Sandbox rõ.
- Output có `ok`, `tool`, `error` khi fail.
- Schema trong `tools/tool_schemas.py`.
- Prompt example.
- Test case.
- Docs.

## Khi Thêm Skill

Theo workflow:

```text
docs/workflows/add-new-skill.md
```

Skill nên mô tả workflow, guardrails, output kỳ vọng. Skill không nên chứa code dài hoặc quyền mới.

## Khi Thêm Agent

Theo workflow:

```text
docs/workflows/create-new-agent.md
```

Agent mới chưa nên được nối vào orchestrator chính nếu chưa có:

- Role rõ.
- Tool permission rõ.
- Failure rules.
- Test prompts.
- Review gate.

## Definition Of Done

Một thay đổi được xem là xong khi:

- Code chạy được.
- Test liên quan pass.
- Không phá guardrails.
- Docs cập nhật nếu behavior thay đổi.
- Final report nói rõ đã test gì.

