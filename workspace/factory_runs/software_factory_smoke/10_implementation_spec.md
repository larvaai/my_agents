# Implementation Specification

## Inputs
- protocol_strategy: `workspace\factory_runs\software_factory_smoke\00_protocol_strategy.json`
- vision: `workspace\factory_runs\software_factory_smoke\00_vision.md`
- brd: `workspace\factory_runs\software_factory_smoke\01_brd.md`
- prd: `workspace\factory_runs\software_factory_smoke\02_prd.md`
- stories: `workspace\factory_runs\software_factory_smoke\03_epics_stories.md`
- acceptance_criteria: `workspace\factory_runs\software_factory_smoke\04_acceptance_criteria.md`
- domain_analysis: `workspace\factory_runs\software_factory_smoke\07_domain_analysis.md`
- business_logic_model: `workspace\factory_runs\software_factory_smoke\08_business_logic_model.md`
- business_logic_validation: `workspace\factory_runs\software_factory_smoke\08_business_logic_validation.json`
- technical_analysis: `workspace\factory_runs\software_factory_smoke\08_technical_analysis.md`
- pattern_decision: `workspace\factory_runs\software_factory_smoke\09_pattern_decision.md`

## Target Project
`society_sim`

## Files to Create or Modify
- `society_sim/models.py`
- `society_sim/rules.py`
- `society_sim/world.py`
- `society_sim/simulation.py`
- `society_sim/persistence.py`
- `society_sim/cli_demo.py`
- `society_sim/test_society_sim.py`

## Implementation Order
1. Create the target folder.
2. Create data/domain models first.
3. Create pure business rules or service logic.
4. Create orchestration/runtime logic.
5. Create persistence or I/O adapters.
6. Create CLI/demo entrypoints.
7. Create tests last, then run tests and demo.

## Business Logic Contract
- Implement the invariants and decision table from `business_logic_model`.
- Convert each testable example into an assert-based, unit, or integration
  check appropriate to the project.
- Do not reinterpret business rules inside CLI, persistence, or reporting code.

## Coding Agent Contract
- Stay inside the requested target folder unless this spec says otherwise.
- Use the smallest implementation that satisfies acceptance criteria.
- Do not choose new design patterns during coding without returning to Pattern Decision.
- Use file editor tools for source edits and terminal/python tools only for validation.
- Return docs metadata: implemented_files, entrypoints, test_commands, env_vars,
  public_interfaces, and docs_notes.
- Keep tool-call JSON small. If the implementation needs long reasoning,
  write or read artifacts and pass compact references instead.

## Expected Compact Code Result Shape
```json
{
  "decision": "implemented_or_blocked",
  "docs_metadata_ref": "artifact path when metadata is long",
  "implemented_files": [
    "path/to/file.py"
  ],
  "test_commands": [
    {
      "command": "python path/to/test.py",
      "status": "pass|fail"
    }
  ]
}
```

## Suggested Validation
- Run the project test command from the prompt if present.
- Run the demo or entrypoint if present.
- Finish only when validation passes or a concrete blocker is reported.

## Original User Prompt
```text
Build a terminal-only Python mini-project named `society_sim`.
    It must include people, houses, jobs, a world clock, automatic actions,
    save/load, a CLI demo, and assert-based tests. Do not use external packages.
    Required files: society_sim/models.py society_sim/rules.py
    society_sim/world.py society_sim/simulation.py society_sim/persistence.py
    society_sim/cli_demo.py society_sim/test_society_sim.py
```
