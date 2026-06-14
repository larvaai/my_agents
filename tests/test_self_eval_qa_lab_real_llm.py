from __future__ import annotations

import argparse
import os
import tempfile
import unittest
from pathlib import Path

from experiments.self_eval_qa_lab import main as lab


def _enabled() -> bool:
    return os.getenv("RUN_SELF_EVAL_REAL_LLM") == "1"


@unittest.skipUnless(_enabled(), "Set RUN_SELF_EVAL_REAL_LLM=1 to run real LLM integration tests.")
class SelfEvalQaLabRealLlmTests(unittest.TestCase):
    def test_real_llm_run_has_clean_trace_health(self) -> None:
        provider = os.getenv("SELF_EVAL_REAL_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "local"))
        args = argparse.Namespace(
            llm_provider=provider,
            server_url=os.getenv("SELF_EVAL_SERVER_URL") or os.getenv("LLM_SERVER_URL"),
            server_api_key=os.getenv("SELF_EVAL_SERVER_API_KEY") or os.getenv("LLM_SERVER_API_KEY"),
            server_model=os.getenv("SELF_EVAL_SERVER_MODEL") or os.getenv("LLM_SERVER_MODEL"),
            model=os.getenv("SELF_EVAL_REAL_LLM_MODEL") or os.getenv("LLM_MODEL"),
            llm_timeout=float(os.getenv("SELF_EVAL_REAL_LLM_TIMEOUT", "60")),
            max_tokens=int(os.getenv("SELF_EVAL_REAL_LLM_MAX_TOKENS", "768")),
        )
        chatgpt_mode = os.getenv("SELF_EVAL_REAL_CHATGPT_MODE", "local")
        question = os.getenv(
            "SELF_EVAL_REAL_LLM_QUESTION",
            "JSON agent co nen temperature bang 0 khi can output schema on dinh khong? Tra loi ngan, khong viet code.",
        )

        with tempfile.TemporaryDirectory() as tmp:
            runner = lab.SelfEvalLab(
                question=question,
                config=lab.load_config(),
                baseline_mode="none",
                force_lenses=False,
                forced_workflow="assisted",
                llm_options=lab.build_llm_options(args, lab.load_config()),
                temperature=0.1,
                mock=False,
                propose_updates=False,
                chatgpt_mode=chatgpt_mode,
                chatgpt_answer_file=None,
                out_dir=Path(tmp),
            )
            result = runner.run()

            self.assertTrue(result.trace_events, result.run_dir)
            self.assertTrue((result.run_dir / "admin" / "full_trace.json").exists())
            self.assertTrue((result.run_dir / "traces" / "agent_calls.jsonl").exists())
            self.assertEqual(result.trace_health["status"], "clean", result.trace_health)
            self.assertEqual(result.trace_health["severe_count"], 0, result.trace_health)
            self.assertFalse(result.trace_health["looping_detected"], result.trace_health)
            self.assertFalse(result.trace_health["json_fallbacks"], result.trace_health)
            self.assertFalse(result.trace_health["handoff_loops"], result.trace_health)
            self.assertFalse(result.trace_health["code_violations"], result.trace_health)
            self.assertGreaterEqual(int(result.critical_audit.get("logic_score", 0)), 6, result.critical_audit)


if __name__ == "__main__":
    unittest.main()
