# Trace And Audit

## Artifact Layout

```text
var/self_eval_qa_lab/<run_id>/
  run.json
  summary.md
  admin/full_trace.json
  prompts/*.md
  outputs/*.md
  traces/events.jsonl
  traces/agent_calls.jsonl
  traces/handoffs.jsonl
  audits/trace_health.json
  audits/critical_audit.json
  audits/evolution_decision.json
```

## What Is Logged

Each agent event stores:

- agent name
- step
- model/provider
- resolved system prompt
- user/input prompt
- raw emitted output
- public rationale
- handoff target and reason
- character counts
- JSON parse status for JSON agents

`admin/full_trace.json` embeds the full event list and full prompt/output payloads without truncation.

## What Is Not Logged

The lab does not invent or expose hidden internal chain-of-thought. It logs what the runtime actually has: prompts, inputs, raw emitted outputs, public rationale, and handoff metadata.

## Trace Health

`analyze_trace_health` checks:

- repeated outputs across different agents
- duplicate agent/step calls
- empty or tiny outputs
- invalid JSON fallback
- code output when this no-code lab did not ask for code
- handoff loops

## Repair And Reconcile Guards

- JSON agents get a minimum output budget and a repair pass when the first output is empty, malformed, or schema-invalid.
- Text agents get a no-code repair pass when they emit markdown code fences, JSON blocks, shell commands, or source code despite no-code constraints.
- Flow Observer output is reconciled against the selected workflow and actual lens trace.
- Critical Auditor output is reconciled against trace facts so hallucinated findings do not drive evolution decisions.
- Raw failed outputs are still stored in `outputs/*.md`; repaired/reconciled outputs are separate events.

Production real-LLM runs should target:

```json
{
  "status": "clean",
  "severe_count": 0,
  "looping_detected": false,
  "json_fallbacks": [],
  "handoff_loops": [],
  "code_violations": []
}
```

## Critical Audit

Critical Auditor uses:

- workflow decision
- workflow trace
- trace health
- ChatGPT comparison
- flow observation
- agent call events

It should be blunt. If an agent repeats another agent, returns invalid JSON, or adds no new signal, the audit should mark it.

## Evolution Decision

Evolution Decider is proposal-only. It may propose:

- routing policy changes
- agent gating/removal
- prompt changes
- output schema changes
- skills/tools additions

It must not apply changes automatically.
