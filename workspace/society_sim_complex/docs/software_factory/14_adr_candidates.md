# ADR Candidates

## Inputs
- pattern_decision: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\09_pattern_decision.md`
- api_inventory: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\13_api_inventory.json`

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

## Candidate ADR-0008: Business Logic Contract Before Architecture
- Status: Proposed
- Context: BRD/PRD artifacts can remain too high-level for coding agents.
- Decision: Add a Business Logic Department that converts domain analysis into
  invariants, decision tables, state transitions, failure modes, and testable
  examples before technical design.
- Consequences: Code/Test agents receive executable intent instead of broad
  business prose. The extra gate adds one artifact but reduces rework.

## Candidate ADR-0009: Compact Code Handoff Packet
- Status: Proposed
- Context: Strict JSON is still valuable for routing and tool calls, but not
  for long business reasoning.
- Decision: Package the Code Agent handoff as compact JSON containing artifact
  refs, read order, and output contract.
- Consequences: Keeps parse reliability while preserving access to full
  business/product/domain context.

## Pattern Evidence Excerpt
```text
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
- Why needed now: evidence exists in c...
```
