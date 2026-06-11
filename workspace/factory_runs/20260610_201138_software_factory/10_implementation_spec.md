# Implementation Specification

## Inputs
- vision: `workspace\factory_runs\20260610_201138_software_factory\00_vision.md`
- brd: `workspace\factory_runs\20260610_201138_software_factory\01_brd.md`
- prd: `workspace\factory_runs\20260610_201138_software_factory\02_prd.md`
- stories: `workspace\factory_runs\20260610_201138_software_factory\03_epics_stories.md`
- acceptance_criteria: `workspace\factory_runs\20260610_201138_software_factory\04_acceptance_criteria.md`
- domain_analysis: `workspace\factory_runs\20260610_201138_software_factory\07_domain_analysis.md`
- technical_analysis: `workspace\factory_runs\20260610_201138_software_factory\08_technical_analysis.md`
- pattern_decision: `workspace\factory_runs\20260610_201138_software_factory\09_pattern_decision.md`

## Target Project
`society_sim`

## Files to Create or Modify
- `society_sim/__init__.py`
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

## Coding Agent Contract
- Stay inside the requested target folder unless this spec says otherwise.
- Use the smallest implementation that satisfies acceptance criteria.
- Do not choose new design patterns during coding without returning to Pattern Decision.
- Use file editor tools for source edits and terminal/python tools only for validation.
- Return docs metadata: implemented_files, entrypoints, test_commands, env_vars,
  public_interfaces, and docs_notes.

## Suggested Validation
- Run the project test command from the prompt if present.
- Run the demo or entrypoint if present.
- Finish only when validation passes or a concrete blocker is reported.

## Original User Prompt
```text
Bạn là Coding Agent local.

Nhiệm vụ:
Tạo một mini-project Python tên `society_sim`, mô phỏng một xã hội nhỏ kiểu life-simulation game, lấy cảm hứng từ game mô phỏng đời sống nhưng không copy thương hiệu, asset, nhân vật hay nội dung cụ thể nào.

Mục tiêu:
Xây một simulation engine chạy bằng terminal, chưa cần đồ họa. Project phải đủ phức tạp để có:
- nhiều nhân vật
- nhu cầu cơ thể
- cảm xúc
- quan hệ xã hội
- công việc
- tiền
- nhà ở
- lịch ngày/đêm
- hành động tự động
- sự kiện xã hội
- save/load state
- test tự động

Phạm vi bắt buộc:
Chỉ tạo project trong thư mục:

society_sim/

Không sửa orchestrator.
Không sửa MCP.
Không sửa file ngoài `society_sim/` trừ khi cần tạo test runner nhỏ trong `society_sim/`.

Không dùng package ngoài stdlib Python.
Không cài package.
Không commit.

Yêu cầu cấu trúc file:

society_sim/
├── __init__.py
├── models.py
├── rules.py
├── world.py
├── simulation.py
├── persistence.py
├── cli_demo.py
└── test_society_sim.py

Chi tiết chức năng:

1. models.py

Tạo các dataclass:

Person:
- id: str
- name: str
- age: int
- money: float
- traits: list[str]
- skills: dict[str, float]
- needs: dict[str, float]
- mood: str
- home_id: str | None
- job_id: str | None
- relationships: dict[str, float]
- current_action: str

Needs bắt buộc:
- hunger
- energy
- social
- fun
- hygiene

Mỗi need nằm trong khoảng 0.0 đến 100.0.

House:
- id
- name
- capacity
- c...
```
