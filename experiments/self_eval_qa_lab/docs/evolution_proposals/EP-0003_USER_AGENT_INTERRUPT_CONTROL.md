# EP-0003: User Agent Interrupt Control

Status: proposed

## Problem

Current `self_eval_qa_lab` treats the user prompt as input at run start. After
the run begins, agents talk to each other, critique the process, and produce
evolution proposals, but the user cannot interrupt the live run with stronger
instructions.

For production use, this is backwards. A human user may notice that the flow is
overbuilt, missing an agent, using the wrong tool, or optimizing the wrong
answer. The live user instruction should carry much higher authority than an
agent's internal preference.

## Goal

Add a `User Agent` control-plane flow:

```text
user prompt
  -> normal agent flow starts
  -> user may send new prompt at any time
  -> User Agent parses it into directives
  -> Compliance Gate checks runtime invariants
  -> Flow Replanner updates active run plan
  -> affected agents are skipped, added, retried, or re-prompted
  -> final answer uses latest accepted user directive
```

The user directive should be treated as the strongest application-level signal,
below only hard runtime/safety invariants.

## Authority Order

Runtime should resolve conflicts in this order:

```text
1. System/runtime invariants
2. Latest accepted user directive
3. Original user question
4. Active run/evolution profile
5. Agent role prompts
6. Agent-to-agent suggestions
7. Heuristics and default routing
```

Examples:

- User says "bo bot critic agent" -> skip/remove critic for this run unless that
  breaks required audit output.
- User says "them mot agent kiem tra logic" -> add an approved logic-checker
  agent or create a candidate agent from an approved template.
- User says "them tool web search" -> request/add an approved tool if available;
  otherwise record a tool request proposal and explain the missing dependency.
- User says "dung lai, tra loi ngay" -> stop remaining optional agents and
  synthesize from current state.

## Non-overridable Invariants

The user is highly authoritative inside the lab, but some invariants should not
be disabled by any live directive:

- Keep trace logging on.
- Keep admin full trace on.
- Do not claim to expose hidden internal chain-of-thought.
- Do not fabricate unavailable tools or skills.
- Do not silently edit core Python runtime from a live answer run.
- Do not apply destructive filesystem/network actions from an answer-only lab.
- Do not hide that a requested directive was rejected, degraded, or postponed.

If a user directive conflicts with these invariants, the User Agent should record
the directive, explain the conflict, and select the closest safe action.

## Core Concept: User Directive

Every live user message becomes a normalized directive:

```json
{
  "directive_id": "userdir_0003",
  "received_at": "2026-06-14T...",
  "raw_text": "bo bot critic agent va them logic checker",
  "priority": "user_live",
  "scope": "current_run",
  "intent": "modify_flow",
  "operations": [
    {
      "op": "remove_agent",
      "target": "answer_critic",
      "mode": "skip_remaining"
    },
    {
      "op": "add_agent",
      "target": "logic_checker",
      "template": "structured_critic"
    }
  ],
  "status": "accepted",
  "notes": []
}
```

Directive intents:

```text
answer_instruction    Add/correct requirements for the final answer.
flow_control          Pause, resume, stop, retry, skip, restart from step.
modify_flow           Add/remove/reorder agents in this run.
modify_agent          Change prompt, role, output contract, temperature, tokens.
tool_request          Add/request a tool for this run or future candidate.
skill_request         Add/request a skill for this run or future candidate.
evaluation_override   Change what the evaluator should compare or prioritize.
```

## Runtime Flow

```text
UserInterruptInbox
  -> UserAgent
  -> DirectiveNormalizer
  -> ComplianceGate
  -> FlowReplanner
  -> ActiveRunState
  -> TraceRecorder
  -> AgentPromptInjector
```

### UserInterruptInbox

Accepts user messages while a run is active.

Initial implementation can support:

- `--interactive`: background stdin reader.
- `--control-dir var/self_eval_qa_lab/control/<run_id>/`: file-based inbox.
- Future API/websocket endpoint.

Inbox file shape:

```text
var/self_eval_qa_lab/<run_id>/control/inbox.jsonl
```

### UserAgent

Parses raw user text into one or more directives. It is not a normal answer
agent. It is a control-plane interpreter that converts user intent into actions
the runner can validate.

### ComplianceGate

Checks each directive against non-overridable invariants and current runtime
capabilities.

Possible statuses:

```text
accepted
accepted_with_degradation
rejected
deferred_to_evolution_proposal
needs_user_confirmation
```

### FlowReplanner

Updates the active run plan:

- Skip not-yet-run agents.
- Mark a running output as stale if it started before a new directive.
- Add a candidate agent from an approved template.
- Reorder optional agents.
- Restart a step with the latest directive injected.
- Stop optional work and synthesize immediately.

### AgentPromptInjector

Every future agent prompt gets a high-priority block:

```text
## Active User Directives

- [userdir_0003] Skip answer_critic for this run.
- [userdir_0003] Add logic_checker before final synthesis.
- Latest user directive wins over previous agent suggestions.
```

## Soft vs Hard Interrupt

Implement in two phases.

### Phase 1: Soft Interrupt Checkpoints

Fast implementation:

