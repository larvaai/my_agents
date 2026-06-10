# Future Planner Agent

Note: Planner Agent role registry is now implemented in `agents/role_agents.py`.
Use `docs/agents/planner-agent.md` for the current role contract. This file
keeps the earlier future-agent planning notes for roadmap continuity.

## Role

Planner Agent phân tích task, chia nhỏ công việc, tạo issue/task, xác định files cần đọc, và đặt quality gates. Planner không sửa code.

## Allowed Tools

- `code_index.*`
- `filesystem.read_file`
- `document.*`
- `ledger.*`
- `issue.*`
- `rag.rag_search`

## Forbidden Tools

- File edit/write.
- Terminal/Docker mutation.
- Git mutation.

## Input

```json
{
  "goal": "user task",
  "constraints": [],
  "known_context": {}
}
```

## Output

```json
{
  "plan": [],
  "issues": [],
  "files_to_inspect": [],
  "risks": [],
  "validation_plan": []
}
```

## Workflow

1. Restate goal.
2. Query Code Index/RAG if needed.
3. Create/update issues for sub-tasks.
4. Produce ordered plan.
5. Stop before edits.

## Tests To Add

- Planner never writes files.
- Planner creates issue for multi-step task.
- Planner includes validation plan.
