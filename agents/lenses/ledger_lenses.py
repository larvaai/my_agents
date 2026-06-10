from __future__ import annotations

from agents.lenses.base_lens import LensSpec


LEDGER_LENSES: tuple[LensSpec, ...] = (
    LensSpec(
        name="historian",
        department="ledger_ops",
        purpose="Record what happened, which files changed, which validations ran, and the final outcome.",
        allowed_tools=("ledger.ledger_append", "ledger.ledger_tail"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "historian",
            "events_to_record": [],
            "summary": "",
        },
    ),
    LensSpec(
        name="task_state",
        department="ledger_ops",
        purpose="Maintain task status transitions such as pending, in_progress, testing, needs_review, done, blocked.",
        allowed_tools=("issue.issue_get", "issue.issue_update", "issue.issue_list"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "task_state",
            "task_updates": [],
            "invalid_transitions": [],
        },
    ),
    LensSpec(
        name="decision_record",
        department="ledger_ops",
        purpose="Capture durable decisions, rationale, and rejected alternatives when the run changes architecture or policy.",
        allowed_tools=("ledger.ledger_append", "document.document_write_markdown", "document.document_append_section"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "decision_record",
            "decisions_to_record": [],
            "adr_needed": False,
        },
    ),
    LensSpec(
        name="auditor",
        department="ledger_ops",
        purpose="Check consistency: done with failing tests, approve with blockers, code changes without ledger evidence.",
        allowed_tools=("ledger.ledger_tail", "ledger.ledger_search", "issue.issue_list", "issue.issue_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "auditor",
            "consistency_status": "pass|warning|fail",
            "inconsistencies": [],
            "repairs_needed": [],
        },
    ),
    LensSpec(
        name="incident_tracker",
        department="ledger_ops",
        purpose="Turn repeated failures, tool incidents, and unresolved test failures into issues or ledger incidents.",
        allowed_tools=("issue.issue_create", "issue.issue_add_comment", "ledger.ledger_append"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "terminal.terminal_run", "git.git_commit"),
        output_schema={
            "lens": "incident_tracker",
            "issues_to_create": [],
            "incidents_to_record": [],
            "severity": "low|medium|high",
        },
    ),
)
