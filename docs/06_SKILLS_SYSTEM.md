# Skills System

## Skill Là Gì?

Skill là hướng dẫn Markdown giúp agent hành xử đúng trong một loại task. Skill không phải tool. Skill không chạy code; nó điều khiển cách agent chọn tool và báo cáo.

## Vị Trí

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
```

Loader:

```text
tools/skill_loader.py
```

Agent prompt ghép skills qua:

```text
agents/tool_agent.py -> build_skills_prompt()
```

## Format SKILL.md

Mỗi skill cần YAML frontmatter:

```md
---
name: code-edit
description: Make a narrowly scoped code change...
---

# Code Edit

Workflow...
```

`name` và `description` là bắt buộc.

## Skills Hiện Có

| Skill | Khi dùng | Luật chính |
|---|---|---|
| `project-plan` | Lập kế hoạch read-only | Không sửa file |
| `code-edit` | Sửa code nhỏ | Đọc file trước, sửa hẹp |
| `debug-traceback` | Debug lỗi/traceback | Bắt đầu từ lỗi cụ thể |
| `run-test` | Chạy validation | Chỉ command an toàn |
| `git-review` | Review diff | Không commit |

## Khi Nào Tạo Skill Mới?

Tạo skill khi:

- Có workflow lặp lại nhiều lần.
- Cần guardrail hành vi.
- Không cần tool/API mới.
- Muốn agent có cách làm ổn định hơn chỉ prompt user.

Không tạo skill khi:

- Cần quyền hoặc capability mới: hãy tạo MCP.
- Chỉ là hướng dẫn một lần.
- Nội dung quá phụ thuộc một task cụ thể.

## Test Skill

Skill nên có prompt case trong `prompts/skill_cases/` hoặc `prompts/auto_cases/`, và được nối vào `run_all_cases.py`.

Xem workflow:

```text
docs/workflows/add-new-skill.md
```

