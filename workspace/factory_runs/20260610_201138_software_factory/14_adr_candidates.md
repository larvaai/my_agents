# ADR Candidates

## Inputs
- pattern_decision: `workspace\factory_runs\20260610_201138_software_factory\09_pattern_decision.md`
- api_inventory: `workspace\factory_runs\20260610_201138_software_factory\13_api_inventory.json`

## Candidate ADR-0006: Artifact-First Software Factory
- Status: Proposed
- Context: Business and product analysis can be too long for strict tool-call JSON.
- Decision: Store long analysis in versioned artifacts and pass compact JSON
  references through the agent protocol.
- Consequences: Better parse reliability, easier audit, and clearer handoff to
  coding agents. Requires artifact cleanup/retention policy later.

## Candidate ADR-0007: Pattern Decisions Require Hotspot Evidence
- Status: Proposed
- Context: Product specs should not select design patterns directly.
- Decision: Pattern Decision Agent must map every pattern to hotspot/story/AC evidence.
- Consequences: Reduces overengineering and keeps architecture traceable.

## Pattern Evidence Excerpt
```text
# Pattern Decision

## Inputs
- domain_analysis: `workspace\factory_runs\20260610_201138_software_factory\07_domain_analysis.md`
- technical_analysis: `workspace\factory_runs\20260610_201138_software_factory\08_technical_analysis.md`

## Change Hotspot Evidence
- need decay rates
- action priority rules
- job schedule and salary rules
- relationship changes
- world persistence schema
- summary/reporting fields
- test and demo execution markers

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
- Trace: need decay rates, action priority rules, relationship changes
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
```
