from __future__ import annotations

from agents.lenses.base_lens import LensSpec


ARCHITECT_LENSES: tuple[LensSpec, ...] = (
    LensSpec(
        name="system_architect",
        department="architecture",
        purpose="Define modules, responsibilities, communication paths, and boundaries.",
        allowed_tools=("code_index.*", "filesystem.read_file", "rag.rag_search", "context7.*"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "system_architect",
            "modules": [],
            "responsibilities": [],
            "boundaries": [],
        },
    ),
    LensSpec(
        name="data_architect",
        department="architecture",
        purpose="Design entities, schemas, state rules, serialization, migration, and data ownership.",
        allowed_tools=("code_index.*", "filesystem.read_file", "document.document_extract_text"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "data_architect",
            "entities": [],
            "schemas": [],
            "state_rules": [],
            "migration_notes": [],
        },
    ),
    LensSpec(
        name="api_contract",
        department="architecture",
        purpose="Keep public interfaces, input/output contracts, and compatibility boundaries stable.",
        allowed_tools=("code_index.*", "filesystem.read_file", "context7.*"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "api_contract",
            "public_interfaces": [],
            "input_contracts": [],
            "output_contracts": [],
            "compatibility_risks": [],
        },
    ),
    LensSpec(
        name="security_architect",
        department="architecture",
        purpose="Design safe sandboxing, secret handling, path safety, tool boundaries, and blocked patterns.",
        allowed_tools=("filesystem.read_file", "code_index.*", "ledger.ledger_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "security_architect",
            "threats": [],
            "security_requirements": [],
            "blocked_patterns": [],
        },
    ),
    LensSpec(
        name="scalability",
        department="architecture",
        purpose="Plan for long context, many agents, many files, large tests, and avoid overengineering.",
        allowed_tools=("code_index.*", "ledger.ledger_search", "issue.issue_search"),
        forbidden_tools=("file_editor.*", "filesystem.write_file", "git.git_commit"),
        output_schema={
            "lens": "scalability",
            "bottlenecks": [],
            "scaling_plan": [],
            "do_not_overengineer": [],
        },
    ),
)
