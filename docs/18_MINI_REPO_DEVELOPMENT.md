# Mini Repo Development

Tài liệu này là guide riêng cho việc phát triển nhiều mini repo/lab trong `my_agents`.

Mini repo là nơi thử ý tưởng nhỏ, đo được, có runner riêng, nhưng vẫn chạy được qua entrypoint chung:

```powershell
python main.py lab <mini-repo> [command] [args...]
```

Mục tiêu là để thử nhanh nhiều hướng agent/prompt/orchestration mà không làm core runtime phình ra.

## Vì Sao Cần Mini Repo?

Core project có nhiều phần nghiêm túc: Agent Kernel, MCP tools, JsonGate, orchestrator, safety, RAG, tests. Nếu mọi ý tưởng đều nhét thẳng vào core, repo sẽ nhanh rối và khó biết thay đổi nào thật sự có giá trị.

Mini repo giúp:

- thử một ý tưởng độc lập
- chạy mock/dry-run trước khi gọi LLM thật
- lưu output riêng để so sánh
- bỏ đi dễ nếu ý tưởng không hiệu quả
- nâng cấp lên core sau khi có bằng chứng

Nguyên tắc chính:

```text
Mini repo trước. Core sau.
Đo được trước. Tích hợp sâu sau.
Lens/prompt trước. Agent phức tạp sau.
```

## Khi Nào Nên Tạo Mini Repo?

Nên tạo mini repo khi ý tưởng:

- là một luồng agent mới chưa chắc đúng
- cần so sánh nhiều prompt, lens, rubric, hoặc strategy
- có output dạng artifact/ledger/transcript riêng
- có thể chạy bằng một CLI độc lập
- có thể validate bằng mock/smoke test
- chưa cần trở thành feature chính của `core/` hoặc `orchestration/`

Ví dụ phù hợp:

- `business_prompt_lab`: lab phân tích business và no-code agent room
- `self_eval_qa_lab`: lab so sánh simple answer, lens answer, baseline answer, evaluator, flow observer
- `prompt_rubric_lab`: lab đo chất lượng rubric/evaluator
- `agent_flow_lab`: lab kiểm tra agent nào hữu ích, agent nào thừa

Không nên tạo mini repo nếu:

- chỉ là một helper dùng chung rõ ràng, nên đặt vào `tools/`
- là MCP capability thật, nên đi qua `features/` + `mcp_servers/`
- là role agent chính thức, nên đi qua `agents/` + `config/roles/`
- là sửa nhỏ trong runner hiện có

## Contract Bắt Buộc

Mỗi mini repo nên tuân theo contract này:

- Có thư mục riêng: `business_prompt_lab/` hoặc `experiments/<lab_name>/`.
- Có ít nhất một runner độc lập, ví dụ `main.py`, `run.py`, hoặc `agent_room.py`.
- Runner nhận CLI args bằng `argparse`.
- Runner có `--mock` hoặc `--dry-run` nếu có thể, để test không cần LLM.
- Runner ghi output runtime vào `var/<lab_name>/...`.
- Runner dùng `llm.py` nếu cần gọi model, không tự tạo client rời rạc.
- Runner không tự sửa core repo, prompt chính, skills, hoặc registry nếu chưa có approval rõ.
- Runner được đăng ký trong `tools/mini_repo_registry.py`.
- Có README riêng trong mini repo.
- Có smoke/unit test nếu lab là surface được hỗ trợ lâu dài.

## Layout Chuẩn

Layout tối thiểu:

```text
<mini_repo>/
  README.md
  main.py hoặc run.py
  prompts/
  cases/ hoặc questions/
```

Layout khuyến nghị cho lab nghiêm túc:

```text
<mini_repo>/
  README.md
  DESIGN.md
  main.py
  config.json hoặc config.yaml
  prompts/
    classifier.md
    generator.md
    evaluator.md
  lenses/
    architecture.md
    critic.md
    practical.md
  rubrics/
    answer_quality.yaml
    flow_quality.yaml
  cases/
    sample_01.json
  questions/
    sample_question.md
  tests/
    sample_questions.jsonl
```

Runtime output không nằm trong mini repo source, mà nằm dưới `var/`:

```text
var/<mini_repo>/<timestamp>/
  final.md
  transcript.md
  transcript.json
  summary.md
  summary.json
  outputs/
  inputs/
```

## Chạy Qua `main.py`

List mini repo đã đăng ký:

