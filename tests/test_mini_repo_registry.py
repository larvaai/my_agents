from __future__ import annotations

import unittest

from tools.mini_repo_registry import (
    list_mini_repos,
    resolve_lab_invocation,
    resolve_mini_repo,
)


class MiniRepoRegistryTests(unittest.TestCase):
    def test_business_prompt_lab_is_registered(self) -> None:
        repo = resolve_mini_repo("business_prompt_lab")

        self.assertEqual(repo.id, "business_prompt_lab")
        self.assertTrue(repo.root.exists())
        self.assertEqual(repo.default_command, "agent-room")

    def test_self_eval_qa_lab_is_registered(self) -> None:
        repo = resolve_mini_repo("self-eval")

        self.assertEqual(repo.id, "self_eval_qa_lab")
        self.assertTrue(repo.root.exists())
        self.assertEqual(repo.default_command, "run")

    def test_default_command_keeps_forwarded_args(self) -> None:
        repo, command, args = resolve_lab_invocation(
            "business_prompt_lab",
            ["--mock", "question"],
        )

        self.assertEqual(repo.id, "business_prompt_lab")
        self.assertEqual(command.id, "agent-room")
        self.assertEqual(args, ["--mock", "question"])

    def test_command_can_be_selected_by_first_forwarded_arg(self) -> None:
        _, command, args = resolve_lab_invocation(
            "business_prompt_lab",
            ["benchmark", "--list"],
        )

        self.assertEqual(command.id, "benchmark")
        self.assertEqual(args, ["--list"])

    def test_command_can_be_selected_with_colon_syntax(self) -> None:
        _, command, args = resolve_lab_invocation(
            "business_prompt_lab:agent-room",
            ["--dry-run", "question"],
        )

        self.assertEqual(command.id, "agent-room")
        self.assertEqual(args, ["--dry-run", "question"])

    def test_self_eval_default_command(self) -> None:
        repo, command, args = resolve_lab_invocation(
            "self_eval_qa_lab",
            ["--mock", "question"],
        )

        self.assertEqual(repo.id, "self_eval_qa_lab")
        self.assertEqual(command.id, "run")
        self.assertEqual(args, ["--mock", "question"])

    def test_registered_command_scripts_exist(self) -> None:
        for repo in list_mini_repos():
            for command in repo.commands:
                with self.subTest(repo=repo.id, command=command.id):
                    self.assertTrue(command.script.exists())


if __name__ == "__main__":
    unittest.main()
