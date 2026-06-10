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