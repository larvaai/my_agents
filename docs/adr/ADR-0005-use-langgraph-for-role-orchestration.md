# ADR-0005: Use LangGraph For Role Orchestration

## Status

Accepted

## Context

Project đã có MCP tools, BaseAgent, và role registry. Orchestrator cũ là một loop tuyến tính tốt cho single-agent, nhưng khó biểu diễn pipeline nhiều vai như Research, Planner, Architect, Code, Test, Review, Ledger, Final.

LangGraph cung cấp graph orchestration với shared state, node, edge, conditional routing, và khả năng mở rộng về persistence/human-in-the-loop sau này.

## Decision

Thêm LangGraph như orchestration layer riêng:

```text
main_langgraph.py
  -> orchestration/langgraph_orchestrator.py
  -> Research/Planner/Architect/Code/Test/Review/Ledger/Final nodes
  -> tool node
  -> MCP servers giữ nguyên
```

Không thay MCP. Không xóa `orchestrator.py` cũ.

Graph implementation phải giữ các guard sau:

- Tool execution vẫn đi qua MCP client và role allowlist.
- Tool result lớn phải được compact trước khi quay lại LLM.
- Invalid JSON có retry cap theo role, sau đó handoff hoặc blocker rõ ràng.
- Final không được tự suy diễn pass; coding/test task cần validation thật trong `tests_run`.
- Orchestrator được phép rescue các prompt tạo file đơn giản khi path và content đã rõ trong user task.

## Consequences

Pros:

- Tách role pipeline rõ.
- Shared state explicit thay vì chỉ message history.
- Có conditional routing qua graph.
- Sẵn đường nâng cấp checkpoint/persistence.
- Ít hallucinate completion hơn vì Final bị kiểm bởi state thật.

Cons:

- Thêm dependency `langgraph`.
- Multi-role LLM run có thể chậm hơn single-agent.
- Cần smoke test riêng để bắt lỗi graph/API.
- Có thêm một lớp policy/router cần test khi đổi role prompt.

## Follow-up

- Thêm checkpoint khi cần resume/human-in-the-loop.
- Thêm handoff protocol chặt hơn giữa roles.
- Tích hợp Ledger/Issue vào state summary thay vì đưa toàn bộ history vào prompt.
