# Test Case Template

## TestCase Entry

Add to `run_all_cases.py`:

```python
TestCase(
    name="<group>_<number>_<short_name>",
    group="<group>",
    prompt_file="test_<name>.md",
    expect_contains=[
        "EXPECTED_SENTINEL",
    ],
    expect_not_contains=[
        "Agent/LLM call failed",
        "Agent returned invalid JSON too many times",
        "Unknown MCP tool",
    ],
    timeout=240,
    prompt="""
Prompt content.
""".strip(),
)
```

## Prompt Rules

- Use a unique sentinel.
- State exact tools expected.
- State forbidden tools.
- Ask for JSON tool call or JSON final only.
- Keep acceptance criteria concrete.

## Run

```powershell
python run_all_cases.py --case <case_name> --fail-fast
```

