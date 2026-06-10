from __future__ import annotations

from agents.lenses.base_lens import LensSpec


PLANNER_LENSES: tuple[LensSpec, ...] = (
    LensSpec(
        name="product_manager",
        department="planning",
        purpose="Clarify the real user goal, success criteria, must-have behavior, and nice-to-have scope.",
        allowed_tools=("issue.issue_list", "issue.issue_get", "ledger.ledger_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "product_manager",
            "user_goal": "",
            "success_criteria": [],
            "must_have": [],
            "nice_to_have": [],
        },
    ),
    LensSpec(
        name="project_manager",
        department="planning",
        purpose="Split the work into milestones, tasks, and a clear execution order.",
        allowed_tools=("issue.*", "ledger.ledger_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "project_manager",
            "milestones": [],
            "tasks": [],
            "execution_order": [],
        },
    ),
    LensSpec(
        name="dependency_planner",
        department="planning",
        purpose="Find task, file, and module dependencies and identify what can run in parallel.",
        allowed_tools=("code_index.*", "filesystem.read_file", "issue.issue_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "dependency_planner",
            "dependencies": [],
            "blocked_tasks": [],
            "parallelizable_tasks": [],
        },
    ),
    LensSpec(
        name="risk_manager",
        department="planning",
        purpose="Identify technical risk, scope creep, missing tests, dependency risk, and local LLM risk.",
        allowed_tools=("issue.issue_create", "ledger.ledger_append", "ledger.ledger_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "risk_manager",
            "risks": [],
            "mitigations": [],
            "requires_human_approval": [],
        },
    ),
    LensSpec(
        name="scope_control",
        department="planning",
        purpose="Keep the task bounded and explicitly separate in-scope work from out-of-scope work.",
        allowed_tools=("issue.issue_create", "ledger.ledger_append"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "scope_control",
            "in_scope": [],
            "out_of_scope": [],
            "scope_warnings": [],
        },
    ),
)
