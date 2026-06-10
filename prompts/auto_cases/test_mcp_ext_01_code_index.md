Test Code Index MCP.

Yeu cau:
1. Goi code_index.code_index voi path "mcp_servers" max_files 100.
2. Goi code_index.code_find_symbol voi name "terminal_run" path "mcp_servers" max_results 20.
3. Goi code_index.code_find_references voi name "FastMCP" path "mcp_servers" max_results 30.
4. Goi code_index.code_dependency_graph voi path "mcp_servers" max_files 100.
5. Final bang tieng Viet, bat buoc co CODE_INDEX_MCP_OK va bao cao:
   - index ok khong va scan bao nhieu file
   - co tim thay terminal_run khong
   - references FastMCP co khong
   - dependency graph co du lieu khong

Khong sua file. Khong commit.
Chi tra JSON tool call hoac JSON final.
