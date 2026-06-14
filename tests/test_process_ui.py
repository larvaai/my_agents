from __future__ import annotations

import unittest
from pathlib import Path

from run_process_ui import build_command, derive_run_state


class ProcessUiTests(unittest.TestCase):
    def test_root_command_includes_user_control_dir(self) -> None:
        command = build_command("root", Path("prompt.md"), "ui_root_1", 12)

        self.assertIn("main.py", command)
        self.assertIn("--user-control-dir", command)
        self.assertIn("--max-steps", command)
        self.assertIn("12", command)
        self.assertEqual(command[-1], "prompt.md")

    def test_langgraph_command_uses_main_langgraph(self) -> None:
        command = build_command("langgraph", Path("prompt.md"), "ui_langgraph_1", 12)

        self.assertIn("main_langgraph.py", command)
        self.assertEqual(command[-1], "prompt.md")

    def test_derive_run_state_tracks_agent_tool_and_directive(self) -> None:
        events = [
            {"kind": "StateEvent", "sequence": 1, "status": "langgraph_node_started", "node": "planner", "step": 1},
            {"kind": "ActionEvent", "sequence": 2, "action": "tool", "node": "code", "tool": "file_editor.file_editor_insert", "step": 2},
            {"kind": "ObservationEvent", "sequence": 3, "tool": "file_editor.file_editor_insert", "result": {"ok": True}, "step": 3},
            {
                "kind": "UserDirectiveEvent",
                "sequence": 4,
                "directive": {
                    "intent": "modify_flow",
                    "status": "accepted",
                    "operations": [{"op": "remove_or_skip_agent", "target": "critic", "mode": "skip_current_run_only"}],
                },
            },
        ]

        state = derive_run_state("run_test", events, summary={"metrics": {"steps": 3}})

        self.assertEqual(state["current_agent"], "code")
        self.assertEqual(state["step"], 3)
        self.assertEqual(state["last_tool"], "file_editor.file_editor_insert")
        self.assertEqual(state["directives"][0]["intent"], "modify_flow")
        self.assertEqual({agent["name"] for agent in state["agents"]}, {"planner", "code"})


if __name__ == "__main__":
    unittest.main()
