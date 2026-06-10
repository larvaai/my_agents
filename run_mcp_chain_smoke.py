from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


PROJECT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"
SMOKE_DIR = "_mcp_chain_smoke"
RUNS_DIR = PROJECT_DIR / "test_runs"

os.environ["LEDGER_PATH"] = str(WORKSPACE_DIR / SMOKE_DIR / "ledger.jsonl")

from tools.mcp_client import call_mcp_tool  # noqa: E402
from tools.mcp_config import MCP_SERVERS, MCP_TOOL_NAMES  # noqa: E402


class ChainFailure(AssertionError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ChainFailure(message)


def _call(tool: str, args: dict[str, Any] | None = None, *, require_ok: bool = True) -> dict[str, Any]:
    result = call_mcp_tool(tool, args or {})
    if require_ok:
        _require(bool(result.get("ok")), f"{tool} failed: {json.dumps(result, ensure_ascii=False)}")
    return result


def _write_report(path: str, title: str, content: str) -> dict[str, Any]:
    return _call(
        "document.document_write_markdown",
        {
            "path": path,
            "title": title,
            "content": content,
            "overwrite": True,
        },
    )


def chain_web_fetch_document_ledger() -> dict[str, Any]:
    health = _call("search.search_health")
    search = _call("search.web_search", {"query": "Example Domain", "limit": 3})
    results = search.get("results") or []
    _require(len(results) > 0, "search.web_search returned no results")

    url = results[0]["url"]
    fetch = _call("fetch.fetch_url", {"url": url, "max_chars": 2000, "timeout": 10})

    sentinel = "CHAIN_WEB_FETCH_DOCUMENT_LEDGER_OK"
    report_path = f"{SMOKE_DIR}/web_fetch_report.md"
    _write_report(
        report_path,
        "Web Fetch Chain Report",
        "\n".join(
            [
                sentinel,
                f"Provider: {search.get('provider')}",
                f"URL: {fetch.get('final_url') or url}",
                f"Status: {fetch.get('status')}",
                f"Title: {fetch.get('title')}",
            ]
        ),
    )
    extracted = _call("document.document_extract_text", {"path": report_path, "max_chars": 2000})
    _require(sentinel in extracted.get("text", ""), "document_extract_text did not return sentinel")

    _call(
        "ledger.ledger_append",
        {
            "entry_type": "chain_test",
            "title": sentinel,
            "data": {"url": url, "provider": search.get("provider")},
            "tags": ["chain", "web", "document"],
        },
    )
    ledger_search = _call("ledger.ledger_search", {"text": sentinel, "limit": 5})
    _require(len(ledger_search.get("results") or []) >= 1, "ledger_search did not find web chain entry")

    return {
        "sentinel": sentinel,
        "provider": health.get("providers"),
        "result_count": len(results),
        "fetched_title": fetch.get("title"),
        "report_path": report_path,
    }


def chain_document_filesystem_python_ledger() -> dict[str, Any]:
    sentinel = "CHAIN_DOC_FS_PY_LEDGER_OK"
    spec_path = f"{SMOKE_DIR}/calc_spec.md"
    _write_report(
        spec_path,
        "Calc Spec",
        "CHAIN_CALC_RULE_2026\nnet_score(base, bonus, penalty) returns base + bonus - penalty.",
    )
    spec = _call("document.document_extract_text", {"path": spec_path, "max_chars": 2000})
    _require("CHAIN_CALC_RULE_2026" in spec.get("text", ""), "spec sentinel missing")

    buggy_code = '''def net_score(base, bonus, penalty):
    return base + bonus + penalty

if __name__ == "__main__":
    assert net_score(10, 5, 3) == 12
    print("CHAIN_DOC_FS_PY_LEDGER_OK")
'''
    fixed_code = buggy_code.replace("base + bonus + penalty", "base + bonus - penalty")
    code_path = "code/chain_calc.py"

    _call("filesystem.write_file", {"path": code_path, "content": buggy_code})
    first_run = _call("python.run_python", {"path": code_path, "timeout": 10}, require_ok=False)
    _require(not first_run.get("ok"), "buggy code unexpectedly passed")

    read_result = _call("filesystem.read_file", {"path": code_path})
    text = read_result.get("text") or read_result.get("content") or ""
    _require("base + bonus + penalty" in text, "filesystem.read_file did not return buggy code")

    _call("filesystem.write_file", {"path": code_path, "content": fixed_code})
    second_run = _call("python.run_python", {"path": code_path, "timeout": 10})
    _require(sentinel in second_run.get("stdout", ""), "fixed python run missing sentinel")

    _call(
        "ledger.ledger_append",
        {
            "entry_type": "chain_test",
            "title": sentinel,
            "data": {"first_returncode": first_run.get("returncode"), "second_returncode": second_run.get("returncode")},
            "tags": ["chain", "document", "python"],
        },
    )

    return {
        "sentinel": sentinel,
        "first_returncode": first_run.get("returncode"),
        "second_stdout": second_run.get("stdout"),
    }


def chain_playwright_fetch_document_ledger() -> dict[str, Any]:
    sentinel = "CHAIN_PLAYWRIGHT_FETCH_DOCUMENT_OK"
    health = _call("playwright.playwright_health", require_ok=False)
    if not health.get("ok"):
        _write_report(
            f"{SMOKE_DIR}/playwright_fetch_report.md",
            "Playwright Fetch Report",
            f"{sentinel}\nDependency failure: {health.get('error')}",
        )
        _call(
            "ledger.ledger_append",
            {
                "entry_type": "dependency_failure",
                "title": sentinel,
                "data": {"error": health.get("error")},
                "tags": ["chain", "playwright", "dependency"],
            },
        )
        return {"sentinel": sentinel, "status": "dependency_failure", "error": health.get("error")}

    text = _call(
        "playwright.playwright_get_text",
        {"url": "https://example.com", "selector": "body", "timeout_ms": 30000, "max_chars": 1000},
    )
    screenshot = _call(
        "playwright.playwright_screenshot",
        {"url": "https://example.com", "path": f"{SMOKE_DIR}/example_playwright.png", "full_page": True, "timeout_ms": 30000},
    )
    fetch = _call("fetch.fetch_url", {"url": "https://example.com", "max_chars": 1000, "timeout": 10})

    _write_report(
        f"{SMOKE_DIR}/playwright_fetch_report.md",
        "Playwright Fetch Report",
        "\n".join(
            [
                sentinel,
                f"Playwright title: {text.get('title')}",
                f"Screenshot: {screenshot.get('path')}",
                f"Fetch title: {fetch.get('title')}",
                f"Fetch status: {fetch.get('status')}",
            ]
        ),
    )
    _call(
        "ledger.ledger_append",
        {
            "entry_type": "chain_test",
            "title": sentinel,
            "data": {"screenshot": screenshot.get("path"), "title": text.get("title")},
            "tags": ["chain", "playwright", "fetch"],
        },
    )
    return {"sentinel": sentinel, "title": text.get("title"), "screenshot": screenshot.get("path")}


def chain_git_document_ledger_readonly() -> dict[str, Any]:
    sentinel = "CHAIN_GIT_DOCUMENT_LEDGER_READONLY_OK"
    status = _call("git.git_status")
    diff = _call("git.git_diff_unstaged")
    report_path = f"{SMOKE_DIR}/git_readonly_audit.md"
    _write_report(
        report_path,
        "Git Readonly Audit",
        "\n".join(
            [
                sentinel,
                "Readonly git audit only.",
                f"Status keys: {sorted(status.keys())}",
                f"Diff chars: {len(json.dumps(diff, ensure_ascii=False))}",
            ]
        ),
    )
    _call("document.document_outline", {"path": report_path, "max_items": 20})
    _call(
        "ledger.ledger_append",
        {
            "entry_type": "audit",
            "title": sentinel,
            "data": {"status_ok": status.get("ok"), "diff_ok": diff.get("ok")},
            "tags": ["chain", "git", "readonly"],
        },
    )
    return {"sentinel": sentinel, "status_ok": status.get("ok"), "diff_ok": diff.get("ok")}


def chain_rag_health_gate_document_ledger() -> dict[str, Any]:
    sentinel = "CHAIN_RAG_HEALTH_GATE_RESULT"
    health = _call("rag.rag_health", require_ok=False)
    report_path = f"{SMOKE_DIR}/rag_health_gate.md"

    if not health.get("ok"):
        _write_report(
            report_path,
            "RAG Health Gate",
            f"{sentinel}\nRAG dependency failure: {health.get('error')}",
        )
        _call(
            "ledger.ledger_append",
            {
                "entry_type": "dependency_failure",
                "title": sentinel,
                "data": {"error": health.get("error")},
                "tags": ["chain", "rag", "dependency"],
            },
        )
        return {"sentinel": sentinel, "status": "dependency_failure", "error": health.get("error")}

    note_path = "notes/chain_rag_note.md"
    _call(
        "filesystem.write_file",
        {
            "path": note_path,
            "content": "CHAIN_RAG_SENTINEL_2026\nChain RAG test verifies ingest, search, document report, and ledger audit.\n",
        },
    )
    ingest = _call("rag.rag_ingest", {"path": note_path})
    search = _call(
        "rag.rag_search",
        {
            "query": "CHAIN_RAG_SENTINEL_2026 chain ingest search ledger",
            "top_k": 5,
            "score_threshold": 0.65,
        },
    )
    _write_report(
        report_path,
        "RAG Chain Report",
        f"{sentinel}\nIngested: {ingest.get('ingested_chunks')}\nHits: {len(search.get('hits') or [])}",
    )
    _call(
        "ledger.ledger_append",
        {
            "entry_type": "chain_test",
            "title": sentinel,
            "data": {"hits": len(search.get("hits") or [])},
            "tags": ["chain", "rag"],
        },
    )
    return {"sentinel": sentinel, "status": "ok", "hits": len(search.get("hits") or [])}


def chain_terminal_risk_metadata() -> dict[str, Any]:
    sentinel = "CHAIN_TERMINAL_RISK_METADATA_OK"
    present = "terminal" in MCP_SERVERS and "terminal_run" in MCP_TOOL_NAMES.get("terminal", ())
    _require(present, "terminal.terminal_run is not registered")

    safe = _call(
        "terminal.terminal_run",
        {
            "argv": ["python", "-c", f"print('{sentinel}')"],
            "timeout": 10,
            "cwd": ".",
            "purpose": "test terminal metadata on small probe",
        },
    )
    metadata = safe.get("command_metadata") or {}
    _require(sentinel in safe.get("stdout", ""), "terminal safe probe missing sentinel")
    _require(metadata.get("summary"), "terminal safe probe missing summary")
    _require(metadata.get("security_risk") in {"low", "medium"}, "terminal safe probe missing low/medium security_risk")

    blocked = _call(
        "terminal.terminal_run",
        {
            "argv": ["cmd", "/c", "echo", "should_not_run"],
            "timeout": 10,
            "cwd": ".",
            "purpose": "ensure shell execution is blocked",
        },
        require_ok=False,
    )
    blocked_metadata = blocked.get("command_metadata") or {}
    _require(not blocked.get("ok"), "blocked shell command unexpectedly succeeded")
    _require(blocked.get("blocked"), "blocked shell command missing blocked=true")
    _require(blocked_metadata.get("security_risk") == "blocked", "blocked shell command missing blocked risk")

    return {
        "sentinel": sentinel,
        "safe_risk": metadata.get("security_risk"),
        "safe_summary": metadata.get("summary"),
        "blocked_risk": blocked_metadata.get("security_risk"),
    }


def chain_extended_mcp_core() -> dict[str, Any]:
    sentinel = "CHAIN_EXTENDED_MCP_CORE_OK"
    expected = {
        "code_index": ("code_index", "code_find_symbol", "code_find_references", "code_dependency_graph"),
        "lint_test": ("lint_compile", "test_python_file", "test_smoke_suite"),
        "docker": ("docker_ps", "docker_compose_ps", "docker_compose_logs"),
        "obsidian": ("obsidian_write_note", "obsidian_read_note", "obsidian_search_notes", "obsidian_list_notes"),
        "issue": ("issue_create", "issue_list", "issue_add_comment", "issue_update", "issue_get"),
    }
    for server_name, tool_names in expected.items():
        _require(server_name in MCP_SERVERS, f"{server_name} MCP server is not registered")
        registered = MCP_TOOL_NAMES.get(server_name, ())
        for tool_name in tool_names:
            _require(tool_name in registered, f"{server_name}.{tool_name} is not registered")

    index = _call("code_index.code_index", {"path": "mcp_servers", "max_files": 80})
    _require(index.get("files_count", 0) > 0, "code_index did not scan mcp_servers")
    symbol = _call("code_index.code_find_symbol", {"name": "terminal_run", "path": "mcp_servers", "max_results": 20})
    _require(symbol.get("count", 0) >= 1, "code_find_symbol did not find terminal_run")
    refs = _call("code_index.code_find_references", {"name": "FastMCP", "path": "mcp_servers", "max_results": 50})
    _require(refs.get("count", 0) >= 1, "code_find_references did not find FastMCP")
    graph = _call("code_index.code_dependency_graph", {"path": "mcp_servers", "max_files": 80})
    _require(isinstance(graph.get("graph"), dict), "code_dependency_graph missing graph")

    compile_result = _call("lint_test.lint_compile", {"path": "mcp_servers", "timeout": 60})
    _require(compile_result.get("checked_files", 0) > 0, "lint_compile checked no files")
    smoke_result = _call("lint_test.test_smoke_suite", {"timeout": 60}, require_ok=False)
    _require("results" in smoke_result, "test_smoke_suite missing results")

    docker_result = _call("docker.docker_ps", {"all": True, "timeout": 20}, require_ok=False)
    docker_metadata = docker_result.get("command_metadata") or {}
    _require(docker_metadata.get("summary"), "docker_ps missing command metadata summary")
    _require(docker_metadata.get("security_risk") == "low", "docker_ps missing low security risk")

    note_path = "Projects/Extended MCP Smoke.md"
    note_body = f"# Extended MCP Smoke\n\n{sentinel}\n"
    write_note = _call("obsidian.obsidian_write_note", {"path": note_path, "content": note_body, "overwrite": True})
    read_note = _call("obsidian.obsidian_read_note", {"path": note_path, "max_chars": 2000})
    _require(sentinel in read_note.get("text", ""), "obsidian_read_note missing sentinel")
    search_note = _call("obsidian.obsidian_search_notes", {"query": sentinel, "folder": "Projects", "limit": 10})
    _require(search_note.get("count", 0) >= 1, "obsidian_search_notes did not find sentinel")
    list_note = _call("obsidian.obsidian_list_notes", {"folder": "Projects", "limit": 50})
    _require(any(item.get("path") == note_path for item in list_note.get("notes", [])), "obsidian_list_notes did not list note")

    created = _call(
        "issue.issue_create",
        {
            "title": sentinel,
            "description": "Smoke test for extended MCP core.",
            "kind": "task",
            "priority": 2,
            "assignee": "smoke_agent",
            "labels": ["smoke", "mcp"],
            "related_files": ["mcp_servers/issue_server.py"],
        },
    )
    issue_id = created.get("issue_id")
    _require(isinstance(issue_id, int), "issue_create did not return issue_id")
    listed = _call("issue.issue_list", {"status": "open", "limit": 50})
    _require(any(item.get("id") == issue_id for item in listed.get("issues", [])), "issue_list did not include created issue")
    _call("issue.issue_add_comment", {"issue_id": issue_id, "message": "Extended MCP smoke comment.", "author": "smoke_agent"})
    _call("issue.issue_update", {"issue_id": issue_id, "status": "in_progress"})
    fetched = _call("issue.issue_get", {"issue_id": issue_id})
    _require(fetched.get("issue", {}).get("status") == "in_progress", "issue_update did not persist status")
    _require(len(fetched.get("comments") or []) >= 1, "issue_get missing comment")

    return {
        "sentinel": sentinel,
        "indexed_files": index.get("files_count"),
        "terminal_symbol_matches": symbol.get("count"),
        "lint_checked_files": compile_result.get("checked_files"),
        "docker_ok": docker_result.get("ok"),
        "note_path": note_path,
        "issue_id": issue_id,
    }


CASES: list[tuple[str, Callable[[], dict[str, Any]]]] = [
    ("chain_01_web_fetch_document_ledger", chain_web_fetch_document_ledger),
    ("chain_02_document_filesystem_python_ledger", chain_document_filesystem_python_ledger),
    ("chain_03_playwright_fetch_document_ledger", chain_playwright_fetch_document_ledger),
    ("chain_04_git_document_ledger_readonly", chain_git_document_ledger_readonly),
    ("chain_05_rag_health_gate_document_ledger", chain_rag_health_gate_document_ledger),
    ("chain_06_terminal_risk_metadata", chain_terminal_risk_metadata),
    ("chain_07_extended_mcp_core", chain_extended_mcp_core),
]


def main() -> int:
    results = []
    for name, func in CASES:
        started = datetime.now()
        try:
            details = func()
            status = "PASS"
            error = ""
        except Exception as exc:
            details = {}
            status = "FAIL"
            error = str(exc)

        results.append(
            {
                "name": name,
                "status": status,
                "duration_seconds": round((datetime.now() - started).total_seconds(), 3),
                "details": details,
                "error": error,
            }
        )
        print(f"{status:4} {name}")
        if error:
            print(f"     {error}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    summary_path = run_dir / "mcp_chain_smoke.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSummary saved to: {summary_path}")

    return 1 if any(item["status"] != "PASS" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
