from __future__ import annotations

from agents.lenses.base_lens import LensSpec


FINAL_LENSES: tuple[LensSpec, ...] = (
    LensSpec(
        name="executive_summary",
        department="communication",
        purpose="Summarize what happened, pass/fail status, key results, and remaining risk.",
        allowed_tools=("ledger.ledger_tail", "issue.issue_list"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "executive_summary",
            "summary": "",
            "status": "success|partial|failed",
            "key_results": [],
        },
    ),
    LensSpec(
        name="technical_writer",
        department="communication",
        purpose="Report files changed, tests run, commands, and important stdout/stderr evidence.",
        allowed_tools=("ledger.ledger_tail", "issue.issue_list", "git.git_diff_unstaged"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "technical_writer",
            "files_changed": [],
            "tests_run": [],
            "technical_notes": [],
        },
    ),
    LensSpec(
        name="user_facing_explanation",
        department="communication",
        purpose="Explain the outcome clearly without excessive implementation detail.",
        allowed_tools=("ledger.ledger_tail",),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "user_facing_explanation",
            "message": "",
            "next_user_actions": [],
        },
    ),
    LensSpec(
        name="limitation_disclosure",
        department="communication",
        purpose="State what was not done, not tested, or assumed, without overclaiming.",
        allowed_tools=("ledger.ledger_tail", "issue.issue_list"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "limitation_disclosure",
            "limitations": [],
            "untested_areas": [],
            "assumptions": [],
        },
    ),
    LensSpec(
        name="next_step_recommendation",
        department="communication",
        purpose="Suggest useful next steps in priority order.",
        allowed_tools=("issue.issue_list", "ledger.ledger_tail"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "next_step_recommendation",
            "recommended_next_steps": [],
            "priority_order": [],
        },
    ),
)
