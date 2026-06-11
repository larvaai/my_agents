# Product Vision

## Inputs
- protocol_strategy: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\00_protocol_strategy.json`

## Mission
Build `society_sim_complex` as a useful, testable software product, not just a
code exercise.

## User Intent
Build a terminal-only Python mini-project named `society_sim_complex`.
    It needs business logic, acceptance criteria, required files:
    society_sim_complex/models.py society_sim_complex/autonomy.py
    society_sim_complex/simulation.py society_sim_complex/test_society_sim_complex.py.
    Include quality gates and save/load.

## Product Outcome
- Deliver a working life-simulation engine.
- Preserve the explicit constraints from the user prompt.
- Produce enough evidence for downstream coding, testing, review, and docs.

## Operating Mode
- Task mode: `business_to_logic`.
- Control channel: `compact_json_envelope`.
- Analysis channel: `artifact_files`.
- Long reasoning is stored as artifacts; JSON stays small and parseable.

## Non-Goals
- Do not choose implementation patterns in this document.
- Do not write code from the raw idea.
- Do not claim delivery before validation evidence exists.

## Success Signal
The factory can trace every code-facing requirement back to Vision, BRD, PRD,
Story, Acceptance Criteria, Domain Analysis, and Change Hotspots.
