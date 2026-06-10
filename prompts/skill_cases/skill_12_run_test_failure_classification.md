Use run_test.

Yêu cầu:

1. Tạo file code/skill_run_test_fail.py với nội dung:

assert 1 == 2, "intentional failure"

2. Chạy python.run_python path "code/skill_run_test_fail.py".
3. Không sửa file.
4. Chỉ phân loại kết quả.
5. Final bằng tiếng Việt:
- command/tool đã chạy
- result class phải là test failure hoặc assertion failure
- key stderr lines
- recommended next action

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
