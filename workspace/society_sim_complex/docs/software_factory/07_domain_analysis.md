# Domain Analysis and Change Hotspots

## Inputs
- prd: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\02_prd.md`
- stories: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\03_epics_stories.md`
- acceptance_criteria: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\04_acceptance_criteria.md`
- product_critique: `D:\Agent PRJ\my_agents\workspace\_global_supervisor_smoke\factory_runs\global_supervisor_product_smoke\06_product_spec_critique.md`

## Domain
life-simulation engine

## Actors
- player/operator
- simulated person
- world clock

## Domain Objects
- Person
- House
- Job
- WorldEvent
- WorldState
- Simulation
- Persistence

## Use-Case Flows
- create default world
- advance one tick
- choose automatic person action
- apply action effects
- summarize world state
- save and load world state
- run terminal demo

## Change Hotspots
- need decay rates
- action priority rules
- job schedule and salary rules
- relationship changes
- world persistence schema
- summary/reporting fields
- test and demo execution markers

## Side Effects
- File creation or update in the target workspace.
- Local command execution for validation.
- Optional save/load artifacts produced by the generated product.

## Non-Functional Requirements
- stdlib-only Python
- deterministic terminal execution
- no graphics dependency
- plain assert tests
- save/load compatibility

## Gate Rule
No pattern decision may be made without explicit hotspot evidence from this
document.
