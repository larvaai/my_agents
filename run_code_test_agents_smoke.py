from __future__ import annotations

from orchestration.code_test_orchestrator import CodeTestOrchestrator


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    task = (
        "Create a small Python file code/lens_smoke_test.py that prints "
        "CODE_TEST_LENS_OK. Then validate that it runs."
    )
    result = CodeTestOrchestrator(max_cycles=2).run(task)
    _assert(result.get("ok") is True, f"orchestrator did not pass: {result}")
    _assert(result.get("status") == "ready_for_review", f"unexpected status: {result.get('status')}")

    history = result.get("history", [])
    _assert(len(history) >= 2, "expected code and test history entries")
    code_result = history[0]["result"]
    test_result = history[1]["result"]

    _assert(code_result["route"]["next_agent"] == "test_agent", "code did not route to test_agent")
    _assert(test_result["route"]["next_agent"] == "review_agent", "test did not route to review_agent")
    _assert(code_result["execution"]["ok"] is True, "code execution failed")
    _assert(test_result["execution"]["ok"] is True, "test execution failed")

    stdout = test_result["execution"]["test_results"][0].get("stdout", "")
    _assert("CODE_TEST_LENS_OK" in stdout, "sentinel missing from test stdout")

    print("CODE_TEST_AGENTS_V05_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