```powershell
python main.py lab list
```

Chạy default command của một lab:

```powershell
python main.py lab business_prompt_lab --mock "question"
```

Chọn command bằng positional arg:

```powershell
python main.py lab business_prompt_lab benchmark --list
```

Chọn command bằng colon syntax:

```powershell
python main.py lab business_prompt_lab:agent-room --dry-run "question"
```

Aliases hiện có:

```powershell
python main.py lab business --mock "question"
python main.py lab bpl room --dry-run "question"
```

Cách chạy cũ của core vẫn giữ nguyên:

```powershell
python main.py
python main.py prompts/test_mcp_prompt.md
```

## Đăng Ký Mini Repo

Registry nằm ở:

```text
tools/mini_repo_registry.py
```

Thêm một `MiniRepo(...)` entry:

```python
MiniRepo(
    id="self_eval_qa_lab",
    root=PROJECT_DIR / "experiments" / "self_eval_qa_lab",
    description="Self-evaluating answer flow lab.",
    default_command="run",
    aliases=("self-eval",),
    commands=(
        MiniRepoCommand(
            id="run",
            script=PROJECT_DIR / "experiments" / "self_eval_qa_lab" / "main.py",
            description="Run one self-evaluation flow.",
            aliases=("eval",),
        ),
    ),
)
```

Rules:

- `id` dùng `snake_case`, ổn định, không đổi tùy hứng.
- `aliases` ngắn, tiện gõ, nhưng không thay thế `id` chính.
- `default_command` là command người dùng sẽ chạy nhiều nhất.
- Mỗi command trỏ tới script thật có thể chạy độc lập.
- Nếu mini repo còn thử nghiệm cá nhân, chưa cần đăng ký cho tới khi có runner ổn.

## CLI Design

CLI của lab nên có các flag này khi phù hợp:

| Flag | Ý nghĩa |
|---|---|
| `--mock` | Chạy flow giả lập deterministic, không gọi LLM |
| `--dry-run` | In plan/roster/config, không gọi LLM |
| `--list` | Liệt kê prompt/case/config có sẵn |
| `--question-file` hoặc `--task-file` | Đọc input từ file |
| `--out-dir` | Override thư mục output |
| `--model` | Override model từ `llm.py` |
| `--temperature` | Điều chỉnh sampling |
| `--runs` | Lặp nhiều lần để đo độ ổn định |

CLI nên có output rõ:

```text
Run directory: D:\Agent PRJ\my_agents\var\<lab>\<timestamp>
Summary: ...
Transcript: ...
```

## LLM Usage

Nếu cần gọi model, ưu tiên import từ `llm.py`:

```python
from llm import MODEL, call_llm
```

