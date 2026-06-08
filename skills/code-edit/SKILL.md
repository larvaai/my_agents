---
name: code-edit
description: Make a narrowly scoped code change after reading relevant files. Use when the user asks for code_edit, a bug fix, an implementation change, editing source files, writing files, or a report of exactly which files changed.
---

# Code Edit

Alias: `code_edit`.

Make the smallest change that satisfies the request.

## Workflow

1. Read the request and identify the exact behavior to change.
2. Read the relevant file before editing it.
3. Edit only the smallest necessary region.
4. Preserve existing style, naming, imports, and architecture.
5. Avoid broad refactors, unrelated cleanup, formatting churn, or file moves.
6. Write the file.
7. Report the files changed and what changed in each.

## Guardrails

- Do not modify files that are unrelated to the request.
- If a wider refactor seems useful but not required, mention it as a follow-up instead of doing it.
- If a file has unrelated user changes, work around them and do not revert them.
- Prefer validation after editing when a relevant test or compile command is known.
