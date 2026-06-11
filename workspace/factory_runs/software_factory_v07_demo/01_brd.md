# Business Requirements Document

## Inputs
- vision: `workspace\factory_runs\software_factory_v07_demo\00_vision.md`

## Business Goals
- The product must satisfy the user-visible workflow described in the prompt.
- The product must be runnable locally with simple commands.
- The product must include validation evidence before it is considered done.

## Stakeholders
- Requesting user: wants a working local coding-agent outcome.
- Future maintainer: needs understandable modules, tests, and docs.
- QA/review roles: need measurable acceptance criteria.

## In-Scope Capabilities
- create default world
- advance one tick
- choose automatic person action
- apply action effects
- summarize world state
- save and load world state
- run terminal demo

## Constraints
- stdlib-only Python
- deterministic terminal execution
- no graphics dependency
- plain assert tests
- save/load compatibility

## Business Risks
- Ambiguous idea-to-code jumps can create the wrong product.
- Early pattern selection can overfit design before real variation is known.
- Missing validation creates false completion.

## Explicit Rule
This BRD does not select technical patterns. It only defines business need,
scope, constraints, and measurable outcomes.
