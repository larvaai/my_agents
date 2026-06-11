# Repo Understanding

## Repo Này Là Gì?

`my_agents` là một local coding-agent lab/framework. Nó không phải chatbot
thường, không phải UI app, và cũng không chỉ là một script gọi LLM.

Nó là một hệ thống thử nghiệm để biến yêu cầu của user thành một vòng làm việc:

```text
nhận prompt
  -> gọi LLM
  -> ép LLM trả JSON action
  -> validate JSON và tool args
  -> gọi tool an toàn qua MCP/kernel
  -> đưa kết quả tool về LLM
  -> sửa code hoặc chạy kiểm thử
  -> chỉ final khi có evidence hoặc blocker rõ
```

## Vấn Đề Repo Đang Giải Quyết

Khi tự xây coding-agent, các lỗi thường gặp là:

- LLM trả markdown hoặc text thay vì JSON máy đọc được.
- Agent gọi sai tool, thiếu args, hoặc gọi tool không tồn tại.
- Agent sửa file bằng terminal hoặc shell không audit được.
- Agent nói "xong" nhưng chưa chạy test.
- Agent retry mù khi tool fail.
- Prompt dài chứa BRD/PRD/domain logic làm JSON bị vỡ.
- Multi-agent trở thành nhiều vai nói chuyện tự do, không có contract.
- Không có log đủ tốt để debug tại sao agent làm vậy.

Repo này xử lý các vấn đề đó bằng:

- JsonGate cho output contract.
- Agent Kernel và CapabilityResult envelope.
- MCP tool layer có schema và policy.
- Workspace sandbox.
- File Editor MCP thay vì terminal edit.
- Lint/Test/Python MCP cho validation.
- Event logs và inspect CLI.
- Role boundaries: Code, Test, Review, Ledger, Final.
- Software Factory artifact protocol cho phân tích dài.

## Trạng Thái Hiện Tại Của Repo

Repo đã vượt qua mức single-agent cơ bản và đang ở trạng thái "nhiều runtime
song song":

| Runtime | File chính | Ý nghĩa |
|---|---|---|
| Single-agent legacy | `main.py`, `orchestrator.py` | ReAct loop cũ, vẫn hữu ích và có finish gate |
| Agent Kernel | `core/`, `features/` | Boundary mới cho capability/tool |
| MCP tools | `features/mcp_tools/`, `mcp_servers/` | Tool runtime, schema, policy, sandbox |
| JsonGate | `output_gate/` | Parse, repair, validate, dry-run safety |
| Role agents | `agents/base_agent.py`, `agents/role_agents.py` | LLM role prompt và tool allowlist |
| LangGraph path | `main_langgraph.py`, `orchestration/langgraph_orchestrator.py` | Multi-agent state machine thực tế |
| Company v0.5 | `orchestration/company_orchestrator.py` | Deterministic department contract smoke |
| Software Factory v0.7 | `orchestration/software_factory_orchestrator.py` | Product/spec artifacts trước khi code |
| Global Supervisor | `orchestration/global_supervisor.py` | Router tổng quát cho knowledge/research/code/factory |
| Test harness | `run_all_cases.py`, `run_dev_checks.py` | Regression suite cho capability và agent behavior |

## Điều Quan Trọng Cần Hiểu

Repo có nhiều lớp đang cùng tồn tại vì đây là quá trình tiến hóa:

1. Ban đầu là single-agent JSON loop.
2. Sau đó thêm MCP tools và sandbox.
3. Sau đó thêm JsonGate để kiểm output LLM.
4. Sau đó tách Agent Kernel để core không phụ thuộc trực tiếp MCP.
5. Sau đó thêm role agents và LangGraph orchestration.
6. Sau đó thêm Company Agents để đóng contract phòng ban.
7. Sau đó thêm Software Factory để xử lý prompt business/product dài.
8. Sau đó thêm Global Supervisor để route request ngoài coding.

Khi rebuild repo mới, không nên copy ngay toàn bộ. Nên build lại theo tầng,
mỗi tầng có contract và smoke riêng.

## Ý Nghĩa Sản Phẩm

Sản phẩm mà repo đang hướng tới là:

> Một local agent operating system nhỏ cho coding và product-to-code: có thể
> hiểu yêu cầu, phân loại task, sinh spec khi cần, sửa code an toàn, chạy test,
> review, ghi memory/audit và trả final có evidence.

Định vị thực tế:

- Local-first.
- CLI-first.
- LM Studio/OpenAI-compatible.
- Python-first.
- MCP-first.
- Test/evidence-first.
- Không ưu tiên UI trước khi runtime ổn định.

## Những Gì Chưa Hoàn Thiện

Repo vẫn là lab, chưa phải platform production:

- MCP stdio hiện start server theo call, dễ debug nhưng chậm.
- Một số docs/prompt cũ bị lỗi encoding.
- Lens phần lớn là spec/prompt hoặc deterministic, chưa phải bounded sub-agent đầy đủ.
- Global Supervisor đang deterministic và side-effect-light.
- Agent Factory mới là placeholder.
- UI event viewer chưa có.
- RAG chưa có reranker/source line ranges.
- Software Factory tạo spec rất tốt nhưng không tự implement code, phải handoff.

## Kết Luận

Muốn hiểu repo này, hãy xem nó như một cây tiến hóa:

```text
Coding-agent loop
  -> Tool safety
  -> Validation discipline
  -> Role ownership
  -> Artifact-first product planning
  -> General supervisor routing
```

Bản rebuild nên giữ tinh thần đó, nhưng triển khai tuần tự hơn để bạn kiểm soát
từng tầng.

