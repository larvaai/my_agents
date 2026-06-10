Test Issue Tracker MCP.

Yeu cau:
1. Goi issue.issue_create voi title "ISSUE_MCP_OK", description "Kiem tra issue tracker MCP local", kind "task", priority 2, assignee "planner_agent", labels ["test","mcp"], related_files ["mcp_servers/issue_server.py"].
2. Goi issue.issue_list status "open" limit 50.
3. Lay issue_id vua tao, goi issue.issue_add_comment message "Issue tracker MCP hoat dong." author "tester_agent".
4. Goi issue.issue_update voi issue_id do, status "in_progress".
5. Goi issue.issue_get voi issue_id do.
6. Final bang tieng Viet:
   - issue co tao duoc khong
   - issue_id la gi
   - list co thay issue khong
   - comment co luu khong
   - update status co thanh cong khong
   - issue_get co du comments/status khong

Khong commit.
Chi tra JSON tool call hoac JSON final.
