Use project_plan.

Mục tiêu:
Lập kế hoạch thêm một quality gate cho RAG để không trả context rác khi score thấp.

Yêu cầu:
- Chỉ lập kế hoạch.
- Không sửa file.
- Không dùng filesystem.write_file.
- Không dùng git commit.
- Có thể dùng filesystem.list_directory hoặc filesystem.read_file nếu cần đọc context.
- Final phải gồm:
  - Goal
  - Files to inspect
  - Task breakdown
  - Risks and edge cases
  - Open questions nếu có

Chỉ trả JSON tool call hoặc JSON final.
