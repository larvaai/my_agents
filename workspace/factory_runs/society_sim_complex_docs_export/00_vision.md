# Product Vision

## Inputs
- protocol_strategy: `workspace\factory_runs\society_sim_complex_docs_export\00_protocol_strategy.json`

## Mission
Build `society_sim_complex` as a useful, testable software product, not just a
code exercise.

## User Intent
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

## Product Outcome
- Deliver a working life-simulation engine.
- Preserve the explicit constraints from the user prompt.
- Produce enough evidence for downstream coding, testing, review, and docs.

## Operating Mode
- Task mode: `business_to_logic`.
- Control channel: `compact_json_envelope`.
- Analysis channel: `artifact_files`.
- Long reasoning is stored as artifacts; JSON stays small and parseable.

## Non-Goals
- Do not choose implementation patterns in this document.
- Do not write code from the raw idea.
- Do not claim delivery before validation evidence exists.

## Success Signal
The factory can trace every code-facing requirement back to Vision, BRD, PRD,
Story, Acceptance Criteria, Domain Analysis, and Change Hotspots.
