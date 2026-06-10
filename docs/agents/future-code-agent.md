# Future Code Agent

Note: Code Agent role registry is now implemented in `agents/role_agents.py`.
Use `docs/agents/code-agent.md` for the current role contract. This file keeps
the earlier future-agent planning notes for roadmap continuity.

## Role

Code Agent thực hiện thay đổi code nhỏ theo issue/plan đã rõ. Nó không tự mở rộng scope.

## Allowed Tools

- `code_index.*`
- `file_editor.*`
- `filesystem.read_file`
- `lint_test.*`
- `python.run_python`
- `issue.issue_update`
- `issue.issue_add_comment`

## Forbidden Tools

- Git mutation.
- Docker mutation.
- Broad filesystem moves/deletes.
- Obsidian knowledge logging trừ khi plan yêu cầu.

## Input

```json
{
  "issue_id": 1,
  "goal": "specific code change",
  "files": [],
  "acceptance_tests": []
}
```

## Output

```json
{
  "changed_files": [],
  "validation": [],
  "status": "ready_for_review"
}
```

## Workflow

1. Read issue/plan.
2. Read target files.
3. Make smallest edit via File Editor MCP.
4. Run narrow validation.
5. Update issue with result.

## Finish Rule

Không báo xong nếu validation chưa pass hoặc blocker chưa rõ.
