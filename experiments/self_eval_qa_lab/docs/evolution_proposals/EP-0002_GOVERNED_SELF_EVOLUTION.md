# EP-0002: Governed Self Evolution

Status: proposed

## Problem

The current lab can observe its own run, criticize the process, and produce an
evolution decision. That is useful, but it is still proposal-only. The next
question is how to safely give the model authority to add, remove, or edit
agents and flow after it has observed the full multi-agent trace for a prompt.

The danger is that unrestricted self-editing can create agent sprawl, brittle
prompts, overfit routing, hidden regressions, or changes that look clever for
one case but reduce dataset performance.

## Proposed Direction

Move the lab toward governed self-evolution:

```text
run prompt
  -> save full trace
  -> critical auditor reviews process logic
  -> evolution decider proposes change
  -> evidence aggregator checks repeated pattern
  -> change planner writes a normalized evolution plan
  -> candidate profile is generated
  -> tests and dataset batch compare old vs candidate
  -> promotion gate accepts, revises, or rejects
```

The model should not directly rewrite core Python during normal operation.
Instead, the model should edit a constrained agent/flow manifest or create a
candidate profile that the runner can validate.

## Permission Levels

Use explicit evolution permission levels:

```text
level 0: observe only
level 1: propose only
level 2: create candidate profile, not active by default
level 3: apply to experimental profile after tests pass
level 4: production promotion requires human approval
```

Current v0.3 behavior is level 1. The first implementation of this proposal
should target level 2.

## Agent Graph Manifest

Introduce a config-driven agent graph so the model can change behavior without
writing arbitrary runtime code.

Candidate shape:

```yaml
agents:
  - id: answer_synthesizer
    kind: text
    prompt_file: agents/answer_synthesizer.md
    inputs:
      - question
      - simple_answer
      - critic_notes
    outputs:
      type: markdown
    max_tokens: 1536
    tools_allowed: []

flows:
  assisted:
    steps:
      - simple_answer
      - answer_critic
      - answer_synthesizer
    gates:
      - id: rewrite_if_material_issue
        when: critic_requests_material_rewrite
        action: run answer_synthesizer
```

The runner validates this manifest before use. Unknown agent kinds, missing
prompt files, cycles, duplicated step ids, impossible gates, and missing output
contracts should fail fast.

## Change Types

Allowed model-driven changes at level 2:

- Add an agent from an approved template.
- Remove an agent from a flow when repeated evidence shows redundancy.
- Edit an agent prompt in a candidate profile.
- Change routing thresholds or workflow selection rules.
- Change output contracts for a structured agent.
- Add a tool or skill request as a proposal, not as an active tool.
- Change token budgets within configured min and max limits.

Blocked at level 2:

- Editing core Python runtime files.
- Adding network tools without explicit approval.
- Disabling trace logging, baseline comparison, or critical audit.
- Applying changes to the default profile automatically.

## Evidence Rules

A model can request a candidate change after a single run, but promotion should
require repeated evidence.

Recommended gates:

- At least 20 dataset cases before batch-level changes.
- At least 3 repeated trace-health findings for the same failure mode.
- No promotion when parse success is below the configured evaluable threshold.
- No promotion if the candidate improves one metric while causing severe trace
  regressions.
- One meaningful change per candidate unless the failure requires a paired
  prompt/schema update.

## Critical Thinking Contract

The critical agent should review the whole process, not just the final answer:

- Was the selected workflow justified by the question?
- Did agents repeat each other without adding information?
- Did any handoff lose important context?
- Did a critic request a rewrite that was skipped?
- Did an agent output become too short, malformed, or generic?
- Did the final answer improve over the simple answer and ChatGPT baseline?
- Was the cost/latency justified by answer quality?

The output should be a public audit summary with concrete evidence from the
trace. It should not claim to expose hidden internal chain-of-thought.

## New Runtime Components

Add these pieces later, in order:

- `EvidenceAggregator`: groups trace-health and audit findings across runs.
- `EvolutionPlan`: normalized JSON/YAML change request.
- `GraphValidator`: validates candidate agent graph and flow manifests.
- `CandidateProfileWriter`: writes candidate prompts/config under `var/`.
- `RegressionRunner`: compares default profile vs candidate profile.
- `PromotionGate`: enforces metrics, rollback, and approval policy.

## Candidate Storage

Store generated candidates outside the live source tree first:

```text
var/self_eval_qa_lab/evolution_candidates/<candidate_id>/
  proposal.json
  agent_graph.yaml
  prompts/
  validation.json
  regression_summary.md
```

Only after acceptance should a human or controlled implementation step copy the
candidate into source-controlled config or prompts.

## Metrics

Compare default vs candidate on:

- Dataset accuracy.
- Final-answer parse success.
- Trace health clean rate.
- JSON/XML repair rate.
- Repeated-output findings.
- Handoff-loop findings.
- Average latency and token budget.
- Win rate versus simple answer and ChatGPT baseline.

## Test Plan

Add tests for:

- Candidate graph schema validation.
- Cycle detection in flow steps.
- Rejection of unknown agent ids and missing prompt files.
- Candidate profile creation under `var/` only.
- Promotion gate rejecting changes with low parse success.
- Promotion gate rejecting changes that disable trace or baseline artifacts.
- Mock A/B comparison of default profile vs candidate profile.

Add real model validation after level 2 exists:

```powershell
python main.py lab self_eval_qa_lab dataset --llm-provider local --limit 20 --subsets logiqa --review-every 20 --candidate-profile <candidate_id> --chatgpt-mode mock
```

## Acceptance Criteria

Level 2 can be considered implemented when:

- The model can create a candidate profile from a critical audit.
- The candidate profile never edits live source files.
- The runner can validate and reject unsafe candidate graphs.
- A/B dataset comparison writes a clear promotion report.
- Promotion remains disabled unless explicitly requested.

## Rollback

Candidate profiles are inactive by default. Rollback is deleting or ignoring:

```text
var/self_eval_qa_lab/evolution_candidates/<candidate_id>/
```

If a candidate is promoted later, keep a source-controlled diff and preserve the
previous profile as `default` so the runner can switch back.
