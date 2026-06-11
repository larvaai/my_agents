# Product Vision

## Mission
Build `society_sim` as a useful, testable software product, not just a
code exercise.

## User Intent
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

## Product Outcome
- Deliver a working life-simulation engine.
- Preserve the explicit constraints from the user prompt.
- Produce enough evidence for downstream coding, testing, review, and docs.

## Non-Goals
- Do not choose implementation patterns in this document.
- Do not write code from the raw idea.
- Do not claim delivery before validation evidence exists.

## Success Signal
The factory can trace every code-facing requirement back to Vision, BRD, PRD,
Story, Acceptance Criteria, Domain Analysis, and Change Hotspots.
