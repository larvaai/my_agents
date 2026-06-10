# ADR-0001: Use MCP Stdio For Tool Integration

## Status

Accepted

## Context

Agent cần gọi nhiều nhóm tool: filesystem, git, Python, RAG, browser, document, Docker, issue tracker. Nếu mỗi tool là Python function tự do, rất khó audit, sandbox, và mở rộng.

## Decision

Dùng MCP servers qua stdio làm interface chính cho tools.

Tool flow:

```text
agent JSON -> mcp_client -> stdio MCP server -> normalized result
```

## Consequences

Ưu điểm:

- Tách process rõ.
- Dễ thêm server mới.
- Có thể sandbox theo server.
- Tool protocol gần chuẩn hệ sinh thái MCP.

Nhược điểm:

- Mỗi tool call hiện khởi động process mới, có overhead.
- Debug cần xem stderr/log MCP.
- Schema phải được sync giữa config, prompt và docs.

## Follow-up

- Xem xét MCP process pooling nếu overhead thành bottleneck.
- Tiếp tục thêm schema cho local/custom tools quan trọng.

