Hãy test RAG MCP mới.

Yêu cầu chạy lần lượt:

1. Gọi rag.rag_ingest với path "notes".
2. Gọi rag.rag_search với query "basal ganglia là gì?" và top_k = 5.
3. Đọc tool result.
4. Final bằng tiếng Việt, tóm tắt:
   - RAG MCP có chạy không
   - ingest được bao nhiêu file
   - search trả bao nhiêu hit
   - nguồn liên quan nhất là file nào
   - nội dung tìm được có đủ để trả lời câu hỏi không

Không sửa file.
Không commit.
Chỉ trả JSON tool call hoặc JSON final đúng system prompt.