# Product Requirements Document

## Inputs
- vision: `workspace\factory_runs\20260610_201138_software_factory\00_vision.md`
- brd: `workspace\factory_runs\20260610_201138_software_factory\01_brd.md`

## Functional Requirements
- Support workflow: create default world.
- Support workflow: advance one tick.
- Support workflow: choose automatic person action.
- Support workflow: apply action effects.
- Support workflow: summarize world state.
- Support workflow: save and load world state.
- Support workflow: run terminal demo.

## Required Interfaces
- CLI or script entrypoint for local execution.
- Automated validation command.
- Final report with files changed, test evidence, limits, and next steps.

## Requested Files or Modules
- `society_sim/__init__.py`
- `society_sim/models.py`
- `society_sim/rules.py`
- `society_sim/world.py`
- `society_sim/simulation.py`
- `society_sim/persistence.py`
- `society_sim/cli_demo.py`
- `society_sim/test_society_sim.py`

## Product-Level Quality Requirements
- stdlib-only Python.
- deterministic terminal execution.
- no graphics dependency.
- plain assert tests.
- save/load compatibility.

## Out of Scope
- Unrequested external packages.
- Unrequested UI or graphics.
- Repository-wide refactors outside the target scope.

## Product Rule
The PRD is still not allowed to choose design patterns. It prepares stories and
acceptance criteria for later analysis.
