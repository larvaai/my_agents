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
