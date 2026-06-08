---
name: debug-traceback
description: Debug an exception or failing run from traceback output by reading from the bottom, locating the file and line, making the smallest fix, and rerunning validation. Use when the user asks for debug_traceback or provides a traceback, stack trace, exception, failing test, or runtime error.
---

# Debug Traceback

Alias: `debug_traceback`.

Start from the concrete failure, not from a rewrite.

## Workflow

1. Read the traceback from bottom to top.
2. Identify the final exception type, message, file, and line number.
3. Read that file and nearby code.
4. Read caller files only when needed to understand inputs or state.
5. Form one likely root cause.
6. Apply the smallest local fix.
7. Rerun the failing command or closest available test.
8. If the error changes, repeat from the new traceback.

## Output

Report:

- Root cause
- File and line touched
- Fix applied
- Test command run
- Remaining failure, if any

Avoid speculative rewrites and broad refactors.
