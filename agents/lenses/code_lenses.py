from __future__ import annotations

from agents.lenses.base_lens import LensSpec


CODE_LENSES: tuple[LensSpec, ...] = (
    LensSpec(
        name="implementation",
        department="engineering",
        purpose="Implement the direct user request with the smallest correct source change.",
        allowed_tools=(
            "file_editor.*",
            "filesystem.create_directory",
            "filesystem.write_file",
        ),
        forbidden_tools=(
            "lint_test.*",
            "python.*",
            "terminal.terminal_run",
            "git.git_commit",
        ),
        output_schema={
            "lens": "implementation",
            "files_to_modify": [],
            "implementation_steps": [],
            "notes": [],
        },
    ),
    LensSpec(
        name="integration",
        department="engineering",
        purpose="Check that new code connects to existing modules, config, prompts, tools, and public contracts.",
        allowed_tools=("filesystem.read_file", "code_index.*", "file_editor.file_editor_view"),
        forbidden_tools=("git.git_commit", "terminal.terminal_run"),
        output_schema={
            "lens": "integration",
            "integration_points": [],
            "required_config_updates": [],
            "compatibility_notes": [],
        },
    ),
    LensSpec(
        name="defensive_coding",
        department="engineering",
        purpose="Identify malformed input, timeout, empty result, exception, and JSON/tool failure modes before editing.",
        allowed_tools=("filesystem.read_file", "code_index.*", "file_editor.file_editor_view"),
        forbidden_tools=("git.git_commit",),
        output_schema={
            "lens": "defensive_coding",
            "failure_modes": [],
            "guards_to_add": [],
            "error_messages": [],
        },
    ),
    LensSpec(
        name="refactor_discipline",
        department="engineering",
        purpose="Prevent broad refactors; only allow refactoring that is necessary for the current task.",
        allowed_tools=("filesystem.read_file", "code_index.*", "file_editor.file_editor_view"),
        forbidden_tools=("git.git_commit", "filesystem.move_file"),
        output_schema={
            "lens": "refactor_discipline",
            "refactor_needed": False,
            "safe_refactors": [],
            "forbidden_refactors": [],
        },
    ),
    LensSpec(
        name="developer_experience",
        department="engineering",
        purpose="Keep names, error messages, docs, and test commands clear for the next developer.",
        allowed_tools=("filesystem.read_file", "document.document_extract_text"),
        forbidden_tools=("git.git_commit",),
        output_schema={
            "lens": "developer_experience",
            "readability_notes": [],
            "naming_notes": [],
            "docs_needed": [],
        },
    ),
)
