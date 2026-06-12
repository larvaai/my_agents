# Add a Mini Repo Lab

Mini repo labs are small experiments that can run standalone and through the shared root entrypoint.

Full development guide:

```text
docs/18_MINI_REPO_DEVELOPMENT.md
```

## Contract

Each lab should:

- live in its own folder, for example `business_prompt_lab/` or `experiments/<lab_name>/`
- have at least one standalone runner script with `if __name__ == "__main__"`
- accept CLI args through `argparse`
- write runtime outputs under `var/<lab_name>/...`
- avoid changing global repo state unless the user explicitly asks for it
- register commands in `tools/mini_repo_registry.py`

## Run From Root

List labs:

```powershell
python main.py lab list
```

Run a lab default command:

```powershell
python main.py lab business_prompt_lab --mock "question"
```

Run a specific command:

```powershell
python main.py lab business_prompt_lab benchmark --list
python main.py lab business_prompt_lab:agent-room --dry-run "question"
```

The old orchestrator entrypoint still works:

```powershell
python main.py
python main.py prompts/test_mcp_prompt.md
```

## Register a New Lab

Add one `MiniRepo(...)` entry in `tools/mini_repo_registry.py`:

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
            description="Run one evaluation flow.",
            aliases=(),
        ),
    ),
)
```

Then add a small registry test in `tests/test_mini_repo_registry.py` if the lab is part of the supported surface.
