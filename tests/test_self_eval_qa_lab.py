from __future__ import annotations

import argparse
import os
import tempfile
import unittest
from pathlib import Path
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

    def test_benchmark_multiple_choice_routes_to_assisted(self) -> None:
        question = "\n".join(
            [
                "Benchmark task: multiple-choice reasoning.",
                "",
                "Passage:",
                "A file cabinet contains reports, but this is not a repo task.",
                "",
                "Question:",
                "Which option follows?",
                "",
                "Options:",
                "A. Alpha",
                "B. Beta",
                "",
                "Instructions:",
                "- The last non-empty line must be exactly: Answer: <letter>",
            ]
        )
        classification = lab.classify_question_deterministic(question, lab.DEFAULT_LENSES)
        decision = lab.route_workflow_deterministic(question, classification, policy=lab.load_routing_policy())

        self.assertEqual(classification["task_type"], "benchmark_mcq")
        self.assertEqual(decision["selected_workflow"], "assisted")

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

    def test_trace_health_flags_repeated_agent_outputs(self) -> None:
        calls = [
            {
                "event_type": "agent_call",
                "agent": "critic",
                "step": "review",
                "output": "This answer should name the trade-off, list one risk, and give one concrete next step.",
                "metadata": {},
            },
            {
                "event_type": "agent_call",
                "agent": "answer_synthesizer",
                "step": "rewrite",
                "output": "This answer should name the trade-off, list one risk, and give one concrete next step.",
                "metadata": {},
            },
        ]

        health = lab.analyze_trace_health(calls)

        self.assertTrue(health["looping_detected"])
        self.assertTrue(health["repeated_outputs"])

    def test_trace_health_ignores_superseded_empty_text_output(self) -> None:
        calls = [
            {
                "event_type": "agent_call",
                "agent": "simple_answer",
                "step": "draft",
                "output": "",
                "metadata": {"superseded_by_repair": True},
            },
            {
                "event_type": "agent_call",
                "agent": "simple_answer",
                "step": "draft_empty_repair",
                "output": "The correct option is A.\nAnswer: A",
                "metadata": {},
            },
        ]

        health = lab.analyze_trace_health(calls)

        self.assertEqual(health["empty_or_tiny_outputs"], [])
        self.assertEqual(health["status"], "clean")

    def test_trace_health_ignores_direct_pass_through_repeat(self) -> None:
        answer = "The correct option is A because it follows from the location constraints.\nAnswer: A"
        calls = [
            {
                "event_type": "agent_call",
                "agent": "simple_answer",
                "step": "draft",
                "output": answer,
                "metadata": {},
            },
            {
                "event_type": "agent_output",
                "agent": "direct_answer",
                "step": "finalize",
                "output": answer,
                "metadata": {"pass_through": True},
            },
        ]

        health = lab.analyze_trace_health(calls)

        self.assertFalse(health["looping_detected"])
        self.assertEqual(health["repeated_outputs"], [])

    def test_trace_health_ignores_mock_baseline_repeat(self) -> None:
        answer = "A compact benchmark-style answer with a practical note and no hidden reasoning."
        calls = [
            {
                "event_type": "agent_call",
                "agent": "simple_answer",
                "step": "draft",
                "output": answer,
                "metadata": {},
            },
            {
                "event_type": "agent_output",
                "agent": "chatgpt_baseline",
                "step": "answer",
                "output": answer,
                "metadata": {"mock_baseline": True},
            },
        ]

        health = lab.analyze_trace_health(calls)

        self.assertFalse(health["looping_detected"])
        self.assertEqual(health["repeated_outputs"], [])

    def test_trace_health_flags_mock_provider_repetition(self) -> None:
        answer = "This repeated mock output is long enough to be compared and should still count as a loop signal."
        calls = [
            {
                "event_type": "agent_call",
                "agent": "simple_answer",
                "step": "draft",
                "provider": "mock",
                "output": answer,
                "metadata": {},
            },
            {
                "event_type": "agent_call",
                "agent": "lens_answer",
                "step": "deep_answer",
                "provider": "mock",
                "output": answer,
                "metadata": {},
            },
        ]

        health = lab.analyze_trace_health(calls)

        self.assertTrue(health["looping_detected"])
        self.assertTrue(health["repeated_outputs"])

    def test_text_agent_repairs_empty_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = lab.SelfEvalLab(
                question="Pick A or B.",
                config=lab.LabConfig(version="0.3"),
                baseline_mode="none",
                force_lenses=False,
                forced_workflow=None,
                llm_options=lab.LLMOptions(provider="local", max_tokens=128),
                temperature=0.2,
                mock=False,
                propose_updates=False,
                chatgpt_mode="mock",
                chatgpt_answer_file=None,
                out_dir=Path(tmp),
            )
            runner.recorder = lab.RunRecorder("run_test", Path(tmp) / "run_test")
            with patch(
                "experiments.self_eval_qa_lab.main.call_model",
                side_effect=[
                    ("model-a", ""),
                    ("model-a", "The correct option is A.\nAnswer: A"),
                ],
            ):
                output = runner.call_text_agent(
                    "simple_answer",
                    "draft",
                    "Answer directly.",
                    "Choose A or B.",
                    fallback="Fallback answer.",
                )

        self.assertEqual(output, "The correct option is A.\nAnswer: A")
        self.assertTrue(any(call["step"] == "draft_empty_repair" for call in runner.recorder.agent_calls))

    def test_json_agent_records_deterministic_fallback_after_failed_repair(self) -> None:
        fallback = {
            "task_type": "general_qa",
            "complexity": "low",
            "needs_lens_flow": False,
            "suggested_lenses": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            runner = lab.SelfEvalLab(
                question="Classify this.",
                config=lab.LabConfig(version="0.3"),
                baseline_mode="none",
                force_lenses=False,
                forced_workflow=None,
                llm_options=lab.LLMOptions(provider="local", max_tokens=128),
                temperature=0.2,
                mock=False,
                propose_updates=False,
                chatgpt_mode="mock",
                chatgpt_answer_file=None,
                out_dir=Path(tmp),
            )
            runner.recorder = lab.RunRecorder("run_test", Path(tmp) / "run_test")
            with patch(
                "experiments.self_eval_qa_lab.main.call_model",
                side_effect=[
                    ("model-a", "not json"),
                    ("model-a", "still not json"),
                ],
            ):
                output = runner.call_json_agent(
                    "question_classifier",
                    "classify",
                    "Return JSON.",
                    "Question",
                    fallback=fallback,
                )

        self.assertEqual(output, fallback)
        fallback_events = [call for call in runner.recorder.agent_calls if call["step"] == "classify_fallback"]
        self.assertEqual(len(fallback_events), 1)
        self.assertTrue(fallback_events[0]["metadata"]["used_fallback"])
        health = lab.analyze_trace_health(runner.recorder.agent_calls)
        self.assertEqual(len(health["json_fallbacks"]), 1)

    def test_text_agent_repairs_benchmark_final_answer_contract(self) -> None:
        question = "\n".join(
            [
                "Benchmark task: multiple-choice reasoning.",
                "",
                "Question:",
                "Pick the answer.",
                "",
                "Options:",
                "A. Alpha",
                "B. Beta",
                "",
                "Instructions:",
                "- The last non-empty line must be exactly: Answer: <letter>",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = lab.SelfEvalLab(
                question=question,
                config=lab.LabConfig(version="0.3"),
                baseline_mode="none",
                force_lenses=False,
                forced_workflow=None,
                llm_options=lab.LLMOptions(provider="local", max_tokens=128),
                temperature=0.2,
                mock=False,
                propose_updates=False,
                chatgpt_mode="mock",
                chatgpt_answer_file=None,
                out_dir=Path(tmp),
            )
            runner.recorder = lab.RunRecorder("run_test", Path(tmp) / "run_test")
            with patch(
                "experiments.self_eval_qa_lab.main.call_model",
                side_effect=[
                    ("model-a", "Alpha is the best choice."),
                    ("model-a", "Alpha follows from the prompt.\nAnswer: A"),
                ],
            ):
                output = runner.call_text_agent(
                    "simple_answer",
                    "draft",
                    "Answer directly.",
                    question,
                    fallback="Fallback answer.",
                    enforce_benchmark_answer=True,
                )

        self.assertTrue(output.endswith("Answer: A"))
        self.assertTrue(any(call["step"] == "draft_benchmark_contract_repair" for call in runner.recorder.agent_calls))

    def test_assisted_benchmark_draft_missing_final_forces_rewrite(self) -> None:
        question = "\n".join(
            [
                "Benchmark task: multiple-choice reasoning.",
                "",
                "Question:",
                "Pick the answer.",
                "",
                "Options:",
                "A. Alpha",
                "B. Beta",
                "",
                "Instructions:",
                "- The last non-empty line must be exactly: Answer: <letter>",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = lab.SelfEvalLab(
                question=question,
                config=lab.LabConfig(version="0.3"),
                baseline_mode="none",
                force_lenses=False,
                forced_workflow=None,
                llm_options=lab.LLMOptions(provider="local", max_tokens=128),
                temperature=0.2,
                mock=True,
                propose_updates=False,
                chatgpt_mode="mock",
                chatgpt_answer_file=None,
                out_dir=Path(tmp),
            )
            runner.recorder = lab.RunRecorder("run_test", Path(tmp) / "run_test")
            with patch.object(runner, "call_text_agent", side_effect=["Looks fine.", "Alpha follows.\nAnswer: A"]) as call_mock:
                answer, _ = runner.assisted_answer("Alpha follows.")

        self.assertEqual(answer, "Alpha follows.\nAnswer: A")
        self.assertEqual(call_mock.call_count, 2)

    def test_v03_mock_run_writes_full_trace_and_chatgpt_artifacts(self) -> None:
        args = argparse.Namespace(
            llm_provider=None,
            server_url=None,
            server_api_key=None,
            server_model=None,
            model=None,
            llm_timeout=None,
            max_tokens=None,
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = lab.SelfEvalLab(
                question="JSON agent co nen temp=0 khong?",
                config=lab.LabConfig(version="0.3"),
                baseline_mode="auto",
                force_lenses=False,
                forced_workflow=None,
                llm_options=lab.build_llm_options(args, lab.LabConfig()),
                temperature=0.2,
                mock=True,
                propose_updates=False,
                chatgpt_mode="mock",
                chatgpt_answer_file=None,
                out_dir=Path(tmp),
            )
            result = runner.run()

            self.assertIsNotNone(result.chatgpt_answer)
            self.assertEqual(result.chatgpt_comparison["status"], "compared")
            self.assertTrue((result.run_dir / "admin" / "full_trace.json").exists())
            self.assertTrue((result.run_dir / "prompts" / "chatgpt_prompt.md").exists())
            self.assertTrue((result.run_dir / "audits" / "critical_audit.json").exists())
            self.assertTrue((result.run_dir / "audits" / "evolution_decision.json").exists())
            self.assertTrue((result.run_dir / "audits" / "trace_health.json").exists())
            self.assertTrue(any(event["agent"] == "critical_auditor" for event in result.trace_events))
            self.assertIn(result.trace_health["status"], {"clean", "needs_review"})

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
