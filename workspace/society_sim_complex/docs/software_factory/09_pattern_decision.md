# Pattern Decision

## Inputs
- domain_analysis: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\07_domain_analysis.md`
- business_logic_model: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\08_business_logic_model.md`
- business_logic_validation: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\08_business_logic_validation.json`
- technical_analysis: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\08_technical_analysis.md`

## Change Hotspot Evidence
- need decay rates
- action priority rules
- job schedule and salary rules
- relationship changes
- world persistence schema
- summary/reporting fields
- test and demo execution markers

## Business Logic Evidence
Pattern choices must preserve the logic contract. If a pattern does not make
invariants, decision tables, state transitions, or validation examples easier
to implement and test, it is rejected.

## Decisions
### Decision P01: Domain Model with dataclasses
- Problem solved: Multiple domain objects need explicit state and serialization.
- Why needed now: evidence exists in change hotspots.
- If not used: State would spread across loose dictionaries and tests would be brittle.
- Overengineering risk: Low; dataclasses are stdlib and match the requested model objects.
- Target module: `models.py`
- Trace: Domain Objects, save/load compatibility
### Decision P02: Pure rule functions
- Problem solved: Need/action/mood rules are the primary change hotspot.
- Why needed now: evidence exists in change hotspots.
- If not used: Simulation step would become a large conditional block that is hard to test.
- Overengineering risk: Low; functions are simpler than a class hierarchy or strategy framework.
- Target module: `rules.py`
- Trace: need decay rates, action priority rules, relationship changes, Business Logic Model decision table
### Decision P03: Small persistence adapter
- Problem solved: Save/load is a side effect that should not pollute domain logic.
- Why needed now: evidence exists in change hotspots.
- If not used: Serialization details would leak into simulation and tests.
- Overengineering risk: Low; only one adapter module, no repository framework.
- Target module: `persistence.py`
- Trace: world persistence schema, save/load compatibility

## Explicit Rejections
- Do not introduce a framework-sized pattern without repeated variation.
- Do not use Observer/Event Bus for a small terminal simulation until event
  consumers multiply.
- Do not use ECS unless entity/component variation becomes the main problem.

## Gate Rule
Code may start only after each selected pattern traces to a hotspot, story, or
acceptance criterion.
