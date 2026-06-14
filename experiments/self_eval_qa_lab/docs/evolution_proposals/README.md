# Evolution Proposals

This folder stores proposed runtime changes before implementation. Each proposal
is a separate file so we can choose one candidate to implement, test, or reject
without mixing it with unrelated ideas.

## Proposal Index

- `EP-0001_XML_FIRST_STRUCTURED_OUTPUT.md`: XML-first structured output for JSON agents.
- `EP-0002_GOVERNED_SELF_EVOLUTION.md`: controlled model-driven changes to agents and flow after critical audit.
- `EP-0003_USER_AGENT_INTERRUPT_CONTROL.md`: live user directives that can interrupt and replan an active run.

## Lifecycle

```text
observed_issue
  -> proposal
  -> candidate implementation
  -> mock tests
  -> real LLM smoke
  -> dataset batch
  -> accept / revise / reject
```

## Rules

- A proposal is not runtime behavior.
- A proposal must include evidence, scope, test plan, acceptance criteria, and rollback.
- Runtime changes should be config/prompt/profile driven whenever possible.
- Core Python changes should be explicit implementation work, not automatic model edits.
- Public reasoning and raw emitted outputs can be logged; hidden internal chain-of-thought is not claimed or fabricated.

## Template

```markdown
# EP-XXXX: Title

Status: proposed

## Problem
Observed failure or bottleneck.

## Evidence
Run ids, dataset summaries, trace health findings, or test failures.

## Proposed Change
What to change and why.

## Scope
Files, agents, prompts, tools, and config touched.

## Test Plan
Unit, mock, and real LLM checks.

## Acceptance Criteria
What must be true before merging.

## Rollback
How to turn it off safely.
```
