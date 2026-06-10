# Code Agent

## Role

Engineering Department.

Implements narrowly scoped source changes, then hands off to QA.

## Lenses

- `implementation`
- `integration`
- `defensive_coding`
- `refactor_discipline`
- `developer_experience`

## Allowed Tools

- Read-only file and code-index tools.
- `file_editor.*` for auditable source edits.
- `filesystem.create_directory`
- `filesystem.write_file`
- Limited issue/document read-update tools.

## Forbidden

- Validation tools in the LangGraph role split.
- Git mutation.
- Docker mutation.
- Broad file moves/deletes.

## Main Use

- Bug fix.
- Small implementation.
- Targeted repair after QA failure.
- Safe code generation.

## Finish Rule

Do not claim completion. Hand off to Test Agent after implementation.

## v0.5 Runtime

The direct v0.5 runtime lives in:

```text
agents/code_agent.py
```

It is separate from the LangGraph `code` role runtime.

v0.5 Code Agent output contains:

- `lens_results`
- `synthesis`
- `executor_plan`
- `execution`
- `records`
- `route`

Executor tools are intentionally narrow:

```text
file_editor.file_editor_write_lines
file_editor.file_editor_create
```

Route rules:

| Condition | Next |
|---|---|
| needs planning | `planner_agent` |
| executor failed | `code_agent` |
| executor passed | `test_agent` |

Smoke:

```powershell
python run_code_test_agents_demo.py --version v0.5 --agent code
```
