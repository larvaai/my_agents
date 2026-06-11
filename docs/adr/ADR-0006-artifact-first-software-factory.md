# ADR-0006: Artifact-First Software Factory

## Status

Accepted

## Context

The project uses strict JSON for agent actions because it makes tool calls easy
to validate, repair, audit, and block. That rule works well for coding actions.
It does not work well for long business/product/domain analysis because large
JSON strings are fragile and hard to review.

Complex prompts need a path from user idea to product evidence before code:

```text
Intake Protocol -> Vision -> BRD -> PRD -> Story -> AC
  -> Domain -> Business Logic -> Technical -> Pattern -> Implementation Spec
  -> Code Handoff Packet
```

## Decision

Add Software Factory v0.7 as an artifact-first specification pipeline.

Long content is written to Markdown or JSON artifacts under:

```text
workspace/factory_runs/<run_id>/
```

The agent control envelope stays compact:

```text
agent + decision + route + artifact_refs + missing_inputs + metadata
```

v0.7 adds:

- Intake Protocol Agent to choose compact JSON control plus artifact analysis.
- Business Logic Model and Validator to convert business/domain analysis into
  invariants, decision tables, state transitions, failure modes, and testable
  examples.
- Code Handoff Packager Agent to produce a small JSON packet with artifact refs
  and Code Agent contract.

## Consequences

Positive:

- Business and domain analysis can be long without breaking JSON parsing.
- Business logic is explicit before technical analysis and pattern decisions.
- Code Agent receives both a full implementation spec and a compact handoff
  packet.
- Coding agents receive a focused implementation spec instead of a raw idea.
- Pattern decisions become auditable through artifact traces.
- Docs can be compiled from evidence instead of invented from memory.

Tradeoffs:

- Artifact retention and cleanup need policy later.
- The real coding pipeline must learn to consume generated implementation specs.
- Docs verification must be rerun after code changes.
