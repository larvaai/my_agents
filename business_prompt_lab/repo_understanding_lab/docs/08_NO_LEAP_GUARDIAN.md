# No-Leap Guardian

The No-Leap Guardian is the critical observer for this lab.

Its job is not to be negative. Its job is to stop confident answers from weak
evidence.

## Core Rule

The system must separate:

```text
Observed evidence
Inference
Uncertainty
Next verification step
```

## Bad Pattern

```text
Planner is broken, so edit planner.py.
```

Why it is bad:

- no failing test cited
- no input object inspected
- no caller inspected
- no upstream/downstream check
- no config/runtime check

## Better Pattern

```text
The failing test checks PlannerAgent.plan output.
PlannerAgent.plan receives TaskContext from QuestionAnalyzer.
The trace shows TaskContext.intent is already null before PlannerAgent runs.
So the likely root cause is upstream of PlannerAgent or in fallback validation.
Recommended next step: inspect QuestionAnalyzer and the TaskContext creation
path before editing PlannerAgent.
```

## Guardian Checks

### Evidence Coverage

Did the answer cite:

- file
- symbol
- caller/callee
- test
- config/runtime command if relevant
- docs/ledger if relevant

### Unsupported Claims

Flag:

- "always"
- "never"
- "obviously"
- "the root cause is"
- "safe to change"

unless backed by evidence.

### Docs/Code Conflict

If docs and code disagree, final answer must say so.

### Import Versus Behavior

An import edge is not proof that runtime behavior uses that module.

### Test Adequacy

If a change or behavior claim is made, identify tests or explicitly say tests
were not found.

### Patch Readiness

A run is not ready for patch proposal unless it has:

- impact analysis
- target files
- related tests
- risks
- validation command

## Output Shape

```json
{
  "agent": "NoLeapGuardian",
  "no_leap_score": 0.84,
  "unsupported_claims": [],
  "missed_evidence": [],
  "required_next_checks": [],
  "verdict": "answer_supported"
}
```

## Score Meaning

```text
0.90 - 1.00: strong evidence discipline
0.75 - 0.89: usable, minor gaps
0.50 - 0.74: weak, answer should include more caveats
0.00 - 0.49: unsafe, rerun retrieval before final answer
```

