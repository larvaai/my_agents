Hãy test Filesystem MCP và Python MCP.

Yêu cầu chạy lần lượt:

1. Dùng filesystem.write_file tạo file code/project_smoke_test.py với nội dung:

print("PROJECT_SMOKE_TEST_OK")

2. Dùng filesystem.read_file đọc lại code/project_smoke_test.py.

3. Dùng python.run_python chạy code/project_smoke_test.py với timeout 10.

4. Final bằng tiếng Việt:
- write_file có ok không
- read_file có đúng nội dung không
- run_python có returncode 0 không
- stdout có PROJECT_SMOKE_TEST_OK không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
