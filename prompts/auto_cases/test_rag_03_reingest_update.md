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
