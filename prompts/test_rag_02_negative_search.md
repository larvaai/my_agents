Hãy test RAG negative search.

Yêu cầu:

1. Gọi rag.rag_search với query "công thức pha hồng trà 12k bán kiosk" top_k 5 score_threshold 0.85.

2. Final bằng tiếng Việt:
- search có chạy không
- trả bao nhiêu hits
- nếu có hits, nêu source và giải thích có phải false-positive không
- nếu hits rỗng, kết luận threshold đang hoạt động tốt

Không sửa file.
Không commit.
Chỉ trả JSON tool call hoặc JSON final.