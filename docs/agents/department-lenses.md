# Department Lenses

This project treats core role agents like a small software company.

```text
Department Agent = main accountable role
Role Lens        = narrow cognitive evaluator inside that department
Orchestrator     = coordinator
Ledger           = company memory and audit trail
```

Rule:

```text
Lenses suggest.
Department agents decide.
Orchestrator routes.
Only allowed executor tools perform real actions.
```

## Engineering Department

Agent: `code`

Purpose: implement scoped source changes and hand off to QA.

Lenses:

- `implementation`: direct task implementation.
- `integration`: compatibility with existing modules, config, prompts, tools, and APIs.
- `defensive_coding`: malformed input, exception, timeout, empty result, and JSON/tool failure modes.
- `refactor_discipline`: avoid broad refactors; only make necessary small changes.
- `developer_experience`: names, error messages, docs, and test commands should help the next developer.

Important rule: Engineering does not approve its own work and does not run validation in the LangGraph role split.

## QA Department

Agent: `test`

Purpose: act as Test Council: plan validation, run the narrowest real tests, classify failures.

Lenses:

- `logic`: invariants, impossible states, edge cases, state transitions.
- `critical_thinking`: hidden assumptions, adversarial cases, false-pass risks.
- `experienced_qa`: high-value practical tests, integration, regression, dirty data.
- `regression`: prior failures, affected tests, issue and ledger context.
- `purpose_alignment`: technically passing but conceptually wrong behavior.
- `test_executor`: the only QA lens allowed to run validation tools.

Important rule: QA never edits source code. If validation fails because of code, route back to Engineering with evidence.

## Senior Review Board

Agent: `review`

Purpose: review correctness, scope, security, maintainability, and release risk.

Lenses:

- `senior_engineer`: code quality, simplicity, idioms, obvious bugs.
- `scope_diff`: changed files vs requested scope.
- `security_review`: path traversal, secret exposure, unsafe shell, permission and network risk.
- `maintainability`: readability, boundaries, duplication, future maintenance cost.
- `release_risk`: approve, request changes, or escalate to human review.

Important rule: Review does not edit files and does not mutate git.

## Ledger / Audit / Operations

Agent: `ledger`

Purpose: maintain durable project memory, task state, decisions, audit consistency, and incidents.

Lenses:

- `historian`: record what happened, files changed, tests run, final outcome.
- `task_state`: manage task state transitions.
- `decision_record`: capture decisions, rationale, and alternatives.
- `auditor`: find contradictions such as done with failing tests or approval with blockers.
- `incident_tracker`: turn repeated failures or tool incidents into issues or ledger records.

Important rule: Ledger/Ops records and audits. It does not implement code or run terminal.

## Output Pattern

Department agents still use the normal JSON action protocol:

```json
{
  "action": "final",
  "finish_reason": "handoff",
  "message": "short synthesis",
  "department_report": {
    "agent": "test_agent",
    "lens_results": [],
    "decision": "approve|request_changes|blocked|needs_more_info",
    "confidence": "low|medium|high",
    "required_next_actions": []
  }
}
```

## v0.5 Runtime Lens Results

The direct Code/Test v0.5 runner turns lens specs into concrete runtime
`lens_results`.

Files:

```text
agents/code_agent.py
agents/test_agent.py
orchestration/code_test_orchestrator.py
```

By default the v0.5 runner uses deterministic lens results so smoke tests are
fast and stable. Add `--use-llm` to experiment with model-generated lens JSON:

```powershell
python run_code_test_agents_demo.py --version v0.5 --agent orchestrator --use-llm
```

The route decision is not inferred from prose. Each department returns:

```json
{
  "route": {
    "next_agent": "test_agent",
    "reason": "Implementation is ready for QA validation."
  }
}
```

This is the core v0.5 rule: lens results influence synthesis, synthesis drives
executor plans, executor evidence drives route decisions.

Tool calls remain normal:

```json
{
  "action": "tool",
  "tool": "python.run_python",
  "args": {
    "path": "code/example.py",
    "timeout": 10
  }
}
```