Không tạo nhiều client riêng nếu không có lý do mạnh. Như vậy lab dùng chung:

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
LLM_TIMEOUT
LLM_MAX_TOKENS
```

Lab nên luôn có đường chạy không cần LLM:

- `--dry-run` để kiểm tra routing/config
- `--mock` để kiểm tra transcript/output shape
- unit test cho parser/evaluator/registry

## Output Và Ledger

Mỗi run nên lưu đủ để debug sau này:

```text
question/input
config
selected prompt/lens/agent
intermediate outputs
final answer
evaluation
warnings
run metadata
```

Tên file khuyến nghị:

```text
final.md
transcript.md
transcript.json
summary.md
summary.json
ledger.jsonl
```

Nếu lab có nhiều run, dùng JSONL append-only:

```text
var/<lab>/ledger/runs.jsonl
var/<lab>/ledger/evaluations.jsonl
var/<lab>/ledger/flow_observations.jsonl
```

Không ghi output runtime vào source folder trừ fixtures nhỏ.

## Test Strategy

Mỗi mini repo nên có ít nhất một trong các loại test:

- parser/schema unit test
- registry test
- `--dry-run` smoke
- `--mock` smoke
- evaluator/rubric deterministic test
- golden fixture test cho output shape

Lệnh chung:

```powershell
python -m unittest discover -s tests
python -m py_compile main.py tools/mini_repo_registry.py <mini_repo>/<runner>.py
```

Nếu lab được hỗ trợ chính thức, thêm test vào:

```text
tests/test_mini_repo_registry.py
```

Và nếu muốn compile toàn lab trong dev checks, thêm folder vào `SOURCE_DIRS` trong:

```text
run_dev_checks.py
```

## Development Lifecycle

Một mini repo nên đi qua các phase:

1. **Idea**
   Viết README/DESIGN ngắn: lab đo gì, vì sao đáng thử, output mong muốn là gì.

2. **Mock Runner**
   Tạo CLI chạy `--mock` hoặc `--dry-run`. Chưa gọi LLM.

3. **Real LLM Runner**
   Dùng `llm.py`, lưu transcript và summary.

4. **Evaluation**
   Thêm rubric/evaluator đơn giản, hoặc ít nhất có summary có thể so sánh.

5. **Ledger**
   Lưu run đủ để đọc lại sau 30 đến 50 câu hỏi.

6. **Decision**
   Giữ, bỏ, hoặc nâng cấp thành core feature.

7. **Graduation**
   Nếu lab chứng minh giá trị, chuyển phần ổn định vào `agents/`, `orchestration/`, `features/`, hoặc `tools/`.

## Graduation Rules

Chỉ đưa một ý tưởng từ mini repo vào core khi:

- chạy ổn trên nhiều case, không chỉ một demo
- có test deterministic
- có output tốt hơn baseline hoặc đơn giản hơn rõ ràng
- có contract input/output ổn định
- không làm core phụ thuộc vào prompt/lab quá đặc thù
- tài liệu đã nêu rõ vì sao giữ

Nếu mini repo không còn giá trị:

- giữ lại như archive nếu có dữ liệu hữu ích
- hoặc đánh dấu deprecated trong README
- không để runner hỏng nằm trong registry chính

## Pattern Cho Self-Eval QA Lab

Với ý tưởng `self_eval_qa_lab`, MVP nên gọn:

```text
Question
  -> Question Classifier
  -> Simple Answer
  -> Lens-Based Answer
  -> Optional External Baseline
  -> Blind Evaluator
  -> Error Analyzer
  -> Flow Observer
  -> Ledger
```

Điểm quan trọng:

- luôn có simple answer baseline
- evaluator chấm answer quality
- flow observer chấm process quality
- không tự update skill/lens trong phase đầu
- không thêm nhiều specialist agent nếu lens chưa chứng minh giá trị

Flow Observer nên trả lời:

- câu hỏi này có đáng dùng multi-agent/lens không?
- bước nào thừa?
- bước nào thiếu?
- routing có hợp lý không?
- lần sau nên dùng flow nào?

## Anti-Patterns

Tránh các lỗi này:

- tạo nhiều agent vì nghe hay, nhưng không đo được tác dụng
- cho evaluator biết answer nào là của hệ mình khi cần blind eval
- tự sửa skill/prompt chính sau một lần thua baseline
- ghi artifact runtime vào source folder
- để lab import sâu vào orchestrator/core rồi khó tách
- không có mock/dry-run nên test nào cũng cần LLM
- không lưu transcript nên không debug được vì sao output tệ
- registry trỏ tới script không còn tồn tại

## Checklist Tạo Mini Repo Mới

Trước khi bắt đầu:

- [ ] Lab trả lời câu hỏi đo được nào?
- [ ] Có cần mini repo không, hay chỉ là helper nhỏ?
- [ ] Output cuối là gì: answer, score, transcript, ledger, proposal?

Khi scaffold:

- [ ] Tạo folder lab.
- [ ] Tạo `README.md`.
- [ ] Tạo runner có `argparse`.
- [ ] Thêm `--mock` hoặc `--dry-run`.
- [ ] Ghi output vào `var/<lab>/...`.
- [ ] Dùng `llm.py` nếu gọi model.

Khi tích hợp:

- [ ] Đăng ký trong `tools/mini_repo_registry.py`.
- [ ] Chạy `python main.py lab list`.
- [ ] Chạy default command qua `main.py`.
- [ ] Thêm hoặc cập nhật test registry.
- [ ] Cập nhật docs nếu lab là surface chính thức.

Khi ổn định:

- [ ] Có smoke deterministic.
- [ ] Có output mẫu.
- [ ] Có ledger hoặc summary đọc lại được.
- [ ] Có quyết định giữ/bỏ/nâng cấp.

## Tài Liệu Liên Quan

- `tools/mini_repo_registry.py`
- `docs/workflows/add-mini-repo-lab.md`
- `business_prompt_lab/README.md`
- `business_prompt_lab/NO_CODE_AGENT_FLOW.md`
- `experiments/self_eval_qa_lab/README.md`
- `tests/test_mini_repo_registry.py`
