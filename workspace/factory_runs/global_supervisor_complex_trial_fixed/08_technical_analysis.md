# Technical Analysis

## Inputs
- domain_analysis: `workspace\factory_runs\global_supervisor_complex_trial_fixed\07_domain_analysis.md`
- business_logic_model: `workspace\factory_runs\global_supervisor_complex_trial_fixed\08_business_logic_model.md`
- business_logic_validation: `workspace\factory_runs\global_supervisor_complex_trial_fixed\08_business_logic_validation.json`

## Module Boundaries
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

## Business Logic Boundary
- Implement the Business Logic Model as explicit rules, policies, or pure
  functions before wiring CLI, persistence, or reporting.
- Treat decision tables and invariants as test inputs, not as optional prose.
- If the logic contract conflicts with requested files or constraints, route
  back to Business Logic Model instead of inventing a new pattern.

## Data and State
- Keep business/domain state separate from CLI/demo/reporting code.
- Keep persistence isolated from simulation or workflow logic.
- Keep validation scripts deterministic and local.

## Integration Boundaries
- Local filesystem for source files and generated runtime artifacts.
- Local Python runtime for validation.
- No external packages unless the user explicitly allows them.

## Risk Analysis
- Long, business-heavy prompts can exceed JSON comfort limits.
- Coding agents may overstep into planning if artifact gates are missing.
- A passing test marker must be observed before finish.

## Rule
This document may describe module boundaries and risks, but it still does not
select a design pattern. Pattern choice needs hotspot-to-module evidence.
