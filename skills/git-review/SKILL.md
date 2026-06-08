---
name: git-review
description: Review local Git changes without committing by checking status and diff, summarizing modified files, and suggesting commit messages. Use when the user asks for git_review, git status, git diff, local change review, pre-commit review, or commit message suggestions without committing.
---

# Git Review

Alias: `git_review`.

Never commit while using this skill.

## Workflow

1. Run `git status`.
2. Run `git diff` for unstaged changes.
3. Run `git diff --staged` only when staged files exist.
4. Summarize changed files by purpose.
5. Call out risky or surprising changes.
6. Suggest one concise commit message.
7. Stop before `git add`, `git commit`, `git push`, branch changes, reset, checkout, or stash unless the user explicitly asks.

## Output

Return:

- Status summary
- Diff summary
- Risks or review notes
- Suggested commit message

Keep the review factual and do not modify the repository.
