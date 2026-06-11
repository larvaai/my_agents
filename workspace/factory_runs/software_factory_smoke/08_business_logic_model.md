# Business Logic Model

## Inputs
- domain_analysis: `workspace\factory_runs\software_factory_smoke\07_domain_analysis.md`
- acceptance_criteria: `workspace\factory_runs\software_factory_smoke\04_acceptance_criteria.md`

## Purpose
Convert business/product/domain analysis into a logic contract that Code and
Test agents can implement without reinterpreting the business intent.

## Domain
life-simulation engine

## Invariants
- Every need value stays in the inclusive range 0.0..100.0 after every tick and action.
- World time advances deterministically: 24 hours roll into the next day.
- A person can have at most one active home_id and one active job_id.
- Relationship updates from socialize are symmetric for actor and target.
- Save/load preserves population, houses, jobs, clock, and recent event data.

## Decision Table
| Condition | Rule or Action | Expected Outcome |
| --- | --- | --- |
| hunger < 35 | eat | restore hunger and spend a small amount of money |
| energy < 30 | sleep | restore energy and slightly reduce social |
| hygiene < 30 | clean | restore hygiene |
| current hour is inside assigned job schedule | work | earn salary and improve job skill |
| social < 40 | socialize | increase social and relationship score |
| fun < 40 | play | increase fun and reduce energy |
| no urgent need | idle | make a small neutral recovery |

## State Transitions
- Simulation.step increments tick, updates hour/day, then processes each person.
- Each person runs decay_needs -> choose_action -> apply_action -> calculate_mood.
- World events are appended for meaningful actions and daily rollovers.
- Simulation.run repeats step for a requested number of ticks and returns the final state.

## Testable Examples
- A hungry person chooses eat before work or play.
- A rested worker inside work hours earns money after one work action.
- Two people who socialize both receive increased relationship scores.
- A world saved to JSON and loaded back has the same population count.

## Failure Modes to Guard
- Need values drift outside 0..100.
- Socialize changes only one side of a relationship.
- Persistence serializes dataclasses but cannot reconstruct them.
- CLI demo claims success without exercising save/load.

## Logic Handoff Rule
This artifact is the bridge from business analysis to executable logic. The
Code Agent may choose implementation syntax, but it must preserve these
invariants, decision rules, and testable examples unless it routes back to
business analysis with a concrete conflict.
