Test Obsidian MCP local.

Yeu cau:
1. Goi obsidian.obsidian_write_note path "Projects/MCP Test.md", content "# MCP Test\n\nOBSIDIAN_MCP_OK", overwrite true.
2. Goi obsidian.obsidian_read_note path "Projects/MCP Test.md".
3. Goi obsidian.obsidian_search_notes query "OBSIDIAN_MCP_OK" folder "Projects" limit 10.
4. Goi obsidian.obsidian_list_notes folder "Projects" limit 50.
5. Final bang tieng Viet:
   - write note co ok khong
   - read note co dung OBSIDIAN_MCP_OK khong
   - search co tim thay note khong
   - list co thay Projects/MCP Test.md khong

Khong commit.
Chi tra JSON tool call hoac JSON final.
