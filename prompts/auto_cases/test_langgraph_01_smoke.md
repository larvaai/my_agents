Hãy test LangGraph orchestrator.

Yêu cầu:
1. Research/Planner/Architect chỉ lập hướng đi ngắn, không sửa file.
2. Code Agent tạo file code/langgraph_smoke.py với nội dung:
print("LANGGRAPH_SMOKE_OK")
3. Test Agent chạy validation phù hợp để stdout có LANGGRAPH_SMOKE_OK.
4. Review Agent kiểm tra ngắn.
5. Ledger Agent ghi một ghi chú ngắn nếu phù hợp.
6. Final bằng tiếng Việt, bắt buộc có:
   - LANGGRAPH_SMOKE_OK
   - file đã tạo
   - test đã chạy
   - review đã approve hay chưa

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
