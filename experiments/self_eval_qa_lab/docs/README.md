# Self Eval QA Lab Docs

This docs tree belongs to the mini repo itself. Keep implementation, operations, and audit rules here so the lab can evolve without forcing readers to inspect root-level project docs first.

## Docs Map

- `01_ARCHITECTURE.md`: v0.3 flow and component responsibilities.
- `02_RUNBOOK.md`: daily commands for mock, manual ChatGPT, server, and local model runs.
- `03_TRACE_AND_AUDIT.md`: full trace layout, admin trace, trace health, critical audit.
- `04_REAL_LLM_TESTING.md`: real LLM integration test setup and failure interpretation.
- `05_PRODUCTION_CHECKLIST.md`: pre-production checklist.
- `06_AGENT_CONTRACTS.md`: expected input/output behavior for each agent.
- `07_DATASET_BENCHMARKS.md`: CoT Hub/Open CoT Leaderboard-style dataset runner and batch review cadence.
- `evolution_proposals/README.md`: proposal registry for future runtime changes.
- `run_file_map/README.md`: full file map for running the mini repo, including external project files.
- `run_file_map/00_NEW_CONTRIBUTOR_GUIDE.md`: beginner-friendly guide for prompt, context, flow, and common edits.
- `run_file_map/06_DETAILED_PROMPT_FLOW.md`: detailed prompt flow and system-prompt influence map.

## Non-Negotiables

- Every run stores full prompts, inputs, raw outputs, public rationales, and handoffs.
- `admin/full_trace.json` is the no-truncation admin artifact.
- Hidden internal chain-of-thought is not fabricated or exposed; public rationale and raw emitted outputs are logged.
- ChatGPT baseline is always represented: mock, local, server, or manual-pending artifact.
- Critical audit and evolution decisions are proposal-only by default.
