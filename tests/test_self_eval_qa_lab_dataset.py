from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from experiments.self_eval_qa_lab import dataset_loader, dataset_runner


class SelfEvalQaLabDatasetTests(unittest.TestCase):
    def test_load_cases_from_jsonl_and_render_question(self) -> None:
        rows = [
            {
                "passage": "All blue tokens are round. Token K is blue.",
                "question": "What follows?",
                "options": ["K is square", "K is round", "K is red", "Nothing follows"],
                "answer": 1,
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            cases = dataset_loader.load_cases_from_jsonl(
                path,
                dataset_id="fixture",
                subset="logic",
            )

        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].answer_letter, "B")
        rendered = dataset_loader.render_case_question(cases[0], prompt_style="strict_final")
        self.assertIn("Answer: <letter>", rendered)
        self.assertIn("B. K is round", rendered)

    def test_parse_multiple_choice_answer_variants(self) -> None:
        options = ["Alpha result", "Beta result", "Gamma result", "Delta result"]

        self.assertEqual(dataset_loader.parse_multiple_choice_answer("Final answer: C", options), "C")
        self.assertEqual(dataset_loader.parse_multiple_choice_answer("The answer is option B.", options), "B")
        self.assertEqual(dataset_loader.parse_multiple_choice_answer("I choose Delta result.", options), "D")
        self.assertIsNone(dataset_loader.parse_multiple_choice_answer("Option A seems tempting, but it is not enough.", options))
        self.assertIsNone(dataset_loader.parse_multiple_choice_answer("The answer is not A.", options))
        self.assertIsNone(dataset_loader.parse_multiple_choice_answer("I cannot tell.", options))

    def test_review_cadence_only_fires_on_batch_boundary(self) -> None:
        self.assertFalse(dataset_runner.should_review_case(0, 20))
        self.assertFalse(dataset_runner.should_review_case(19, 20))
        self.assertTrue(dataset_runner.should_review_case(20, 20))
        self.assertFalse(dataset_runner.should_review_case(21, 20))
        self.assertTrue(dataset_runner.should_review_case(40, 20))

    def test_batch_review_blocks_workflow_change_until_parse_is_reliable(self) -> None:
        records = []
        for index in range(20):
            records.append(
                {
                    "case_id": f"case-{index}",
                    "parse_success": index < 10,
                    "correct": index < 3,
                    "trace_health_status": "clean",
                    "trace_severe_count": 0,
                    "looping_detected": False,
                    "json_fallback_count": 0,
                    "code_violation_count": 0,
                }
            )
        policy = dataset_runner.RuntimePolicy()
        review = dataset_runner.review_batch(records, batch_index=1, policy=policy, target_accuracy=0.7)
        new_policy, recommendations = dataset_runner.decide_batch_adjustment(review, policy)

        self.assertEqual(review["metrics"]["correct"], 3)
        self.assertEqual(review["metrics"]["parse_success"], 10)
        self.assertFalse(review["metrics"]["accuracy_evaluable"])
        self.assertEqual(new_policy.prompt_style, "strict_final")
        self.assertIsNone(new_policy.forced_workflow)
        self.assertEqual(len(recommendations), 1)

    def test_batch_review_changes_workflow_after_parseable_low_accuracy(self) -> None:
        records = []
        for index in range(20):
            records.append(
                {
                    "case_id": f"case-{index}",
                    "parse_success": True,
                    "correct": index < 3,
                    "trace_health_status": "clean",
                    "trace_severe_count": 0,
                    "looping_detected": False,
                    "json_fallback_count": 0,
                    "code_violation_count": 0,
                }
            )
        policy = dataset_runner.RuntimePolicy()
        review = dataset_runner.review_batch(records, batch_index=1, policy=policy, target_accuracy=0.7)
        new_policy, recommendations = dataset_runner.decide_batch_adjustment(review, policy)

        self.assertTrue(review["metrics"]["accuracy_evaluable"])
        self.assertIn("low_accuracy", {item["issue"] for item in review["issues"]})
        self.assertEqual(new_policy.forced_workflow, "assisted")
        self.assertEqual(len(recommendations), 1)


if __name__ == "__main__":
    unittest.main()
