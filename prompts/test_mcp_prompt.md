Hãy test 3 MCP hiện có trong project: Filesystem MCP, Git MCP local, Context7 MCP.

Yêu cầu chạy lần lượt:
1. Dùng filesystem.list_directory để liệt kê thư mục gốc workspace.
2. Dùng filesystem.write_file để tạo file notes/mcp_test.md với nội dung ngắn mô tả thời điểm test và tên 3 MCP.
3. Dùng filesystem.read_file để đọc lại notes/mcp_test.md.
4. Dùng filesystem.search_files để tìm file mcp_test.md trong workspace.
5. Dùng git.git_status để kiểm tra trạng thái repo local.
6. Dùng git.git_diff_unstaged để xem thay đổi chưa stage.
7. Dùng context7.resolve-library-id để tìm library ID cho "openai" với query "Python SDK chat completions".
8. Dùng context7.query-docs với library ID phù hợp từ bước 7 để hỏi "chat completions create".

Không commit thay đổi. Khi xong, trả final bằng tiếng Việt, tóm tắt tool nào ok/tool nào lỗi và trích ngắn kết quả quan trọng.
