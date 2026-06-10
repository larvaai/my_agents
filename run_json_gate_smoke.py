from __future__ import annotations

from output_gate.json_gate import json_gate


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    cases = [
        (
            "fenced_trailing_comma",
            """
            Sure, here is the JSON:

            ```json
            {
              "action": "tool",
              "tool": "filesystem.write_file",
              "args": {
                "path": "code/test.py",
                "content": "print('hello')",
              }
            }
            ```
            """,
            True,
            "pass",
        ),
        (
            "unquoted_keys",
            """
            {
              action: "tool",
              tool: "filesystem.read_file",
              args: {
                path: "README.md",
              }
            }
            """,
            True,
            "pass",
        ),
        (
            "safe_aliases",
            """
            {
              "action": "tool",
              "tool_name": "filesystem.write_file",
              "arguments": {
                "filepath": "code/alias.py",
                "data": "print(1)"
              }
            }
            """,
            True,
            "pass",
        ),
        (
            "mixed_single_quoted_line_items",
            """
            {
              "action": "tool",
              "tool": "file_editor.file_editor_write_lines",
              "args": {
                "path": "code/mixed_quotes.py",
                "lines": ["print('a')", 'VALUE = "b"'],
                "overwrite": true
              }
            }
            """,
            True,
            "pass",
        ),
        (
            "unsafe_path",
            """
            {
              "action": "tool",
              "tool": "filesystem.write_file",
              "args": {
                "path": "../../secret.txt",
                "content": "bad"
              }
            }
            """,
            False,
            "dry_run",
        ),
        (
            "terminal_command_string_blocked",
            """
            {
              "action": "tool",
              "tool": "terminal.terminal_run",
              "args": {
                "command": "python main.py"
              }
            }
            """,
            False,
            "tool_args",
        ),
        (
            "git_mutation_policy_blocked",
            """
            {
              "action": "tool",
              "tool": "git.git_commit",
              "args": {
                "message": "test"
              }
            }
            """,
            False,
            "dry_run",
        ),
        (
            "final_message",
            """
            {
              "action": "final",
              "message": "Done"
            }
            """,
            True,
            "pass",
        ),
        (
            "raw_newline_in_final_string",
            '{"action":"final","message":"line one\nline two"}',
            True,
            "pass",
        ),
    ]

    for name, raw, expected_ok, expected_stage in cases:
        result = json_gate(raw)
        _assert(
            result.ok is expected_ok,
            f"{name}: expected ok={expected_ok}, got {result.ok}, error={result.error}",
        )
        _assert(
            result.stage == expected_stage,
            f"{name}: expected stage={expected_stage}, got {result.stage}, error={result.error}",
        )
        print(
            "PASS",
            name,
            f"stage={result.stage}",
            f"repaired_by_code={result.repaired_by_code}",
        )

    print("JSON_GATE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
