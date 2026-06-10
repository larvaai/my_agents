from __future__ import annotations

from agents.lenses.base_lens import LensSpec


REVIEW_LENSES: tuple[LensSpec, ...] = (
    LensSpec(
        name="senior_engineer",
        department="review",
        purpose="Review correctness, simplicity, idiomatic design, and obvious bugs.",
        allowed_tools=("filesystem.read_file", "file_editor.file_editor_view", "code_index.*", "git.git_diff"),
        forbidden_tools=("file_editor.file_editor_create", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "senior_engineer",
            "approved": True,
            "issues": [],
            "suggested_fixes": [],
        },
    ),
    LensSpec(
        name="scope_diff",
        department="review",
        purpose="Compare changed files against the requested scope and flag unrelated edits.",
        allowed_tools=("git.git_diff", "git.git_diff_unstaged", "git.git_status"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "scope_diff",
            "changed_files": [],
            "out_of_scope_changes": [],
            "scope_status": "ok|warning|fail",
        },
    ),
    LensSpec(
        name="security_review",
        department="review",
        purpose="Look for path traversal, secret exposure, unsafe shell, permission, network, and browser risks.",
        allowed_tools=("filesystem.read_file", "code_index.*", "git.git_diff"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "security_review",
            "security_status": "pass|warning|fail",
            "findings": [],
            "must_fix": [],
        },
    ),
    LensSpec(
        name="maintainability",
        department="review",
        purpose="Judge readability, module boundaries, duplication, and future maintenance cost.",
        allowed_tools=("filesystem.read_file", "code_index.*", "git.git_diff"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "maintainability",
            "maintainability_status": "pass|warning|fail",
            "issues": [],
            "recommendations": [],
        },
    ),
    LensSpec(
        name="release_risk",
        department="review",
        purpose="Decide whether evidence is enough to approve, request changes, or escalate to human review.",
        allowed_tools=("git.git_diff", "lint_test.lint_compile", "lint_test.lint_ruff_check"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "release_risk",
            "risk_level": "low|medium|high",
            "blocking_issues": [],
            "approval_recommendation": "approve|request_changes|human_review",
        },
    ),
)
