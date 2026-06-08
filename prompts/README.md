# Prompt Files

- `system_prompt.md`: system prompt của Tool Agent. Giữ `{{MCP_TOOLS}}` nếu bạn muốn tự động chèn danh sách MCP hiện tại.
- `user_prompt.md`: user prompt mặc định khi chạy `python main.py`.
- `test_mcp_prompt.md`: prompt test Filesystem MCP, Git MCP local, và Context7 MCP.

Chạy prompt mặc định:

```powershell
python main.py
```

Chạy một file prompt cụ thể:

```powershell
python main.py prompts/test_mcp_prompt.md
```