- Poll inbox before and after each agent call.
- Apply directives before starting the next agent.
- If a directive arrives while a model call is running, store it immediately but
  apply it after the call returns.
- If the completed output began before a newer directive, mark it as `stale` and
  optionally retry the affected step.

This gives useful user control without rewriting the LLM client around async
cancellation.

### Phase 2: Hard Interrupt During LLM Call

Later implementation:

- Run model calls in cancellable worker threads/processes or streaming mode.
- Background input thread watches stdin/control-dir/websocket.
- New user directive can set a cancellation token.
- Runner records the interrupted call as `cancelled_by_user_directive`.
- FlowReplanner restarts from the safest checkpoint.

## Agent Add/Remove Rules

Allowed in current run:

- Skip optional agents.
- Add an agent from an approved template.
- Change a text agent's visible instruction block.
- Change route between `direct`, `assisted`, `deep`, and `repo_debug`.
- Add a requested tool/skill only if it already exists in the approved registry.

Deferred to evolution proposal:

- New tool installation.
- New skill installation.
- New persistent agent file.
- Persistent default flow change.
- Core Python runtime change.

Blocked:

- Disable trace/admin logging.
- Hide user intervention records.
- Suppress audit artifacts.
- Pretend a tool exists when it does not.

## Suggested Approved Agent Templates

Start with simple templates:

```text
logic_checker        structured critic for logical consistency.
constraint_checker   checks whether latest user requirements are satisfied.
tool_planner         proposes tools/skills without executing unavailable tools.
brevity_editor       shortens answer when user says "bo bot".
evidence_checker     checks whether claims are supported by prompt/trace.
```

Each template should define:

```yaml
id: logic_checker
kind: text_or_structured
prompt_template: agents/templates/logic_checker.md
allowed_inputs:
  - question
  - active_user_directives
  - current_answer
  - trace_summary
allowed_outputs:
  - critique
  - required_rewrite
max_tokens: 768
tools_allowed: []
```

## Trace Requirements

Every user intervention must be preserved:

```text
var/self_eval_qa_lab/<run_id>/
  control/
    inbox.jsonl
    accepted_directives.jsonl
    rejected_directives.jsonl
  traces/
    user_directives.jsonl
  admin/
    full_trace.json
```

Each directive event should include:

- Raw user text.
- Normalized directive.
- Acceptance status.
- Before/after workflow graph.
- Agents skipped, added, retried, or marked stale.
- Whether final answer used the directive.

## Example Flow

User starts:

```text
Hay phan tich co nen dung multi-agent QA lab khong?
```

Run begins:

```text
Question Classifier -> assisted
Simple Answer -> Answer Critic ...
```

User interrupts:

```text
Bo bot critic. Them 1 agent chi kiem tra logic thoi. Tra loi ngan hon.
```

Runtime applies:

```text
UserAgent -> accepted directives
FlowReplanner:
  - skip answer_critic if not completed
  - add logic_checker before final
  - inject "tra loi ngan hon" into all future prompts
  - mark previous long draft as stale if needed
Final Synthesizer -> concise answer using latest directive
```

## Scope

Likely files to add later:

```text
experiments/self_eval_qa_lab/agents/user_agent.md
experiments/self_eval_qa_lab/agents/templates/logic_checker.md
experiments/self_eval_qa_lab/user_directives.py
experiments/self_eval_qa_lab/run_state.py
experiments/self_eval_qa_lab/flow_replanner.py
```

Likely files to modify later:

```text
experiments/self_eval_qa_lab/main.py
experiments/self_eval_qa_lab/config.yaml
experiments/self_eval_qa_lab/docs/01_ARCHITECTURE.md
experiments/self_eval_qa_lab/docs/06_AGENT_CONTRACTS.md
tests/test_self_eval_qa_lab.py
```

## Test Plan

Add tests for:

- User directive is parsed and logged.
- Latest directive wins when two user messages conflict.
- User can skip an optional not-yet-run agent.
- User can add an approved template agent.
- User can force immediate final synthesis.
- User directive is injected into subsequent agent prompts.
- A model output started before a directive can be marked stale.
- Requests to disable trace/admin logging are rejected.
- Requests for unavailable tools become tool proposals, not fake tools.

Mock integration tests:

```powershell
python main.py lab self_eval_qa_lab --mock --interactive "question"
python main.py lab self_eval_qa_lab --mock --control-dir var/tmp_control "question"
```

## Acceptance Criteria

Phase 1 is acceptable when:

- User messages can be accepted while a run is active.
- Directives are applied at agent boundaries.
- Final answer reflects the latest accepted directive.
- Full trace shows what changed and why.
- User cannot disable trace/admin artifacts.
- Existing non-interactive CLI behavior remains unchanged.

Phase 2 is acceptable when:

- A live LLM call can be cancelled or marked stale immediately after a user
  interrupt.
- The run restarts from a clear checkpoint.
- Cancelled/stale outputs are visible in admin trace.
- No agent silently ignores the latest accepted user directive.

## Rollback

Keep the flow disabled by default until stable:

```yaml
user_agent:
  enabled: false
  interrupt_mode: checkpoint
```

If the feature causes instability, disable `user_agent.enabled` and the old
single-prompt run behavior remains intact.
