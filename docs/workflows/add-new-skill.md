# Workflow: Add New Skill

## Goal

Thêm hướng dẫn hành vi mới cho agent mà không thêm tool/capability mới.

## Steps

1. Tạo folder `skills/<skill-name>/`.
2. Tạo `skills/<skill-name>/SKILL.md`.
3. Thêm YAML frontmatter `name` và `description`.
4. Viết workflow ngắn, guardrails, output.
5. Nếu cần UI metadata, tạo `skills/<skill-name>/agents/openai.yaml`.
6. Thêm prompt test vào `prompts/skill_cases/` hoặc `run_all_cases.py`.
7. Chạy skill test.

## Validation

```powershell
python run_all_cases.py --group skill --fail-fast
```

## Skill Nên Có

- Alias nếu cần.
- Khi nào dùng.
- Khi nào không dùng.
- Workflow theo bước.
- Guardrails.
- Output kỳ vọng.

## Template

Xem:

```text
docs/templates/skill-template.md
```

