from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.user_agent import UserDirectiveController, parse_user_directive
from orchestrator import run_orchestrator


class UserAgentControlTests(unittest.TestCase):
    def test_parse_force_final_directive(self) -> None:
        directive = parse_user_directive("Dung lai, tra loi ngay.", "userdir_0001")

        self.assertEqual(directive.status, "accepted")
        self.assertEqual(directive.intent, "flow_control")
        self.assertTrue(any(operation["op"] == "force_final" for operation in directive.operations))

    def test_reject_disable_trace_directive(self) -> None:
        directive = parse_user_directive("Tat trace log va dung tiep.", "userdir_0001")

        self.assertEqual(directive.status, "rejected")
        self.assertEqual(directive.intent, "blocked_runtime_invariant")
        self.assertTrue(any(operation["target"] == "trace_logging" for operation in directive.operations))

    def test_parse_current_run_only_skip_agent_directive(self) -> None:
        directive = parse_user_directive(
            "Trong lượt chạy này không cần vai trò của critic agent, lượt sau vẫn cần.",
            "userdir_0001",
        )

        self.assertEqual(directive.status, "accepted")
        self.assertEqual(directive.scope, "current_run")
        self.assertEqual(directive.intent, "modify_flow")
        skip_ops = [operation for operation in directive.operations if operation["op"] == "remove_or_skip_agent"]
        self.assertEqual(len(skip_ops), 1)
        self.assertEqual(skip_ops[0]["mode"], "skip_current_run_only")
        self.assertIn("critic agent", skip_ops[0]["target"])
        self.assertTrue(any("current run" in note for note in directive.notes))

    def test_control_dir_jsonl_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            control_dir = Path(tmp) / "control"
            controller = UserDirectiveController(run_id="run_test", control_dir=control_dir)
            controller.start()
            inbox = control_dir / "inbox.jsonl"
            inbox.write_text(json.dumps({"text": "Tra loi ngan hon."}, ensure_ascii=False) + "\n", encoding="utf-8")

            directives = controller.poll()

            self.assertEqual(len(directives), 1)
            self.assertEqual(directives[0].status, "accepted")
            self.assertTrue((control_dir / "accepted_directives.jsonl").exists())

    def test_orchestrator_marks_output_stale_when_user_directive_arrives_during_agent_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "runs"
            control_dir = Path(tmp) / "control"
            control_dir.mkdir(parents=True)
            calls: list[list[dict[str, str]]] = []

            def fake_tool_agent(messages: list[dict[str, str]]) -> str:
                calls.append(messages)
                if len(calls) == 1:
                    inbox = control_dir / "inbox.jsonl"
                    inbox.write_text(
                        json.dumps({"text": "Dung lai, tra loi ngay va ngan gon."}, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    return json.dumps({"action": "final", "message": "old answer"}, ensure_ascii=False)
                return json.dumps({"action": "final", "message": "new answer"}, ensure_ascii=False)

            with patch.dict("os.environ", {"AGENT_RUNS_DIR": str(runs_dir), "AGENT_EVENT_LOG": "1"}, clear=False):
                with patch("orchestrator.tool_agent", side_effect=fake_tool_agent):
                    result = run_orchestrator(
                        "Original task",
                        max_steps=3,
                        user_control_dir=control_dir,
                    )

            self.assertEqual(result, "new answer")
            self.assertGreaterEqual(len(calls), 2)
            second_call_text = "\n".join(message["content"] for message in calls[1])
            self.assertIn("USER AGENT LIVE DIRECTIVES", second_call_text)
            summary_files = list(runs_dir.glob("*/summary.json"))
            self.assertEqual(len(summary_files), 1)
            summary = json.loads(summary_files[0].read_text(encoding="utf-8"))
            self.assertEqual(summary["metrics"]["stale_agent_outputs"], 1)


if __name__ == "__main__":
    unittest.main()
