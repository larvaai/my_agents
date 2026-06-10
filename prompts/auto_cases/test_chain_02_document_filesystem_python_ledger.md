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
