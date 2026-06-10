from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.lenses import (
    ARCHITECT_LENSES,
    CODE_LENSES,
    FINAL_LENSES,
    LEDGER_LENSES,
    PLANNER_LENSES,
    RESEARCH_LENSES,
    REVIEW_LENSES,
    TEST_LENSES,
)


READ_ONLY_FILES = (
    "filesystem.read_file",
    "filesystem.read_text_file",
    "filesystem.read_multiple_files",
    "filesystem.list_directory",
    "filesystem.list_directory_with_sizes",
    "filesystem.directory_tree",
    "filesystem.search_files",
    "filesystem.get_file_info",
    "filesystem.list_allowed_directories",
    "file_editor.file_editor_view",
)

READ_ONLY_GIT = (
    "git.git_status",
    "git.git_diff_unstaged",
    "git.git_diff_staged",
    "git.git_diff",
    "git.git_log",
    "git.git_show",
    "git.git_branch",
)

RESEARCH_TOOLS = (
    *READ_ONLY_FILES,
    "code_index.*",
    "search.search_health",
    "search.web_search",
    "fetch.fetch_url",
    "context7.*",
    "rag.rag_health",
    "rag.rag_search",
    "document.document_extract_text",
    "document.document_outline",
    "obsidian.obsidian_list_notes",
    "obsidian.obsidian_read_note",
    "obsidian.obsidian_search_notes",
)

PLANNER_TOOLS = (
    *READ_ONLY_FILES,
    "code_index.*",
    "rag.rag_health",
    "rag.rag_search",
    "document.document_extract_text",
    "document.document_outline",
    "issue.*",
    "ledger.*",
)

ARCHITECT_TOOLS = (
    *READ_ONLY_FILES,
    "code_index.*",
    "context7.*",
    "rag.rag_health",
    "rag.rag_search",
    "document.document_extract_text",
    "document.document_outline",
    "document.document_write_markdown",
    "document.document_append_section",
    "issue.*",
    "ledger.*",
)

CODE_TOOLS = (
    *READ_ONLY_FILES,
    "code_index.*",
    "filesystem.create_directory",
    "filesystem.write_file",
    "file_editor.file_editor_create",
    "file_editor.file_editor_write_lines",
    "file_editor.file_editor_str_replace",
    "file_editor.file_editor_insert",
    "document.document_extract_text",
    "issue.issue_get",
    "issue.issue_update",
    "issue.issue_add_comment",
)

TEST_TOOLS = (
    *READ_ONLY_FILES,
    "code_index.*",
    "lint_test.*",
    "python.*",
    "terminal.terminal_run",
    "issue.issue_create",
    "issue.issue_get",
    "issue.issue_update",
    "issue.issue_add_comment",
    "ledger.ledger_append",
)

REVIEW_TOOLS = (
    *READ_ONLY_FILES,
    *READ_ONLY_GIT,
    "code_index.*",
    "lint_test.lint_compile",
    "lint_test.lint_ruff_check",
    "lint_test.lint_ruff_format_check",
    "issue.*",
    "ledger.*",
)

LEDGER_TOOLS = (
    "ledger.*",
    "issue.*",
    "obsidian.*",
    "document.document_extract_text",
    "document.document_write_markdown",
    "document.document_append_section",
    "document.document_outline",
)

FINAL_TOOLS = (
    *READ_ONLY_FILES,
    *READ_ONLY_GIT,
    "ledger.ledger_tail",
    "ledger.ledger_search",
    "ledger.ledger_get",
    "ledger.ledger_stats",
    "issue.issue_list",
    "issue.issue_get",
    "issue.issue_search",
    "issue.issue_stats",
    "document.document_extract_text",
    "document.document_outline",
)


