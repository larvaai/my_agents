# Rebuild Roadmap

## Nguyên Tắc Rebuild

- Không copy toàn bộ repo ngay.
- Mỗi milestone có một runtime chạy được.
- Mỗi milestone có smoke test.
- Không thêm multi-agent trước khi single-agent + tools + validation ổn.
- Không thêm Software Factory trước khi artifact protocol rõ.
- Không thêm UI trước khi event log và inspect ổn.

## Milestone M0 - Project Baseline

Scope:

- Repo skeleton.
- Runtime paths.
- Prompt loader.
- Dev check compile.

Exit criteria:

- `python -m compileall -q .` pass.
- `python main.py` chạy được ở fake mode.

## Milestone M1 - Single-Agent JSON Runtime

Scope:

- LLM adapter.
- Tool Agent prompt.
- Orchestrator parse final/tool JSON.
- Simple retry.

Exit criteria:

- Prompt final JSON pass.
- Invalid JSON retry pass.

## Milestone M2 - Event Log And Inspect

Scope:

- EventLogger.
- events.jsonl.
- summary.json.
- inspect CLI.

Exit criteria:

- Một run có MessageEvent/ActionEvent/StateEvent.
- `inspect_runs.py list/events latest` chạy được.

## Milestone M3 - Kernel And Capability Contract

Scope:

- AgentKernel.
- CapabilityRegistry.
- ToolPort.
- CapabilityResult.
- Feature loader.

Exit criteria:

- Kernel tests pass.
- Disabled feature không crash.

## Milestone M4 - Minimal Tools And Sandbox

Scope:

- file_editor view/create/write_lines/replace/insert.
- python sandbox.
- path safety.

Exit criteria:

- Create file, read/view file, run Python file.
- Path escape blocked.

## Milestone M5 - JsonGate And Tool Schemas

Scope:

- JsonGate parse/repair.
- Tool schema registry.
- Tool alias resolution.
- Policy dry-run.

Exit criteria:

- JsonGate smoke pass.
- Unsafe path/git mutation blocked.

## Milestone M6 - MCP Adapter

Scope:

- MCP server config.
- MCP stdio client.
- Adapter feature.
- Schema/policy integrated.

Exit criteria:

- Kernel -> MCP tool call works.
- Tool result normalized.

## Milestone M7 - Validation Discipline

Scope:

- lint_test server.
- terminal safe runner.
- finish gate.
- context condenser.
- repeated tool/failure guards.

Exit criteria:

- Code edit requires validation.
- Failed tool twice stops.
- Same tool loop blocked.

## Milestone M8 - Test Harness

Scope:

- run_all_cases.
- run_dev_checks.
- deterministic smoke scripts.

Exit criteria:

- Quick checks pass.
- Prompt cases can be run by group/case.

## Milestone M9 - Role Agents

Scope:

- BaseAgent.
- Role registry.
- Tool allowlists.
- Lenses as prompt/spec.

Exit criteria:

- Role permission smoke pass.
- Code/Test/Review/Ledger boundaries enforced.

## Milestone M10 - LangGraph Multi-Agent Runtime

Scope:

- AgentState.
- Role nodes.
- Tool node.
- route_next.
- last_failure repair flow.

Exit criteria:

- LangGraph compile smoke pass.
- Failed-test repair guard pass.

## Milestone M11 - Company Agents v0.5

Scope:

- Deterministic department agents.
- Department result contract.
- Code/Test orchestrator.
- Full company orchestrator.

Exit criteria:

- Code/Test smoke pass.
- Company smoke pass.

## Milestone M12 - Software Factory v0.7

Scope:

- Artifact protocol.
- Factory agents.
- Product/business/domain/logic/technical/docs artifacts.
- Handoff packet.

Exit criteria:

- Software Factory smoke pass.
- Required artifact keys exist.
- Implementation spec can be fed to coding path.

## Milestone M13 - Global Supervisor

Scope:

- Intent router.
- Knowledge agents.
- Research department skeleton.
- Safety department.
- Final synthesis.

Exit criteria:

- Global supervisor smoke pass.
- Product prompt routes to Software Factory.
- Prompt injection blocked.

## Milestone M14 - Hardening

Scope:

- Encoding cleanup.
- RAG health and failure quality.
- More test coverage.
- Docs verification.
- MCP process pooling design.

Exit criteria:

- `run_dev_checks.py --full` pass.
- Docs and traceability updated.

## Suggested Work Order For New Repo

Sprint 1:

- M0, M1, M2.

Sprint 2:

- M3, M4.

Sprint 3:

- M5, M6.

Sprint 4:

- M7, M8.

Sprint 5:

- M9, M10.

Sprint 6:

- M11.

Sprint 7:

- M12.

Sprint 8:

- M13, M14.

Không chuyển sprint nếu exit criteria của milestone trước chưa pass.

