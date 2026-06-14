# Run File Map

Muc tieu cua cay docs nay: giai thich toan bo file lien quan de chay duoc
`self_eval_qa_lab`, bao gom file nam trong mini repo va file nam ngoai mini repo
nhung van la dependency runtime.

Mini repo chay theo 2 duong:

```text
python main.py lab self_eval_qa_lab ...
  -> root main.py
  -> tools/mini_repo_registry.py
  -> experiments/self_eval_qa_lab/main.py

python experiments/self_eval_qa_lab/main.py ...
  -> experiments/self_eval_qa_lab/main.py
```

Dataset runner chay theo registry:

```text
python main.py lab self_eval_qa_lab dataset ...
  -> root main.py
  -> tools/mini_repo_registry.py
  -> experiments/self_eval_qa_lab/dataset_runner.py
  -> experiments/self_eval_qa_lab/dataset_loader.py
  -> experiments/self_eval_qa_lab/main.py
```

## Read Order

- `00_NEW_CONTRIBUTOR_GUIDE.md`: ban de hieu cho nguoi moi, giai thich system prompt, user prompt, context, flow bang vi du.
- `01_RUN_ENTRYPOINTS.md`: lenh chay, entrypoint, registry, CLI flags.
- `02_INTERNAL_SOURCE_FILES.md`: tat ca file source/config/data nam trong mini repo.
- `03_AGENT_PROMPTS_AND_CONTRACTS.md`: agents, lenses, rubrics, contracts output.
- `04_EXTERNAL_PROJECT_FILES.md`: file ngoai mini repo nhung can de chay.
- `05_RUNTIME_DATA_OUTPUTS_AND_TESTS.md`: output `var/`, dataset cache, ledger, tests.
- `06_DETAILED_PROMPT_FLOW.md`: flow thuc te, tung model call, va file/folder anh huong len system prompt.

## Quick Commands

```powershell
python main.py lab list
python main.py lab self_eval_qa_lab --mock "JSON agent co nen temp=0 khong?"
python main.py lab self_eval_qa_lab dataset --mock --limit 20 --subsets logiqa --review-every 20
python -m unittest tests.test_self_eval_qa_lab tests.test_self_eval_qa_lab_dataset tests.test_mini_repo_registry
```

## Boundary

Docs in this folder describe runtime files. They do not change runtime behavior.
The lab logs public rationales, public reasoning summaries, prompts, handoffs,
and raw emitted outputs. It does not claim to expose hidden model internals that
were not emitted by the model.
