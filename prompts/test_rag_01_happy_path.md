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