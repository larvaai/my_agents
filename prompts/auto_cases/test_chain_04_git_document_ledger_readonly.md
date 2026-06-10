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
