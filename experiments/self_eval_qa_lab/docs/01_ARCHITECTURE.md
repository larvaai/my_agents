# Architecture

## v0.3 Flow

```text
Question
  -> Run Planner
  -> Question Classifier
  -> Workflow Router
  -> Simple Answer
  -> Direct / Assisted / Deep / Repo Debug Path
  -> Optional Baseline
  -> ChatGPT Baseline
  -> Blind Evaluator
  -> Error Analyzer
  -> Flow Observer
  -> Lesson Extractor
  -> Trace Health
  -> Critical Auditor
  -> Evolution Decider
  -> Ledger + Admin Full Trace
```

## Workflows

- `direct`: use the simple answer as final. Best for definitions and narrow clarifications.
- `assisted`: draft, critic, rewrite. Best for medium questions where a light review helps.
- `deep`: lens answer plus optional baseline. Best for architecture, strategy, multi-agent, and trade-off questions.
- `repo_debug`: local repo/debug reasoning. Avoid external baseline by default.

## Data Boundaries

- Source prompts live in `agents/`.
- Lens instructions live in `lenses/`.
- Runtime artifacts live under `var/self_eval_qa_lab/<run_id>/`.
- Ledger files live under `var/self_eval_qa_lab/ledger/`.
- The mini repo does not mutate prompts, skills, tools, or source code during normal runs.

## Production Principle

The lab should prove that a larger flow beats a smaller flow. If the trace shows repeated output, unnecessary agents, invalid JSON, or ChatGPT consistently winning, the right default action is proposal-only evolution, not silent self-modification.

## Proposed User Agent Flow

`EP-0003_USER_AGENT_INTERRUPT_CONTROL.md` proposes a future control-plane flow
where the user can send live directives while a run is active.

```text
Active Run
  -> UserInterruptInbox
  -> User Agent
  -> Compliance Gate
  -> Flow Replanner
  -> Active User Directives injected into future agents
  -> Final answer follows latest accepted user directive
```

The user directive has higher authority than agent-to-agent suggestions, but it
cannot disable trace/admin logging, fabricate unavailable tools, or claim hidden
internal chain-of-thought.
