# ADR-0003: Use JSON-only Agent Protocol

## Status

Accepted

## Context

Local LLM dễ trả markdown, giải thích chen vào tool call, hoặc bịa format. Orchestrator cần output parse được để gọi tool an toàn.

## Decision

Agent chỉ được trả một JSON object:

- `{"action":"tool", ...}`
- `{"action":"final", ...}`

Không markdown, không text ngoài JSON.

## Consequences

Ưu điểm:

- Parse deterministic.
- Tool loop đơn giản.
- Dễ test bằng prompt cases.
- Dễ log và audit.

Nhược điểm:

- Prompt phải rất nghiêm.
- Model yếu có thể fail JSON.
- Người đọc log mất phần giải thích tự nhiên, nên cần field `plan` ngắn.

## Enforcement

`orchestrator.py` parse JSON, retry khi lỗi, và fail nếu model trả JSON sai quá nhiều lần.

