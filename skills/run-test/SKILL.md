---
name: run-test
description: Run whitelisted validation commands, read stdout and stderr, classify failures, and decide whether to fix or stop. Use when the user asks for run_test, test execution, validation, linting, type checks, compile checks, or command output analysis.
---

# Run Test

Alias: `run_test`.

Run only commands that are explicitly allowed by the project or this skill.

## Whitelist

Allowed command families:

- `python -m py_compile ...`
- `python -m pytest ...`
- `pytest ...`
- `npm test`
- `npm run test`
- `npm run lint`
- `npm run typecheck`
- `git status`
- `git diff`

If a requested command is outside the whitelist, stop and ask for approval or report that no safe whitelisted command is available.

## Workflow

1. Choose the narrowest relevant command.
2. Run one command at a time.
3. Read stdout, stderr, and exit code.
4. Classify the result as pass, test failure, syntax/import error, lint/type error, environment/dependency error, or command not allowed.
5. If the failure maps to a small code fix and the user asked for fixing, continue with the appropriate editing/debug skill.
6. If the failure is environmental, destructive, or needs a non-whitelisted command, stop and report clearly.

## Output

Report the command, result class, key stdout/stderr lines, and recommended next action.
