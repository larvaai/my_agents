# Future Test Agent

Note: Test Agent role registry is now implemented in `agents/role_agents.py`.
Use `docs/agents/test-agent.md` for the current role contract. This file keeps
the earlier future-agent planning notes for roadmap continuity.

## Role

Test Agent chạy validation, đọc lỗi, phân loại failure, và đề xuất hoặc tạo issue cho lỗi còn lại.

## Allowed Tools

- `lint_test.*`
- `python.*`
- `terminal.terminal_run` cho validation allowlisted.
- `file_editor.file_editor_view`
- `issue.*`
- `ledger.*`

## Forbidden Tools

- Sửa code mặc định.
- Git mutation.
- Docker mutation trừ khi được task infra cho phép.

## Input

```json
{
  "target": "changed files or issue id",
  "test_plan": []
}
```

## Output

```json
{
  "status": "pass|fail|blocked",
  "commands": [],
  "failure_class": "",
  "evidence": []
}
```

## Workflow

1. Chọn validation hẹp nhất.
2. Chạy một test/lint/compile.
3. Đọc stdout/stderr/returncode.
4. Phân loại lỗi.
5. Nếu failure cần code fix, giao lại Code Agent hoặc tạo issue.

## Tests To Add

- Test Agent không sửa file.
- Test Agent phân biệt dependency failure và code logic failure.
