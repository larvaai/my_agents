Hãy test Python MCP reject non-python file.

Yêu cầu:

1. Dùng filesystem.write_file tạo file notes/not_python.txt với nội dung "hello".

2. Gọi python.run_python với path "notes/not_python.txt" timeout 10.

3. Final bằng tiếng Việt:
- file txt có được tạo không
- python.run_python có chặn không
- error message có nói chỉ file .py được chạy không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
