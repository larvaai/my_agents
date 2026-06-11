# Test Strategy

## Test Philosophy

Repo này cần test theo tầng, không chỉ unit test. Lý do: phần khó nhất không
phải từng function riêng lẻ, mà là contract giữa LLM output, JsonGate, tool
schema, kernel, MCP server, orchestrator, role routing và final evidence.

## Test Pyramid Cho Rebuild

```text
Contract/unit tests
  -> deterministic smoke scripts
  -> MCP chain tests
  -> role/orchestration tests
  -> prompt regression tests
  -> optional real LLM/manual demos
```

## Required Gates Per Layer

| Layer | Gate |
|---|---|
| CLI/prompt | main reads prompt, exits clean |
| LLM adapter | mock/manual call |
| JSON loop | parse final/tool, retry invalid |
| Event log | events and summary written |
| Kernel | capability envelope tests |
| Feature loader | enabled/disabled feature tests |
| File/Python tools | path sandbox and execution tests |
| JsonGate | repair and block smoke |
| MCP adapter | registration + mocked adapter call |
| Validation | compile/run file/smoke suite |
| Role agents | allowlist permission smoke |
| LangGraph | compile, failure capture, repair guard |
| Company v0.5 | deterministic full chain smoke |
| Software Factory | artifact completeness smoke |
| Global Supervisor | router/safety/factory route smoke |

## Existing Test Commands

Quick:

```powershell
python run_dev_checks.py --quick
```

Full:

```powershell
python run_dev_checks.py --full
```

Individual:

```powershell
python run_kernel_smoke.py
python run_feature_tests.py
python run_json_gate_smoke.py
python run_agent_role_smoke.py
python run_langgraph_smoke.py
python run_mcp_chain_smoke.py
python run_code_test_agents_smoke.py
python run_company_agents_smoke.py
python run_software_factory_smoke.py
python run_global_supervisor_smoke.py
python run_capability_suite.py
```

Prompt regression:

```powershell
python run_all_cases.py --list
python run_all_cases.py --group capability --fail-fast
python run_all_cases.py --group chain --fail-fast
python run_all_cases.py --case orchestrator_01_json_only
```

## What To Assert

### JsonGate

- Pass valid tool/final.
- Recover common malformed JSON.
- Reject unknown tool.
- Reject missing required args.
- Reject unsafe path.
- Reject git mutation.
- Reject terminal shell shape.

### Tools

- Result has `ok`, `tool`, useful error.
- Sandbox escape blocked.
- Timeout returns structured failure.
- Dependency missing returns `dependency_failure`.
- Mutation tools require env opt-in.

### Orchestrator

- Logs every step.
- Condenses large tool results.
- Blocks repeated same tool call.
- Blocks final after code change without validation.
- Allows final blocker when validation impossible.

### Role Pipeline

- Role cannot call forbidden tool.
- Test failure routes to Code.
- Review does not approve without validation evidence.
- Ledger records only after useful evidence.
- Final does not mutate project.

### Software Factory

- All required artifact keys exist.
- Each artifact path exists.
- Implementation spec includes requested files.
- Business Logic Validation passes only when sections exist.
- Pattern Decision contains hotspot evidence.
- Code Handoff Packet uses artifact refs.

## Definition Of Done For Rebuild

A layer is done only when:

- Code compiles.
- Its smoke passes.
- Its docs mention files and commands accurately.
- Failures are structured, not tracebacks.
- No unrelated refactor is mixed into the layer.

