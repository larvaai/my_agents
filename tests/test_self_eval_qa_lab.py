from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
