# Future And Extension MCPs

File này gom các MCP mở rộng đã có và hướng cho MCP tương lai. Các MCP core có file riêng; các MCP mở rộng vẫn được mô tả ở đây để tránh docs bị rải quá nhiều.

## Đã Triển Khai

| Server | File | Purpose |
|---|---|---|
| `file_editor` | `mcp_servers/file_editor_server.py` | View/create/replace/insert file có audit |
| `terminal` | `mcp_servers/terminal_server.py` | Command argv cho validation/probe, có risk metadata |
| `fetch` | `mcp_servers/fetch_server.py` | Fetch một URL |
| `search` | `mcp_servers/search_server.py` | Web search |
| `document` | `mcp_servers/document_server.py` | Extract/write/outline docs |
| `ledger` | `mcp_servers/ledger_server.py` | Append-only memory |
| `playwright` | `mcp_servers/playwright_server.py` | Browser text/screenshot |
| `code_index` | `mcp_servers/code_index_server.py` | Symbol/reference/dependency graph |
| `lint_test` | `mcp_servers/lint_test_server.py` | Compile/lint/test structured validation |
| `docker` | `mcp_servers/docker_server.py` | Docker status/logs, mutation opt-in |
| `obsidian` | `mcp_servers/obsidian_server.py` | Local markdown vault |
| `issue` | `mcp_servers/issue_server.py` | Local SQLite issue tracker |

## Design Rules For New MCPs

- Một MCP chỉ nên có một trách nhiệm chính.
- Có sandbox path nếu chạm filesystem.
- Có timeout/max size.
- Có schema trong `features/mcp_tools/schemas.py`.
- Có prompt examples.
- Có deterministic smoke nếu tool là core path.
- Có test prompt nếu agent cần học cách dùng.
- Side effect phải có metadata và guardrail.

## MCP Nên Thêm Sau

Chỉ thêm khi permission matrix đã rõ:

- Repo hosting MCP: GitHub/GitLab issue/PR thật.
- Package manager MCP: npm/pip audit có allowlist.
- Browser form MCP: cần user approval rõ.
- Deployment MCP: cần role/risk gate riêng.

## Không Nên Thêm

- Shell full quyền.
- Secret manager tự ghi/xuất secret vào prompt.
- Docker destructive tools.
- Cloud deployment mutation không có approval flow.
