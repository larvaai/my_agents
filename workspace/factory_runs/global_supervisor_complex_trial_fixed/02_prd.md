# Product Requirements Document

## Inputs
- vision: `workspace\factory_runs\global_supervisor_complex_trial_fixed\00_vision.md`
- brd: `workspace\factory_runs\global_supervisor_complex_trial_fixed\01_brd.md`

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
- `society_sim_complex/__init__.py`
- `society_sim_complex/constants.py`
- `society_sim_complex/models.py`
- `society_sim_complex/catalog.py`
- `society_sim_complex/rules.py`
- `society_sim_complex/actions.py`
- `society_sim_complex/autonomy.py`
- `society_sim_complex/relationships.py`
- `society_sim_complex/events.py`
- `society_sim_complex/economy.py`
- `society_sim_complex/world.py`
- `society_sim_complex/simulation.py`
- `society_sim_complex/persistence.py`
- `society_sim_complex/reporting.py`
- `society_sim_complex/cli_demo.py`
- `society_sim_complex/test_society_sim_complex.py`

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
