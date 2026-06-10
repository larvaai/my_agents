# ADR-0004: Use Local LLM Through LM Studio-compatible API

## Status

Accepted

## Context

Project ưu tiên local-first để thử nghiệm coding-agent với model chạy trên máy, không phụ thuộc API cloud mặc định.

## Decision

`llm.py` dùng OpenAI Python client với base URL OpenAI-compatible. Mặc định:

```text
http://localhost:1234/v1
api_key=lm-studio
```

## Consequences

Ưu điểm:

- Dễ chạy với LM Studio.
- Có thể đổi sang OpenAI-compatible endpoint khác bằng env.
- Không phải đổi agent/orchestrator.

Nhược điểm:

- Chất lượng phụ thuộc model local.
- Context/token/speed phụ thuộc máy.
- Cần docs debug khi model không tuân JSON.

## Env Overrides

```powershell
$env:LLM_BASE_URL="http://localhost:1234/v1"
$env:LLM_API_KEY="lm-studio"
$env:LLM_MODEL="model-name"
```

