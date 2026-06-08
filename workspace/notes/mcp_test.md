# Test MCP Tools

**Thời điểm test:** $(date)

## Các MCP đã test:
1. **Filesystem MCP** - Quản lý file và thư mục trong workspace sandboxed.
2. **Git MCP (local)** - Thao tác Git cho repo local tại D:\Agent PRJ\my_agents.
3. **Context7 MCP** - Tìm kiếm tài liệu từ các library như OpenAI, React, v.v.

## Kết quả nhanh:
- ✅ `list_directory`: Liệt kê thành công thư mục gốc.
- ⏳ `write_file`: Đang tạo file notes/mcp_test.md...
- ⏳ `read_file`: Sẽ đọc lại sau khi viết xong.
- ⏳ `search_files`: Sẽ tìm file vừa tạo trong workspace.
- ⏳ `git_status`: Kiểm tra trạng thái repo local.
- ⏳ `git_diff_unstaged`: Xem thay đổi chưa stage.
- ⏳ `resolve-library-id`: Tìm library ID cho OpenAI Python SDK.
- ⏳ `query-docs`: Hỏi về chat completions create.