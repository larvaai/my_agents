from __future__ import annotations

import argparse
import os
import unittest
from unittest.mock import patch

from experiments.self_eval_qa_lab import main as lab


class SelfEvalQaLabTests(unittest.TestCase):
    def test_classifier_routes_complex_agent_question_to_lenses(self) -> None:
        classification = lab.classify_question_deterministic(
            "Design a multi-agent evaluation flow with risk review and practical next steps.",
            lab.DEFAULT_LENSES,
        )

        self.assertTrue(classification["needs_lens_flow"])
        self.assertIn("architecture", classification["suggested_lenses"])
        self.assertIn("critic", classification["suggested_lenses"])
        self.assertIn("practical", classification["suggested_lenses"])

    def test_blind_shuffle_hides_sources_but_preserves_mapping(self) -> None:
        pack = lab.blind_shuffle(
            [
                lab.AnswerItem("simple", "Simple", "A"),
                lab.AnswerItem("ours", "Ours", "B"),
                lab.AnswerItem("baseline", "Baseline", "C"),
            ],
            seed=123,
        )

        self.assertEqual(set(pack["visible_answers"]), {"answer_a", "answer_b", "answer_c"})
        self.assertEqual(set(pack["hidden_mapping"].values()), {"simple", "ours", "baseline"})

    def test_reveal_evaluation_maps_scores_to_sources(self) -> None:
        evaluation = {
            "scores": {
                "answer_a": {"total": 70},
                "answer_b": {"total": 90},
            },
            "winner": "answer_b",
        }
        revealed = lab.reveal_evaluation(
            evaluation,
            {
                "answer_a": "simple",
                "answer_b": "ours",
            },
        )

        self.assertEqual(revealed["winner_source"], "ours")
        self.assertEqual(revealed["scores_by_source"]["simple"]["total"], 70)
        self.assertEqual(revealed["scores_by_source"]["ours"]["total"], 90)

    def test_deterministic_flow_observer_flags_unneeded_lenses(self) -> None:
        flow = lab.deterministic_flow_observation(
            {"complexity": "low", "needs_lens_flow": False},
            [{"lens": "architecture"}],
            {"winner_source": "simple"},
            baseline_mode="none",
        )

        self.assertEqual(flow["routing_verdict"], "weak")
        self.assertTrue(flow["wasted_steps"])

    def test_router_sends_simple_definition_direct(self) -> None:
        classification = lab.classify_question_deterministic("Fallback la gi?", lab.DEFAULT_LENSES)
        decision = lab.route_workflow_deterministic(
            "Fallback la gi?",
            classification,
            policy=lab.load_routing_policy(),
        )

        self.assertEqual(decision["selected_workflow"], "direct")
        self.assertFalse(decision["needs_baseline"])

    def test_router_sends_multi_agent_design_deep(self) -> None:
        question = "Design a self-eval multi-agent orchestration workflow with routing, critic, baseline, and lessons."
        classification = lab.classify_question_deterministic(question, lab.DEFAULT_LENSES)
        decision = lab.route_workflow_deterministic(question, classification, policy=lab.load_routing_policy())

        self.assertEqual(decision["selected_workflow"], "deep")
        self.assertTrue(decision["needs_baseline"])

    def test_router_sends_repo_error_to_repo_debug(self) -> None:
        question = "Repo test fail in file main.py with LangGraph state error"
        classification = lab.classify_question_deterministic(question, lab.DEFAULT_LENSES)
        decision = lab.route_workflow_deterministic(question, classification, policy=lab.load_routing_policy())

        self.assertEqual(classification["task_type"], "repo_debug")
        self.assertEqual(decision["selected_workflow"], "repo_debug")
        self.assertFalse(decision["needs_baseline"])

    def test_forced_workflow_overrides_router(self) -> None:
        classification = lab.classify_question_deterministic("Fallback la gi?", lab.DEFAULT_LENSES)
        decision = lab.route_workflow_deterministic(
            "Fallback la gi?",
            classification,
            policy=lab.load_routing_policy(),
            forced_workflow="deep",
        )

        self.assertEqual(decision["selected_workflow"], "deep")
        self.assertIn("Forced workflow", decision["reason"])

    def test_lesson_report_records_routing_issue(self) -> None:
        decision = {
            "selected_workflow": "deep",
        }
        flow = {
            "workflow_verdict": "OVER_ROUTED",
            "recommended_workflow": "direct",
        }
        report = lab.deterministic_lesson_report(decision, flow, {"where_ours_lost": []})

        self.assertFalse(report["apply_updates"])
        self.assertEqual(report["lessons"][0]["lesson_type"], "routing")

    def test_llm_options_default_to_local_provider(self) -> None:
        args = argparse.Namespace(
            llm_provider=None,
            server_url=None,
            server_api_key=None,
            server_model=None,
            model=None,
            llm_timeout=None,
            max_tokens=None,
        )

        options = lab.build_llm_options(args, lab.LabConfig())

        self.assertEqual(options.provider, "local")
        self.assertIsNone(options.server_url)

    def test_llm_options_can_use_server_env(self) -> None:
        args = argparse.Namespace(
            llm_provider="server",
            server_url=None,
            server_api_key=None,
            server_model=None,
            model=None,
            llm_timeout=None,
            max_tokens=None,
        )

        with patch.dict(
            os.environ,
            {
                "SELF_EVAL_SERVER_URL": "https://example.test/v1",
                "SELF_EVAL_SERVER_MODEL": "server-model",
            },
            clear=False,
        ):
            options = lab.build_llm_options(args, lab.LabConfig())

        self.assertEqual(options.provider, "server")
        self.assertEqual(options.server_url, "https://example.test/v1")
        self.assertEqual(options.model, "server-model")


if __name__ == "__main__":
    unittest.main()
