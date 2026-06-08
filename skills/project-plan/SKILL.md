---
name: project-plan
description: Read a coding request, identify files to inspect, split the task into ordered steps, and assess risk without editing code. Use when the user asks for project_plan, planning, a task breakdown, impact analysis, or a read-only implementation plan before code changes.
---

# Project Plan

Alias: `project_plan`.

Operate in read-only mode for the entire task.

## Workflow

1. Read the user's request and restate the goal in one sentence.
2. Identify likely files or directories to inspect.
3. Read only enough context to understand the work.
4. Split the task into small ordered steps.
5. Identify risks, edge cases, and missing information.
6. Stop before any write, edit, move, delete, commit, or formatting command.

## Output

Return a concise plan with:

- Goal
- Files to inspect
- Task breakdown
- Risks and edge cases
- Open questions, only if blocking

Never modify files while using this skill.
