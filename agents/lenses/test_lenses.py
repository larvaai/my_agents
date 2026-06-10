from __future__ import annotations

from agents.lenses.base_lens import LensSpec


TEST_LENSES: tuple[LensSpec, ...] = (
    LensSpec(
        name="logic",
        department="qa",
        purpose="Find invariants, impossible states, boundary cases, and state transition bugs.",
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "logic",
            "invariants": [],
            "possible_violations": [],
            "must_test": [],
            "confidence": "low|medium|high",
        },
    ),
    LensSpec(
        name="critical_thinking",
        department="qa",
        purpose="Attack hidden assumptions and false-pass risks before trusting a green test.",
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "critical_thinking",
            "hidden_assumptions": [],
            "adversarial_cases": [],
            "false_pass_risks": [],
            "confidence": "low|medium|high",
        },
    ),
    LensSpec(
        name="experienced_qa",
        department="qa",
        purpose="Choose high-value practical tests: happy path, failure path, integration, dirty data, and regression.",
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "experienced_qa",
            "test_strategy": [],
            "high_value_tests": [],
            "low_value_tests_to_skip": [],
            "confidence": "low|medium|high",
        },
    ),
    LensSpec(
        name="regression",
        department="qa",
        purpose="Use prior failures, issues, ledger, and changed files to select regression checks.",
        allowed_tools=("ledger.ledger_search", "issue.issue_search", "git.git_diff", "code_index.*"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "regression",
            "related_old_failures": [],
            "affected_tests": [],
            "recommended_regression_tests": [],
        },
    ),
    LensSpec(
        name="purpose_alignment",
        department="qa",
        purpose="Catch behavior that technically passes but misses the user's intended purpose.",
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "purpose_alignment",
            "alignment": "pass|warning|fail",
            "conceptual_issues": [],
            "behavior_that_must_remain_true": [],
            "confidence": "low|medium|high",
        },
    ),
    LensSpec(
        name="test_executor",
        department="qa",
        purpose="Run the narrowest real validation and summarize stdout/stderr without editing code.",
        allowed_tools=("python.run_python", "lint_test.*", "terminal.terminal_run", "filesystem.read_file"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "test_executor",
            "tests_run": [],
            "passed": True,
            "failures": [],
            "stdout_summary": "",
            "stderr_summary": "",
        },
    ),
)
