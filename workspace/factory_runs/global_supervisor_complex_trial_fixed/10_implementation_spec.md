# Implementation Specification

## Inputs
- protocol_strategy: `workspace\factory_runs\global_supervisor_complex_trial_fixed\00_protocol_strategy.json`
- vision: `workspace\factory_runs\global_supervisor_complex_trial_fixed\00_vision.md`
- brd: `workspace\factory_runs\global_supervisor_complex_trial_fixed\01_brd.md`
- prd: `workspace\factory_runs\global_supervisor_complex_trial_fixed\02_prd.md`
- stories: `workspace\factory_runs\global_supervisor_complex_trial_fixed\03_epics_stories.md`
- acceptance_criteria: `workspace\factory_runs\global_supervisor_complex_trial_fixed\04_acceptance_criteria.md`
- domain_analysis: `workspace\factory_runs\global_supervisor_complex_trial_fixed\07_domain_analysis.md`
- business_logic_model: `workspace\factory_runs\global_supervisor_complex_trial_fixed\08_business_logic_model.md`
- business_logic_validation: `workspace\factory_runs\global_supervisor_complex_trial_fixed\08_business_logic_validation.json`
- technical_analysis: `workspace\factory_runs\global_supervisor_complex_trial_fixed\08_technical_analysis.md`
- pattern_decision: `workspace\factory_runs\global_supervisor_complex_trial_fixed\09_pattern_decision.md`

## Target Project
`society_sim_complex`

## Files to Create or Modify
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
Ban la Coding Agent local.

Nhiem vu:
Tao mot mini-project Python ten `society_sim_complex`, mo phong mot he sinh thai
life-simulation terminal phuc tap hon ban `society_sim`. Lay cam hung tu game
mo phong doi song, nhung khong copy thuong hieu, asset, nhan vat, lore, UI hay
noi dung cu the nao.

Muc tieu:
Xay mot simulation engine chay bang terminal, stdlib-only, co du domain logic de
test nang luc LLM khi phai di tu business logic -> thiet ke -> code -> test.
Project phai co autonomy planner, household economy, relationships, schedules,
events, memory, persistence versioned JSON va test tu dong.

Pham vi bat buoc:
Chi tao va sua file trong thu muc:

society_sim_complex/

Khong sua orchestrator.
Khong sua MCP.
Khong sua file ngoai `society_sim_complex/`.
Khong dung package ngoai stdlib Python.
Khong cai package.
Khong commit.
Khong tao do hoa.
Khong dung pygame.

Yeu cau cau truc file:

society_sim_complex/
|-- __init__.py
|-- constants.py
|-- models.py
|-- catalog.py
|-- rules.py
|-- actions.py
|-- autonomy.py
|-- relationships.py
|-- events.py
|-- economy.py
|-- world.py
|-- simulation.py
|-- persistence.py
|-- reporting.py
|-- cli_demo.py
`-- test_society_sim_complex.py

Tong quan domain:

The gioi mac dinh phai co:
- it nhat 10 people
- it nhat 3 households
- it nhat 4 homes
- it nhat 6 jobs
- it nhat 6 locations
- it nhat 12 action types
- it nhat 6 random/daily event...
```