ROLE_AGENTS: dict[str, BaseAgent] = {
    "tool": BaseAgent(
        name="Tool Agent",
        role="General-purpose backward-compatible tool agent.",
        system_prompt=(
            "Handle the full current single-agent workflow. This role exists for "
            "backward compatibility with the current orchestrator."
        ),
        allowed_tools=("*",),
        allowed_skills=("*",),
    ),
    "research": BaseAgent(
        name="Research Agent",
        role="Gather external and internal context without modifying project state.",
        department="Research Department",
        department_rule=(
            "Research owns context gathering and evidence quality. Use source scouting, "
            "credibility, fact-checking, synthesis, and knowledge curation lenses. "
            "Research stays read-only for project code."
        ),
        system_prompt=(
            "Research facts, docs, code references, and RAG context. Prefer primary "
            "sources and read-only tools. Do not edit files or create issues unless "
            "delegated through another role."
        ),
        lenses=RESEARCH_LENSES,
        allowed_tools=RESEARCH_TOOLS,
        allowed_skills=("project-plan",),
    ),
    "planner": BaseAgent(
        name="Planner Agent",
        role="Turn user goals into scoped tasks, issues, risks, and validation plans.",
        department="Planning Department",
        department_rule=(
            "Planning owns product intent, project sequencing, dependencies, risk, "
            "and scope control. Planning may update issues or ledger records, but "
            "does not edit source code."
        ),
        system_prompt=(
            "Plan the work. Create or update issues when useful. Stay read-only for "
            "source code and do not implement changes."
        ),
        lenses=PLANNER_LENSES,
        allowed_tools=PLANNER_TOOLS,
        allowed_skills=("project-plan",),
    ),
    "architect": BaseAgent(
        name="Architect Agent",
        role="Design architecture, boundaries, contracts, and implementation approach.",
        department="Architecture Department",
        department_rule=(
            "Architecture owns system boundaries, data shape, API contracts, security "
            "requirements, and scalability tradeoffs. Architecture writes guidance, "
            "not source implementation."
        ),
        system_prompt=(
            "Produce design decisions and architecture guidance. You may write design "
            "documents, ledger decisions, and issues, but do not edit source code."
        ),
        lenses=ARCHITECT_LENSES,
        allowed_tools=ARCHITECT_TOOLS,
        allowed_skills=("project-plan",),
    ),
    "code": BaseAgent(
        name="Code Agent",
        role="Engineering Department: implement narrowly scoped source changes, then hand off to QA.",
        department="Engineering Department",
        department_rule=(
            "Engineering owns implementation only. Use engineering lenses before each edit: "
            "implementation, integration, defensive coding, refactor discipline, and developer experience. "
            "Engineering does not approve its own work and does not run validation in the LangGraph role split."
        ),
        system_prompt=(
            "Act like a disciplined engineering room. Read before editing, make the smallest code change, "
            "preserve unrelated work, and hand off to QA for validation. When repairing after a failed test, "
            "patch the failing file narrowly instead of rewriting whole files. For generated code files, "
            "prefer file_editor.file_editor_write_lines with one physical file line per JSON array item; "
            "do not place an entire file into one string containing newline escapes. Each lines item must "
            "still be a double-quoted JSON string; use single quotes only inside the generated Python code "
            "and avoid triple-quoted docstrings in tool payloads."
        ),
        lenses=CODE_LENSES,
        allowed_tools=CODE_TOOLS,
        allowed_skills=("code-edit", "debug-traceback"),
    ),
    "test": BaseAgent(
        name="Test Agent",
        role="QA Department / Test Council: design and execute validation, classify failures, and report evidence.",
        department="QA Department",
        department_rule=(
            "QA owns validation strategy and execution. Most QA lenses are reasoning-only; only the "
            "test_executor lens may run validation tools. QA never edits source code."
        ),
        system_prompt=(
            "Act like a QA lead with a small test council. Use logic, critical thinking, experienced QA, "
            "regression, and purpose-alignment lenses to decide what matters, then use the test_executor "
            "lens to run the narrowest real validation. Return actionable evidence and send code failures "
            "back to Engineering."
        ),
        lenses=TEST_LENSES,
        allowed_tools=TEST_TOOLS,
        allowed_skills=("run-test", "debug-traceback"),
    ),
    "review": BaseAgent(
        name="Review Agent",
        role="Senior Review Board: review changes for correctness, scope, security, maintainability, and release risk.",
        department="Senior Review Board",
        department_rule=(
            "Review is an approval gate, not an implementation room. Use review lenses to produce findings "
            "ordered by severity. Do not edit files, do not mutate git, and do not approve without validation evidence."
        ),
        system_prompt=(
            "Act like a senior engineering review board. Lead with concrete findings, check scope diff and "
            "security risk, judge maintainability, and make an approve/request_changes/human_review recommendation. "
            "Create issues for unresolved risks when useful."
        ),
        lenses=REVIEW_LENSES,
        allowed_tools=REVIEW_TOOLS,
        allowed_skills=("git-review", "run-test"),
    ),
    "ledger": BaseAgent(
        name="Ledger Agent",
        role="Secretary / Audit / Operations Department: maintain durable memory, task state, decisions, and incidents.",
        department="Ledger / Audit / Operations Department",
        department_rule=(
            "Ledger/Ops records what happened and audits consistency. It does not implement code, run terminal, "
            "or claim success without evidence from QA/Review. Prefer concise durable records."
        ),
        system_prompt=(
            "Act like project secretary, auditor, and operations desk. Record important events, update task state, "
            "capture decisions, audit contradictions, and turn repeated failures into issues or incidents. "
            "Do not store secrets."
        ),
        lenses=LEDGER_LENSES,
        allowed_tools=LEDGER_TOOLS,
        allowed_skills=(),
    ),
    "final": BaseAgent(
        name="Final Agent",
        role="Synthesize final user-facing answers from gathered evidence.",
        department="Communication Department",
        department_rule=(
            "Final owns user-facing communication only. It summarizes evidence, "
            "discloses limits, and recommends next steps without mutating project state."
        ),
        system_prompt=(
            "Summarize outcomes, validation, blockers, and next steps. Prefer read-only "
            "evidence. Do not perform implementation or mutation."
        ),
        lenses=FINAL_LENSES,
        allowed_tools=FINAL_TOOLS,
        allowed_skills=(),
    ),
}


ALIASES = {
    "tool_agent": "tool",
    "research_agent": "research",
    "planner_agent": "planner",
    "architect_agent": "architect",
    "code_agent": "code",
    "test_agent": "test",
    "review_agent": "review",
    "ledger_agent": "ledger",
    "final_agent": "final",
}


def get_agent(name: str) -> BaseAgent:
    key = ALIASES.get(name, name)
    try:
        return ROLE_AGENTS[key]
    except KeyError as exc:
        known = sorted(set(ROLE_AGENTS) | set(ALIASES))
        raise KeyError(f"Unknown agent role: {name}. Known roles: {known}") from exc


def list_agents() -> list[dict]:
    return [
        {
            "key": key,
            **agent.describe(),
        }
        for key, agent in sorted(ROLE_AGENTS.items())
    ]
