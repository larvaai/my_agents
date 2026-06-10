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
