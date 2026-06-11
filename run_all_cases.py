from __future__ import annotations

import os
import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = PROJECT_DIR / "prompts" / "auto_cases"
SKILL_CASES_DIR = PROJECT_DIR / "prompts" / "skill_cases"
RUNS_DIR = PROJECT_DIR / "test_runs"
GROUP_ORDER = ["capability", "rag", "project", "agent", "chain", "mcp_ext", "langgraph", "skill", "e2e", "orchestrator"]


@dataclass
class TestCase:
    name: str
    group: str
    prompt_file: str
    prompt: str
    expect_contains: list[str]
    expect_not_contains: list[str] | None = None
    timeout: int = 180
    entrypoint: str = "main.py"
    success_marker: str = "=== FINAL RESULT ==="
    pass_prompt_path: bool = True


TEST_CASES: list[TestCase] = [
    TestCase(
        name="capability_00_project_suite",
        group="capability",
        prompt_file="test_capability_00_project_suite.md",
        entrypoint="run_capability_suite.py",
        success_marker="PROJECT_CAPABILITY_SUITE_OK",
        pass_prompt_path=False,
        expect_contains=[
            "PROJECT_CAPABILITY_SUITE_OK",
            "router_capability",
            "global_supervisor_capability",
            "pdf_text_extraction_mcp",
            "existing_smoke_scripts",
        ],
        expect_not_contains=[
            "Traceback",
            "AssertionError",
        ],
        timeout=420,
        prompt="""
Deterministic project capability suite.
This prompt is not passed to the smoke entrypoint.
""".strip(),
    ),
    TestCase(
        name="langgraph_00_compile_smoke",
        group="langgraph",
        prompt_file="test_langgraph_00_compile_smoke.md",
        entrypoint="run_langgraph_smoke.py",
        success_marker="LANGGRAPH_COMPILE_OK",
        pass_prompt_path=False,
        expect_contains=[
            "LANGGRAPH_COMPILE_OK",
            "CompiledStateGraph",
        ],
        expect_not_contains=[
            "Traceback",
            "LangGraph is not installed",
        ],
        timeout=120,
        prompt="""
Deterministic LangGraph compile smoke.
This prompt is not passed to the smoke entrypoint.
""".strip(),
    ),
    TestCase(
        name="langgraph_01_json_gate_smoke",
        group="langgraph",
        prompt_file="test_langgraph_01_json_gate_smoke.md",
        entrypoint="run_json_gate_smoke.py",
        success_marker="JSON_GATE_SMOKE_OK",
        pass_prompt_path=False,
        expect_contains=[
            "JSON_GATE_SMOKE_OK",
            "PASS fenced_trailing_comma",
            "PASS unsafe_path",
            "PASS git_mutation_policy_blocked",
        ],
        expect_not_contains=[
            "Traceback",
            "AssertionError",
        ],
        timeout=120,
        prompt="""
Deterministic JsonGate smoke.
This prompt is not passed to the smoke entrypoint.
""".strip(),
    ),
    TestCase(
        name="rag_01_happy_path",
        group="rag",
        prompt_file="test_rag_01_happy_path.md",
        expect_contains=[
            "rag_test_basal_ganglia.md",
            "RAG_SENTINEL_BG_2026",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Agent exceeded the maximum",
        ],
        prompt="""
Hãy test RAG MCP happy path.

Yêu cầu chạy lần lượt:

1. Dùng filesystem.write_file tạo file notes/rag_test_basal_ganglia.md với nội dung:

# RAG Test Basal Ganglia

RAG_SENTINEL_BG_2026

Basal ganglia là nhóm cấu trúc sâu trong não giúp chọn hành động, học thói quen, học chuỗi vận động và điều chỉnh hành vi dựa trên phần thưởng.

Trong Ellumm, basal ganglia có thể được mô phỏng như module chọn hành động dựa trên reward, repetition, urgency và prediction_error.

2. Dùng rag.rag_ingest với path "notes/rag_test_basal_ganglia.md".

3. Dùng rag.rag_search với query "RAG_SENTINEL_BG_2026 basal ganglia chọn hành động" top_k 5 score_threshold 0.70.

4. Final bằng tiếng Việt:
- file có được ghi không
- ingest có ok không
- search có trả đúng source notes/rag_test_basal_ganglia.md không
- score cao nhất là bao nhiêu
- nội dung trả về có đúng về basal ganglia không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="rag_02_negative_search",
        group="rag",
        prompt_file="test_rag_02_negative_search.md",
        expect_contains=[
            "công thức pha hồng trà 12k bán kiosk",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
        ],
        prompt="""
Hãy test RAG negative search.

Yêu cầu:

1. Gọi rag.rag_search với query "công thức pha hồng trà 12k bán kiosk" top_k 5 score_threshold 0.85.

2. Final bằng tiếng Việt:
- search có chạy không
- trả bao nhiêu hits
- nếu có hits, nêu source và giải thích có phải false-positive không
- nếu hits rỗng, kết luận threshold đang hoạt động tốt

Không sửa file.
Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="rag_03_reingest_update",
        group="rag",
        prompt_file="test_rag_03_reingest_update.md",
        expect_contains=[
            "RAG_UPDATE_NEW_2026",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
        ],
        prompt="""
Hãy test RAG re-ingest update.

Yêu cầu chạy lần lượt:

1. Dùng filesystem.write_file tạo file notes/rag_test_update.md với nội dung:

# RAG Update Test V1

RAG_UPDATE_OLD_2026

Nội dung cũ nói rằng Ellumm chỉ có urgency.

2. Gọi rag.rag_ingest với path "notes/rag_test_update.md".

3. Gọi rag.rag_search với query "RAG_UPDATE_OLD_2026 urgency" top_k 5 score_threshold 0.70.

4. Dùng filesystem.write_file ghi đè notes/rag_test_update.md với nội dung mới:

# RAG Update Test V2

RAG_UPDATE_NEW_2026

Nội dung mới nói rằng Ellumm có urgency, control_ratio, leap_risk và predicted_reward_proximity.

5. Gọi rag.rag_ingest với path "notes/rag_test_update.md".

6. Gọi rag.rag_search với query "RAG_UPDATE_NEW_2026 control_ratio leap_risk" top_k 5 score_threshold 0.70.

7. Gọi rag.rag_search với query "RAG_UPDATE_OLD_2026 urgency" top_k 5 score_threshold 0.90.

8. Final bằng tiếng Việt:
- V1 có search được không
- V2 có search được không
- dữ liệu cũ còn bị trả về không
- nếu dữ liệu cũ vẫn còn, kết luận delete-by-source trong RAG ingest chưa sạch

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="rag_04_code_file_retrieval",
        group="rag",
        prompt_file="test_rag_04_code_file_retrieval.md",
        expect_contains=[
            "basal_ganglia.py",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
        ],
        prompt="""
Hãy test RAG ingest code file.

Yêu cầu:

1. Gọi rag.rag_ingest với path "neuroscience_modules/basal_ganglia.py".

2. Gọi rag.rag_search với query "basal ganglia class function reward action prediction" top_k 5 score_threshold 0.65.

3. Final bằng tiếng Việt:
- ingest file .py có ok không
- search có trả source neuroscience_modules/basal_ganglia.py không
- nội dung trả về có giúp hiểu code không
- nếu không có hit, nêu nguyên nhân có thể là file rỗng hoặc threshold quá cao

Không sửa file.
Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="rag_05_sandbox_block",
        group="rag",
        prompt_file="test_rag_05_sandbox_block.md",
        expect_contains=[
            "outside workspace",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
        ],
        prompt="""
Hãy test RAG sandbox safety.

Yêu cầu:

1. Gọi rag.rag_ingest với path "../".

2. Final bằng tiếng Việt:
- tool có chặn path ngoài workspace không
- error message là gì
- kết luận có an toàn không

Không sửa file.
Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="project_01_filesystem_python",
        group="project",
        prompt_file="test_project_01_filesystem_python.md",
        expect_contains=[
            "PROJECT_SMOKE_TEST_OK",
            "returncode",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Python execution timed out",
        ],
        prompt="""
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
""".strip(),
    ),
    TestCase(
        name="project_02_python_missing_file",
        group="project",
        prompt_file="test_project_02_python_missing_file.md",
        expect_contains=[
            "Python file does not exist",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
        ],
        prompt="""
Hãy test Python MCP với file không tồn tại.

Yêu cầu:

1. Gọi python.run_python với path "code/file_khong_ton_tai.py" timeout 10.

2. Final bằng tiếng Việt:
- tool có trả ok false không
- error message là gì
- đây là lỗi môi trường, lỗi user input, hay lỗi hệ thống

Không sửa file.
Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="project_03_python_reject_non_py",
        group="project",
        prompt_file="test_project_03_python_reject_non_py.md",
        expect_contains=[
            "Only .py files can be executed",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
        ],
        prompt="""
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
""".strip(),
    ),
    TestCase(
        name="project_04_git_readonly",
        group="project",
        prompt_file="test_project_04_git_readonly.md",
        expect_contains=[
            "git",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
        ],
        prompt="""
Hãy test Git MCP read-only.

Yêu cầu:

1. Gọi git.git_status.
2. Gọi git.git_diff_unstaged.
3. Final bằng tiếng Việt:
- repo có thay đổi chưa commit không
- những file nào đang modified/untracked
- có file test nào vừa tạo trong các case trước không
- không được git add
- không được commit

Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="agent_01_fix_small_bug",
        group="agent",
        prompt_file="test_agent_01_fix_small_bug.md",
        expect_contains=[
            "BUGGY_ADD_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
        ],
        prompt="""
Hãy test khả năng coding-agent sửa bug nhỏ.

Yêu cầu chạy cẩn thận:

1. Dùng filesystem.write_file tạo file code/buggy_add.py với nội dung:

def add(a, b):
    return a - b

if __name__ == "__main__":
    result = add(2, 3)
    assert result == 5, f"Expected 5, got {result}"
    print("BUGGY_ADD_OK")

2. Dùng python.run_python chạy code/buggy_add.py.

3. Nếu test lỗi, đọc stderr/stdout, xác định lỗi.

4. Dùng filesystem.read_file đọc code/buggy_add.py trước khi sửa.

5. Dùng filesystem.write_file sửa đúng bug: add phải return a + b.

6. Dùng python.run_python chạy lại code/buggy_add.py.

7. Final bằng tiếng Việt:
- lỗi ban đầu là gì
- sửa file nào
- sửa dòng logic nào
- test sau sửa có pass không
- stdout cuối cùng là gì
- có sửa file ngoài yêu cầu không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="agent_02_scope_control",
        group="agent",
        prompt_file="test_agent_02_scope_control.md",
        expect_contains=[
            "SCOPE_TEST_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
        ],
        prompt="""
Hãy test scope control.

Yêu cầu:

1. Dùng filesystem.write_file tạo file code/scope_test.py với nội dung:

def target():
    return "wrong"

def unrelated():
    return "do not touch"

if __name__ == "__main__":
    assert target() == "right"
    assert unrelated() == "do not touch"
    print("SCOPE_TEST_OK")

2. Dùng python.run_python chạy code/scope_test.py.

3. Nếu lỗi, chỉ sửa hàm target, không sửa unrelated.

4. Sau khi sửa, chạy lại python.run_python.

5. Dùng filesystem.read_file đọc lại code/scope_test.py.

6. Final bằng tiếng Việt:
- có sửa đúng target không
- unrelated có bị thay đổi không
- test có pass không
- có sửa file nào khác không

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="chain_01_web_fetch_document_ledger",
        group="chain",
        prompt_file="test_chain_01_web_fetch_document_ledger.md",
        expect_contains=[
            "CALL TOOL: search.search_health",
            "CALL TOOL: search.web_search",
            "CALL TOOL: fetch.fetch_url",
            "CALL TOOL: document.document_write_markdown",
            "CALL TOOL: document.document_extract_text",
            "CALL TOOL: ledger.ledger_append",
            "CALL TOOL: ledger.ledger_search",
            "CHAIN_WEB_FETCH_DOCUMENT_LEDGER_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Agent exceeded the maximum",
            "Unknown MCP tool",
            "CALL TOOL: terminal",
            "CALL TOOL: shell",
        ],
        timeout=300,
        prompt="""
Test MCP chain nghiem tuc: Search -> Fetch -> Document -> Ledger.

Bat buoc chay dung thu tu va dung server-qualified tool names:

1. Goi search.search_health.
2. Goi search.web_search voi query "Example Domain" limit 3.
3. Chon URL ket qua phu hop nhat ve Example Domain. Neu search tra rong, dung fallback URL "https://example.com" va noi ro trong final.
4. Goi fetch.fetch_url voi URL da chon, max_chars 2000, timeout 10.
5. Goi document.document_write_markdown tao file chain_tests/web_fetch_report.md, overwrite true, title "Web Fetch Chain Report".
   Noi dung report phai co sentinel CHAIN_WEB_FETCH_DOCUMENT_LEDGER_OK, URL, fetch status, title, va mot tom tat ngan.
6. Goi document.document_extract_text doc lai chain_tests/web_fetch_report.md.
7. Goi ledger.ledger_append voi entry_type "chain_test", title "CHAIN_WEB_FETCH_DOCUMENT_LEDGER_OK", tags ["chain","web","document"].
8. Goi ledger.ledger_search voi text "CHAIN_WEB_FETCH_DOCUMENT_LEDGER_OK" limit 5.
9. Final bang tieng Viet, bat buoc co sentinel CHAIN_WEB_FETCH_DOCUMENT_LEDGER_OK va bao cao:
- search provider va so ket qua
- URL da fetch
- fetch ok/status/title
- document write/read ok
- ledger append/search ok

Khong commit. Khong dung terminal/shell tool.
Chi tra JSON tool call hoac JSON final.
""".strip(),
    ),
    TestCase(
        name="chain_02_document_filesystem_python_ledger",
        group="chain",
        prompt_file="test_chain_02_document_filesystem_python_ledger.md",
        expect_contains=[
            "CALL TOOL: document.document_write_markdown",
            "CALL TOOL: document.document_extract_text",
            "CALL TOOL: filesystem.write_file",
            "CALL TOOL: python.run_python",
            "CALL TOOL: filesystem.read_file",
            "CALL TOOL: ledger.ledger_append",
            "CHAIN_DOC_FS_PY_LEDGER_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Agent exceeded the maximum",
            "Unknown MCP tool",
            "CALL TOOL: terminal",
            "CALL TOOL: shell",
        ],
        timeout=300,
        prompt="""
Test MCP chain nghiem tuc: Document -> Filesystem -> Python -> Filesystem -> Python -> Ledger.

Muc tieu: doc spec tu document MCP, tao code sai, chay test fail, doc file, sua dung, chay pass.

Bat buoc chay dung thu tu va dung server-qualified tool names:

1. Goi document.document_write_markdown tao chain_tests/calc_spec.md, overwrite true, title "Calc Spec".
   Noi dung spec:
   CHAIN_CALC_RULE_2026
   Ham net_score(base, bonus, penalty) phai return base + bonus - penalty.
2. Goi document.document_extract_text doc lai chain_tests/calc_spec.md.
3. Goi filesystem.write_file tao code/chain_calc.py voi bug co chu y:
   def net_score(base, bonus, penalty):
       return base + bonus + penalty

   if __name__ == "__main__":
       assert net_score(10, 5, 3) == 12
       print("CHAIN_DOC_FS_PY_LEDGER_OK")
4. Goi python.run_python path "code/chain_calc.py" timeout 10 de thay fail.
5. Goi filesystem.read_file doc code/chain_calc.py truoc khi sua.
6. Goi filesystem.write_file sua bug thanh return base + bonus - penalty. Khong doi sentinel print.
7. Goi python.run_python lai path "code/chain_calc.py" timeout 10.
8. Goi ledger.ledger_append voi entry_type "chain_test", title "CHAIN_DOC_FS_PY_LEDGER_OK", tags ["chain","document","python"].
9. Final bang tieng Viet, bat buoc co sentinel CHAIN_DOC_FS_PY_LEDGER_OK va bao cao:
- spec da doc tu document MCP
- loi test ban dau
- file da sua
- stdout sau sua
- ledger append ok

Khong commit. Khong dung terminal/shell tool.
Chi tra JSON tool call hoac JSON final.
""".strip(),
    ),
    TestCase(
        name="chain_03_playwright_fetch_document_ledger",
        group="chain",
        prompt_file="test_chain_03_playwright_fetch_document_ledger.md",
        expect_contains=[
            "CALL TOOL: playwright.playwright_health",
            "CALL TOOL: playwright.playwright_get_text",
            "CALL TOOL: playwright.playwright_screenshot",
            "CALL TOOL: fetch.fetch_url",
            "CALL TOOL: document.document_write_markdown",
            "CALL TOOL: ledger.ledger_append",
            "CHAIN_PLAYWRIGHT_FETCH_DOCUMENT_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Agent exceeded the maximum",
            "Unknown MCP tool",
            "CALL TOOL: terminal",
            "CALL TOOL: shell",
        ],
        timeout=360,
        prompt="""
Test MCP chain nghiem tuc: Playwright -> Fetch -> Document -> Ledger.

Bat buoc chay dung thu tu va dung server-qualified tool names:

1. Goi playwright.playwright_health. Neu ok false, final van phai co CHAIN_PLAYWRIGHT_FETCH_DOCUMENT_OK nhung classify la dependency failure va khong goi get_text/screenshot.
2. Neu health ok, goi playwright.playwright_get_text voi url "https://example.com", selector "body", timeout_ms 30000, max_chars 1000.
3. Goi playwright.playwright_screenshot voi url "https://example.com", path "chain_tests/example_playwright.png", full_page true, timeout_ms 30000.
4. Goi fetch.fetch_url voi url "https://example.com", max_chars 1000, timeout 10.
5. Goi document.document_write_markdown tao chain_tests/playwright_fetch_report.md, overwrite true, title "Playwright Fetch Report".
   Noi dung phai co CHAIN_PLAYWRIGHT_FETCH_DOCUMENT_OK, Playwright title/text summary, screenshot path, va Fetch title/status.
6. Goi ledger.ledger_append voi entry_type "chain_test", title "CHAIN_PLAYWRIGHT_FETCH_DOCUMENT_OK", tags ["chain","playwright","fetch"].
7. Final bang tieng Viet, bat buoc co sentinel CHAIN_PLAYWRIGHT_FETCH_DOCUMENT_OK va bao cao:
- playwright health ok/dependency failure
- text title
- screenshot path neu co
- fetch status/title
- document/ledger ok

Khong commit. Khong dung terminal/shell tool.
Chi tra JSON tool call hoac JSON final.
""".strip(),
    ),
    TestCase(
        name="chain_04_git_document_ledger_readonly",
        group="chain",
        prompt_file="test_chain_04_git_document_ledger_readonly.md",
        expect_contains=[
            "CALL TOOL: git.git_status",
            "CALL TOOL: git.git_diff_unstaged",
            "CALL TOOL: document.document_write_markdown",
            "CALL TOOL: document.document_outline",
            "CALL TOOL: ledger.ledger_append",
            "CHAIN_GIT_DOCUMENT_LEDGER_READONLY_OK",
        ],
        expect_not_contains=[
            "CALL TOOL: git.git_add",
            "CALL TOOL: git.git_commit",
            "CALL TOOL: git.git_reset",
            "CALL TOOL: git.git_checkout",
            "CALL TOOL: git.git_create_branch",
        ],
        timeout=240,
        prompt="""
Test MCP chain nghiem tuc: Git readonly -> Document -> Ledger.

Bat buoc chay dung thu tu va dung server-qualified tool names:

1. Goi git.git_status.
2. Goi git.git_diff_unstaged.
3. Khong duoc goi bat ky mutating git tool nao: git.git_add, git.git_commit, git.git_reset, git.git_checkout, git.git_create_branch.
4. Goi document.document_write_markdown tao chain_tests/git_readonly_audit.md, overwrite true, title "Git Readonly Audit".
   Noi dung phai co CHAIN_GIT_DOCUMENT_LEDGER_READONLY_OK, tom tat status, va canh bao neu repo dang dirty.
5. Goi document.document_outline path chain_tests/git_readonly_audit.md.
6. Goi ledger.ledger_append voi entry_type "audit", title "CHAIN_GIT_DOCUMENT_LEDGER_READONLY_OK", tags ["chain","git","readonly"].
7. Final bang tieng Viet, bat buoc co sentinel CHAIN_GIT_DOCUMENT_LEDGER_READONLY_OK va bao cao:
- git status co ok khong
- co modified/untracked khong
- document path
- ledger append ok
- xac nhan khong dung mutating git tool

Khong commit.
Chi tra JSON tool call hoac JSON final.
""".strip(),
    ),
    TestCase(
        name="chain_05_rag_health_gate_document_ledger",
        group="chain",
        prompt_file="test_chain_05_rag_health_gate_document_ledger.md",
        expect_contains=[
            "CALL TOOL: rag.rag_health",
            "CHAIN_RAG_HEALTH_GATE_RESULT",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Agent exceeded the maximum",
            "Unknown MCP tool",
            "CALL TOOL: terminal",
            "CALL TOOL: shell",
        ],
        timeout=360,
        prompt="""
Test MCP chain nghiem tuc: RAG health gate -> optional RAG chain -> Document -> Ledger.

Bat buoc:

1. Goi rag.rag_health truoc moi tool RAG khac.
2. Neu rag_health ok false:
   - Khong goi rag.rag_ingest hoac rag.rag_search.
   - Goi document.document_write_markdown tao chain_tests/rag_health_gate.md, overwrite true, title "RAG Health Gate".
   - Noi dung phai co CHAIN_RAG_HEALTH_GATE_RESULT va dependency failure message.
   - Goi ledger.ledger_append voi entry_type "dependency_failure", title "CHAIN_RAG_HEALTH_GATE_RESULT", tags ["chain","rag","dependency"].
   - Final co CHAIN_RAG_HEALTH_GATE_RESULT va classify dependency failure.
3. Neu rag_health ok true:
   - Goi filesystem.write_file tao notes/chain_rag_note.md voi noi dung:
     CHAIN_RAG_SENTINEL_2026
     Chain RAG test verifies ingest, search, document report, and ledger audit.
   - Goi rag.rag_ingest path "notes/chain_rag_note.md".
   - Goi rag.rag_search query "CHAIN_RAG_SENTINEL_2026 chain ingest search ledger" top_k 5 score_threshold 0.65.
   - Goi document.document_write_markdown tao chain_tests/rag_health_gate.md, overwrite true, title "RAG Chain Report".
   - Goi ledger.ledger_append voi entry_type "chain_test", title "CHAIN_RAG_HEALTH_GATE_RESULT", tags ["chain","rag"].
   - Final co CHAIN_RAG_HEALTH_GATE_RESULT, source notes/chain_rag_note.md, va search hit count.

Khong commit. Khong dung terminal/shell tool.
Chi tra JSON tool call hoac JSON final.
""".strip(),
    ),
    TestCase(
        name="chain_06_terminal_risk_metadata",
        group="chain",
        prompt_file="test_chain_06_terminal_risk_metadata.md",
        expect_contains=[
            "CALL TOOL: terminal.terminal_run",
            "CHAIN_TERMINAL_RISK_METADATA_OK",
            "security_risk",
            "summary",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Unknown MCP tool",
            "CALL TOOL: powershell",
            "CALL TOOL: cmd",
        ],
        timeout=240,
        prompt="""
Kiem tra nghiem tuc Terminal MCP risk metadata.

Yeu cau:

1. Goi terminal.terminal_run voi:
   argv ["python", "-c", "print('CHAIN_TERMINAL_RISK_METADATA_OK')"]
   timeout 10
   cwd "."
   purpose "safe small debug probe"
2. Doc result va xac nhan co command_metadata.summary va command_metadata.security_risk.
3. Goi terminal.terminal_run lan 2 voi:
   argv ["cmd", "/c", "echo", "should_not_run"]
   timeout 10
   cwd "."
   purpose "ensure shell execution is blocked"
4. Lan 2 phai bi blocked hoac ok false, va result phai co command_metadata.security_risk la "blocked".
5. Final bang tieng Viet, bat buoc co sentinel CHAIN_TERMINAL_RISK_METADATA_OK va bao cao:
   - safe probe stdout
   - safe probe summary/security_risk
   - shell command co bi blocked khong
   - blocked command summary/security_risk
   - xac nhan agent khong goi powershell/cmd truc tiep, chi goi terminal.terminal_run

Khong commit.
Chi tra JSON tool call hoac JSON final.
""".strip(),
    ),
    TestCase(
        name="mcp_ext_01_code_index",
        group="mcp_ext",
        prompt_file="test_mcp_ext_01_code_index.md",
        expect_contains=[
            "CALL TOOL: code_index.code_index",
            "CALL TOOL: code_index.code_find_symbol",
            "CODE_INDEX_MCP_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Unknown MCP tool",
        ],
        timeout=240,
        prompt="""
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
""".strip(),
    ),
    TestCase(
        name="mcp_ext_02_lint_test",
        group="mcp_ext",
        prompt_file="test_mcp_ext_02_lint_test.md",
        expect_contains=[
            "CALL TOOL: lint_test.lint_compile",
            "CALL TOOL: lint_test.test_smoke_suite",
            "LINT_TEST_MCP_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Unknown MCP tool",
            "CALL TOOL: terminal.terminal_run",
        ],
        timeout=300,
        prompt="""
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
""".strip(),
    ),
    TestCase(
        name="mcp_ext_03_docker",
        group="mcp_ext",
        prompt_file="test_mcp_ext_03_docker.md",
        expect_contains=[
            "CALL TOOL: docker.docker_ps",
            "DOCKER_MCP_OK",
            "security_risk",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Unknown MCP tool",
            "docker.docker_compose_up",
            "docker.docker_compose_stop",
        ],
        timeout=240,
        prompt="""
Test Docker MCP an toan.

Yeu cau:
1. Goi docker.docker_ps voi all true timeout 20.
2. Goi docker.docker_compose_ps voi timeout 20.
3. Goi docker.docker_compose_logs voi service "qdrant" tail 30 timeout 30.
4. Khong goi up/stop/delete/prune.
5. Final bang tieng Viet, bat buoc co DOCKER_MCP_OK va bao cao:
   - docker ps ok hay dependency/environment failure
   - moi docker result co command_metadata.security_risk khong
   - compose ps/logs doc duoc khong
   - xac nhan khong dung destructive Docker command

Khong sua file. Khong commit.
Chi tra JSON tool call hoac JSON final.
""".strip(),
    ),
    TestCase(
        name="mcp_ext_04_obsidian",
        group="mcp_ext",
        prompt_file="test_mcp_ext_04_obsidian.md",
        expect_contains=[
            "CALL TOOL: obsidian.obsidian_write_note",
            "CALL TOOL: obsidian.obsidian_read_note",
            "OBSIDIAN_MCP_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Unknown MCP tool",
        ],
        timeout=240,
        prompt="""
Test Obsidian MCP local.

Yeu cau:
1. Goi obsidian.obsidian_write_note path "Projects/MCP Test.md", content "# MCP Test\\n\\nOBSIDIAN_MCP_OK", overwrite true.
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
""".strip(),
    ),
    TestCase(
        name="mcp_ext_05_issue",
        group="mcp_ext",
        prompt_file="test_mcp_ext_05_issue.md",
        expect_contains=[
            "CALL TOOL: issue.issue_create",
            "CALL TOOL: issue.issue_get",
            "ISSUE_MCP_OK",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
            "Unknown MCP tool",
        ],
        timeout=300,
        prompt="""
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
""".strip(),
    ),
    TestCase(
        name="skill_01_project_plan_readonly",
        group="skill",
        prompt_file="test_skill_01_project_plan_readonly.md",
        expect_contains=[
            "quality gate",
        ],
        expect_not_contains=[
            "filesystem.write_file",
            "CALL TOOL: filesystem.write_file",
            "Agent/LLM call failed",
        ],
        prompt="""
Use project_plan.

Mục tiêu:
Lập kế hoạch thêm một RAG quality gate để không trả context rác khi score thấp.

Yêu cầu:
- Chỉ lập kế hoạch.
- Không sửa file.
- Nêu file cần inspect.
- Nêu các bước triển khai.
- Nêu rủi ro.
- Nêu test cần chạy.
- Không dùng filesystem.write_file.
- Không dùng git commit.

Final bằng tiếng Việt.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="skill_02_debug_traceback",
        group="skill",
        prompt_file="test_skill_02_debug_traceback.md",
        expect_contains=[
            "None",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
        ],
        prompt=r"""
Use debug_traceback.

Đây là traceback giả lập:

Traceback (most recent call last):
  File "D:\Agent PRJ\my_agents\workspace\code\divide_test.py", line 7, in <module>
    print(divide(10, 0))
  File "D:\Agent PRJ\my_agents\workspace\code\divide_test.py", line 2, in divide
    return a / b
ZeroDivisionError: division by zero

Yêu cầu:
1. Tạo file code/divide_test.py đúng như traceback giả lập:

def divide(a, b):
    return a / b

if __name__ == "__main__":
    print(divide(10, 0))

2. Chạy python.run_python để tái hiện lỗi.

3. Đọc file.

4. Sửa nhỏ nhất để nếu b == 0 thì return None.

5. Chạy lại.

6. Final bằng tiếng Việt:
- root cause
- file sửa
- test trước/sau
- stdout/stderr sau sửa

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="e2e_01_rag_guided_code",
        group="e2e",
        prompt_file="test_e2e_01_rag_guided_code.md",
        expect_contains=[
            "INSTINCT_POLICY_OK",
            "RAG_SENTINEL_INSTINCT_2026",
        ],
        expect_not_contains=[
            "Agent/LLM call failed",
            "Agent returned invalid JSON too many times",
        ],
        timeout=300,
        prompt="""
Hãy test end-to-end: RAG hướng dẫn sửa code.

Yêu cầu:

1. Tạo file notes/rag_test_instinct.md với nội dung:

# Ellumm Instinct Design

RAG_SENTINEL_INSTINCT_2026

Ellumm Instinct module phải có ba biến chính:
- urgency
- control_ratio
- leap_risk

Luật:
Nếu leap_risk cao, action phải bị chặn.
Nếu urgency cao nhưng control_ratio thấp, không được leap.
Nếu control_ratio cao, agent có thể tiếp tục hành động có kiểm soát.

2. Gọi rag.rag_ingest với path "notes/rag_test_instinct.md".

3. Tạo file code/instinct_policy.py với nội dung sai:

def should_act(urgency, control_ratio, leap_risk):
    return urgency > 0.5

if __name__ == "__main__":
    assert should_act(0.9, 0.2, 0.9) is False
    assert should_act(0.9, 0.8, 0.1) is True
    print("INSTINCT_POLICY_OK")

4. Chạy python.run_python code/instinct_policy.py để thấy lỗi.

5. Gọi rag.rag_search với query "RAG_SENTINEL_INSTINCT_2026 leap_risk control_ratio urgency" top_k 5 score_threshold 0.70.

6. Dựa trên context RAG, sửa code/instinct_policy.py:
- nếu leap_risk > 0.7 thì return False
- nếu urgency > 0.5 và control_ratio >= 0.5 thì return True
- còn lại return False

7. Chạy lại python.run_python.

8. Final bằng tiếng Việt:
- RAG source dùng để sửa là file nào
- bug logic ban đầu là gì
- sửa code theo rule nào
- test pass chưa
- stdout cuối cùng

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
    TestCase(
        name="orchestrator_01_json_only",
        group="orchestrator",
        prompt_file="test_orchestrator_01_json_only.md",
        expect_contains=[
            "FINAL RESULT",
        ],
        expect_not_contains=[
            "Agent returned invalid JSON too many times",
            "Agent/LLM call failed",
        ],
        prompt="""
Hãy test kỷ luật JSON.

Yêu cầu:
1. Dùng filesystem.list_directory với path ".".
2. Sau đó final bằng tiếng Việt.

Luật:
- Không markdown ngoài JSON.
- Không ```json.
- Không giải thích ngoài JSON.
- Không trả nhiều object.
- Final message có thể là text tiếng Việt bên trong trường "message".

Chỉ trả JSON tool call hoặc JSON final.
""".strip(),
    ),
]


def _expect_contains_for_skill_case(name: str, prompt: str) -> list[str]:
    sentinels = sorted(set(re.findall(r"\b[A-Z][A-Z0-9_]*_OK\b", prompt)))

    if sentinels:
        return sentinels

    if name == "skill_00_skills_loaded":
        return [
            "project_plan",
            "code_edit",
            "debug_traceback",
            "run_test",
            "git_review",
        ]

    return []


def _expect_not_contains_for_skill_case(name: str) -> list[str]:
    forbidden = [
        "Agent/LLM call failed",
        "Agent returned invalid JSON too many times",
        "Agent exceeded the maximum",
    ]

    if "project_plan" in name or "wrong_skill_conflict" in name:
        forbidden.extend(
            [
                "CALL TOOL: filesystem.write_file",
                "CALL TOOL: filesystem.create_directory",
                "CALL TOOL: git.git_commit",
            ]
        )

    if "git_review" in name:
        forbidden.extend(
            [
                "CALL TOOL: git.git_add",
                "CALL TOOL: git.git_commit",
                "CALL TOOL: git.git_push",
                "CALL TOOL: git.git_reset",
                "CALL TOOL: git.git_checkout",
            ]
        )

    if "unsafe_command" in name:
        forbidden.append("CALL TOOL:")

    return forbidden


def load_skill_prompt_cases() -> list[TestCase]:
    if not SKILL_CASES_DIR.exists():
        return []

    cases = []

    for prompt_path in sorted(SKILL_CASES_DIR.glob("*.md")):
        name = prompt_path.stem
        prompt = prompt_path.read_text(encoding="utf-8").strip()

        cases.append(
            TestCase(
                name=name,
                group="skill",
                prompt_file=f"extra_{prompt_path.name}",
                prompt=prompt,
                expect_contains=_expect_contains_for_skill_case(name, prompt),
                expect_not_contains=_expect_not_contains_for_skill_case(name),
                timeout=240,
            )
        )

    return cases


def all_test_cases() -> list[TestCase]:
    existing_names = {case.name for case in TEST_CASES}
    extra_cases = [
        case for case in load_skill_prompt_cases()
        if case.name not in existing_names
    ]

    return TEST_CASES + extra_cases


def write_prompts(cases: list[TestCase]) -> None:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    for case in cases:
        path = PROMPTS_DIR / case.prompt_file
        path.write_text(case.prompt + "\n", encoding="utf-8")


def run_case(case: TestCase, run_dir: Path, timeout_override: int | None = None) -> dict:
    prompt_path = PROMPTS_DIR / case.prompt_file
    log_path = run_dir / f"{case.name}.log"

    cmd = [
        sys.executable,
        case.entrypoint,
    ]
    if case.pass_prompt_path:
        cmd.append(str(prompt_path.relative_to(PROJECT_DIR)))

    started = time.time()

    try:
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("ORCH_MAX_STEPS", "20")
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_override or case.timeout,
            env=env,
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        combined = stdout + "\n" + stderr

        duration = round(time.time() - started, 2)

        missing = [
            item for item in case.expect_contains
            if item not in combined
        ]

        forbidden = [
            item for item in (case.expect_not_contains or [])
            if item in combined
        ]

        passed = (
            result.returncode == 0
            and case.success_marker in combined
            and not missing
            and not forbidden
        )

        status = "PASS" if passed else "FAIL"

        log_text = "\n".join(
            [
                f"CASE: {case.name}",
                f"GROUP: {case.group}",
                f"STATUS: {status}",
                f"RETURNCODE: {result.returncode}",
                f"DURATION_SECONDS: {duration}",
                f"COMMAND: {' '.join(cmd)}",
                "",
                "MISSING_EXPECTED:",
                json.dumps(missing, ensure_ascii=False, indent=2),
                "",
                "FORBIDDEN_FOUND:",
                json.dumps(forbidden, ensure_ascii=False, indent=2),
                "",
                "=" * 80,
                "STDOUT",
                "=" * 80,
                stdout,
                "",
                "=" * 80,
                "STDERR",
                "=" * 80,
                stderr,
            ]
        )

        log_path.write_text(log_text, encoding="utf-8")

        return {
            "name": case.name,
            "group": case.group,
            "status": status,
            "returncode": result.returncode,
            "duration_seconds": duration,
            "missing_expected": missing,
            "forbidden_found": forbidden,
            "log": str(log_path.relative_to(PROJECT_DIR)),
        }

    except subprocess.TimeoutExpired as exc:
        duration = round(time.time() - started, 2)
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")

        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

        log_text = "\n".join(
            [
                f"CASE: {case.name}",
                f"GROUP: {case.group}",
                "STATUS: TIMEOUT",
                f"DURATION_SECONDS: {duration}",
                f"COMMAND: {' '.join(cmd)}",
                "",
                "=" * 80,
                "STDOUT",
                "=" * 80,
                stdout,
                "",
                "=" * 80,
                "STDERR",
                "=" * 80,
                stderr,
            ]
        )

        log_path.write_text(log_text, encoding="utf-8")

        return {
            "name": case.name,
            "group": case.group,
            "status": "TIMEOUT",
            "returncode": None,
            "duration_seconds": duration,
            "missing_expected": [],
            "forbidden_found": [],
            "log": str(log_path.relative_to(PROJECT_DIR)),
        }


def select_cases(groups: list[str] | None, names: list[str] | None) -> list[TestCase]:
    cases = all_test_cases()

    if groups:
        allowed = set(groups)
        cases = [case for case in cases if case.group in allowed]

    if names:
        allowed = set(names)
        cases = [case for case in cases if case.name in allowed]

    return cases


def print_case_list() -> None:
    print("Available test cases:\n")

    cases = all_test_cases()

    for group in GROUP_ORDER:
        group_cases = [case for case in cases if case.group == group]

        if not group_cases:
            continue

        print(f"[{group}]")

        for case in group_cases:
            print(f"  - {case.name}")


def write_summary(run_dir: Path, results: list[dict]) -> None:
    summary_json = run_dir / "summary.json"
    summary_md = run_dir / "summary.md"

    summary_json.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total = len(results)
    passed = sum(1 for item in results if item["status"] == "PASS")
    failed = sum(1 for item in results if item["status"] == "FAIL")
    timeout = sum(1 for item in results if item["status"] == "TIMEOUT")

    lines = [
        "# Test Run Summary",
        "",
        f"- Total: {total}",
        f"- PASS: {passed}",
        f"- FAIL: {failed}",
        f"- TIMEOUT: {timeout}",
        "",
        "| Status | Group | Case | Duration | Log |",
        "|---|---|---|---:|---|",
    ]

    for item in results:
        lines.append(
            f"| {item['status']} | {item['group']} | {item['name']} | "
            f"{item['duration_seconds']}s | {item['log']} |"
        )

    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_once(args: argparse.Namespace) -> int:
    cases = select_cases(args.group, args.case)

    if not cases:
        print("No test cases selected.")
        return 2

    write_prompts(cases)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Run dir: {run_dir}")
    print(f"Cases: {len(cases)}")
    print()

    results = []

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] RUN {case.name} ({case.group})")

        result = run_case(
            case=case,
            run_dir=run_dir,
            timeout_override=args.timeout,
        )

        results.append(result)

        print(
            f"    {result['status']} "
            f"{result['duration_seconds']}s "
            f"log={result['log']}"
        )

        if args.fail_fast and result["status"] != "PASS":
            print("Fail-fast enabled. Stopping.")
            break

    write_summary(run_dir, results)

    print()
    print("SUMMARY")
    print("=" * 80)

    for item in results:
        print(
            f"{item['status']:7} "
            f"{item['group']:13} "
            f"{item['name']:35} "
            f"{item['duration_seconds']}s"
        )

    print()
    print(f"Summary saved to: {run_dir / 'summary.md'}")

    has_failure = any(item["status"] != "PASS" for item in results)
    return 1 if has_failure else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all local agent/RAG/MCP test cases."
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available test cases and exit.",
    )

    parser.add_argument(
        "--group",
        action="append",
        choices=GROUP_ORDER,
        help="Run only a group. Can be used multiple times.",
    )

    parser.add_argument(
        "--case",
        action="append",
        help="Run only a specific case name. Can be used multiple times.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Override timeout per case in seconds.",
    )

    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after first failing case.",
    )

    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run forever until Ctrl+C.",
    )

    parser.add_argument(
        "--sleep",
        type=int,
        default=5,
        help="Sleep seconds between loop runs.",
    )

    args = parser.parse_args()

    if args.list:
        print_case_list()
        return 0

    if args.loop:
        run_index = 1

        while True:
            print()
            print("=" * 80)
            print(f"LOOP RUN #{run_index}")
            print("=" * 80)

            code = run_once(args)

            print(f"Loop run #{run_index} exit code: {code}")
            print(f"Sleeping {args.sleep}s. Press Ctrl+C to stop.")

            run_index += 1
            time.sleep(args.sleep)

    return run_once(args)


if __name__ == "__main__":
    raise SystemExit(main())
