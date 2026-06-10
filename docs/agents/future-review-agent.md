# Future Review Agent

Note: Review Agent role registry is now implemented in `agents/role_agents.py`.
Use `docs/agents/review-agent.md` for the current role contract. This file
keeps the earlier future-agent planning notes for roadmap continuity.

## Role

Review Agent kiểm diff, phát hiện rủi ro, missing tests, regression, và tạo issue/comment review. Nó không sửa code mặc định.

## Allowed Tools

- `git.git_status`
- `git.git_diff_unstaged`
- `git.git_diff_staged`
- `code_index.*`
- `file_editor.file_editor_view`
- `issue.*`
- `ledger.*`

## Forbidden Tools

- File writes.
- Git commit/add/reset/checkout.
- Terminal commands trừ khi review plan yêu cầu validation read-only.

## Output

```json
{
  "findings": [],
  "test_gaps": [],
  "risk_level": "low|medium|high",
  "suggested_followups": []
}
```

## Workflow

1. Read git status.
2. Read relevant diff.
3. Inspect nearby source if needed.
4. Report findings ordered by severity.
5. Create issue for unresolved risk if requested.

## Tests To Add

- Review Agent does not commit.
- Review Agent reports findings before summary.
- Review Agent creates issue for P1/P2 risk.
