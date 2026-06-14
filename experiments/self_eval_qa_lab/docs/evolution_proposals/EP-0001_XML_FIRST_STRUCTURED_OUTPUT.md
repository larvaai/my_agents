# EP-0001: XML-first Structured Output

Status: saved for later implementation.

## Problem

Some local models lose answer quality when forced directly into strict JSON
mode. The JSON contract helps the runner parse outputs, but it can also make the
model produce short, stiff, or under-reasoned fields. This is especially visible
for judge, critic, and evolution agents where the quality of the reasoning
summary matters.

## Proposed Change

Use XML-first output for structured agents, then parse the XML into JSON inside
the runner.

The model should answer in this shape:

```xml
<reasoning>
Public reasoning summary for the decision. This is not hidden chain-of-thought.
</reasoning>
<result>
{"field": "value"}
</result>
```

The runner will:

- Parse `<reasoning>` as `public_reasoning`.
- Parse `<result>` as the strict JSON object used by the system.
- Validate the JSON object with the existing schema checks.
- Save raw XML output, parsed JSON, and public reasoning into the trace.
- Fall back to the existing JSON repair path if XML parsing fails.

## JSON Fallback Variant

If a provider only supports strict JSON schema mode, put the free-form public
reasoning field first:

```json
{
  "public_reasoning": "Public reasoning summary, not hidden chain-of-thought.",
  "final_answer": "Short result"
}
```

This is a fallback path, not the preferred path.

## Scope

Primary code targets:

- `main.py`: add XML parsing helpers and update `call_json_agent`.
- `config.yaml`: add `structured_output.mode`, defaulting to `xml_then_json`.
- `docs/06_AGENT_CONTRACTS.md`: document the new structured output contract.
- Tests: add parser, repair, and trace assertions.

Agents affected:

- `question_classifier`
- `blind_evaluator`
- `error_analyzer`
- `flow_observer`
- `lesson_extractor`
- `critical_auditor`
- `evolution_decider`

Text answer agents should stay as free-form text agents.

## Trace Requirements

Every structured call must preserve:

- Full prompt.
- Full raw model output.
- Parsed `<reasoning>` public summary.
- Parsed `<result>` JSON.
- Validation status.
- Repair attempt output if parsing or validation fails.
- Deterministic fallback event if repair also fails.

The admin artifact `admin/full_trace.json` remains the no-truncation view.

## Safety Boundary

The lab may store public reasoning summaries and raw emitted model outputs. It
must not claim to expose hidden internal chain-of-thought. Prompts should use
terms like `public_reasoning`, `rationale`, or `analysis_summary`, not hidden
CoT.

## Test Plan

Add unit tests for:

- Parsing XML with plain JSON inside `<result>`.
- Parsing XML with fenced JSON inside `<result>`.
- Rejecting missing `<result>` and entering repair/fallback.
- Preserving `public_reasoning` in parsed agent output.
- Logging XML parse status and repair status in trace events.
- Keeping existing mock mode deterministic.

Add one real local LLM smoke test after implementation:

```powershell
python main.py lab self_eval_qa_lab dataset --llm-provider local --limit 3 --subsets logiqa --review-every 20 --chatgpt-mode mock --baseline-mode none --prompt-style strict_final
```

## Acceptance Criteria

This proposal can be marked implemented when:

- `python -m unittest discover -s tests` passes.
- A 3-case local dataset smoke run parses all structured agent outputs.
- Trace health does not report JSON fallback loops.
- Dataset parse success does not regress versus the latest strict-final smoke.
- Docs explain the new contract clearly enough for adding future agents.

## Rollback

Keep `structured_output.mode` configurable. If XML-first hurts a provider, set:

```yaml
structured_output:
  mode: json
```

The old JSON repair path should remain available.
