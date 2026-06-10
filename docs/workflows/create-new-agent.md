# Workflow: Create New Agent

## Goal

Thêm agent role mới mà không làm loạn quyền tool và orchestration.

## Steps

1. Viết docs agent trước trong `docs/agents/<agent>.md`.
2. Xác định role.
3. Xác định allowed tools.
4. Xác định forbidden tools.
5. Xác định input/output schema.
6. Viết failure rules.
7. Tạo prompt/system wrapper riêng nếu cần.
8. Thêm tests trước khi nối vào orchestrator chính.
9. Chỉ nối vào multi-agent scheduler khi permission matrix đã rõ.

## Required Sections

- Role.
- Allowed tools.
- Forbidden tools.
- Input schema.
- Output schema.
- Workflow.
- Failure rules.
- Tests.

## Template

Xem:

```text
docs/templates/agent-template.md
```

