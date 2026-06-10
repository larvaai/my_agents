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
