# Git MCP

## Purpose

Git MCP dùng để audit repo: status, diff, log, show. Mutating tools bị policy chặn mặc định.

## Server

- Server name: `git`
- Package: `mcp_server_git`
- Repository: project root
- Config: `features/mcp_tools/config.py`

## Read-only Tools

- `git.git_status`
- `git.git_diff_unstaged`
- `git.git_diff_staged`
- `git.git_diff`
- `git.git_log`
- `git.git_show`
- `git.git_branch`

## Mutating Tools

Các tool sau bị hard-block trừ khi `AGENT_ALLOW_GIT_MUTATIONS=1`:

- `git.git_add`
- `git.git_commit`
- `git.git_reset`
- `git.git_checkout`
- `git.git_create_branch`

## Safety Rule

Agent không được commit/push/reset/checkout trừ khi user yêu cầu rõ. Review diff thì dùng skill `git-review`.

## Test

```powershell
python run_all_cases.py --case chain_04_git_document_ledger_readonly --fail-fast
```
