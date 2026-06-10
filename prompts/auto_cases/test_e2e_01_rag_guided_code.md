Hãy test end-to-end: RAG hướng dẫn sửa code.

Yêu cầu:

1. Tạo file notes/rag_test_instinct.md với nội dung:

# Ellumm Instinct Design

RAG_SENTINEL_INSTINCT_2026

Ellumm Instinct module phải có ba biến chính:
- urgency
- control_ratio
- leap_risk

Luật:
Nếu leap_risk cao, action phải bị chặn.
Nếu urgency cao nhưng control_ratio thấp, không được leap.
Nếu control_ratio cao, agent có thể tiếp tục hành động có kiểm soát.

2. Gọi rag.rag_ingest với path "notes/rag_test_instinct.md".

3. Tạo file code/instinct_policy.py với nội dung sai:

def should_act(urgency, control_ratio, leap_risk):
    return urgency > 0.5

if __name__ == "__main__":
    assert should_act(0.9, 0.2, 0.9) is False
    assert should_act(0.9, 0.8, 0.1) is True
    print("INSTINCT_POLICY_OK")

4. Chạy python.run_python code/instinct_policy.py để thấy lỗi.

5. Gọi rag.rag_search với query "RAG_SENTINEL_INSTINCT_2026 leap_risk control_ratio urgency" top_k 5 score_threshold 0.70.

6. Dựa trên context RAG, sửa code/instinct_policy.py:
- nếu leap_risk > 0.7 thì return False
- nếu urgency > 0.5 và control_ratio >= 0.5 thì return True
- còn lại return False

7. Chạy lại python.run_python.

8. Final bằng tiếng Việt:
- RAG source dùng để sửa là file nào
- bug logic ban đầu là gì
- sửa code theo rule nào
- test pass chưa
- stdout cuối cùng

Không commit.
Chỉ trả JSON tool call hoặc JSON final.
