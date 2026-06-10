Test Lint/Test MCP.

Yeu cau:
1. Goi lint_test.lint_compile voi path "mcp_servers" timeout 60.
2. Goi lint_test.test_python_file voi path "workspace/code/project_smoke_test.py" timeout 30.
3. Goi lint_test.test_smoke_suite voi timeout 60.
4. Khong goi terminal de validation trong case nay.
5. Final bang tieng Viet, bat buoc co LINT_TEST_MCP_OK va bao cao:
   - compile ok khong, checked_files bao nhieu
   - test_python_file co ok khong, stdout co PROJECT_SMOKE_TEST_OK khong
   - smoke suite co tra results khong

Khong sua file. Khong commit.
Chi tra JSON tool call hoac JSON final.
