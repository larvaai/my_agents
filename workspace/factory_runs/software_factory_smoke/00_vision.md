# Product Vision

## Inputs
- protocol_strategy: `workspace\factory_runs\software_factory_smoke\00_protocol_strategy.json`

## Mission
Build `society_sim` as a useful, testable software product, not just a
code exercise.

## User Intent
Build a terminal-only Python mini-project named `society_sim`.
    It must include people, houses, jobs, a world clock, automatic actions,
    save/load, a CLI demo, and assert-based tests. Do not use external packages.
    Required files: society_sim/models.py society_sim/rules.py
    society_sim/world.py society_sim/simulation.py society_sim/persistence.py
    society_sim/cli_demo.py society_sim/test_society_sim.py

## Product Outcome
- Deliver a working life-simulation engine.
- Preserve the explicit constraints from the user prompt.
- Produce enough evidence for downstream coding, testing, review, and docs.

## Operating Mode
- Task mode: `coding_execution`.
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
