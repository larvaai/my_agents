from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from business_prompt_lab.repo_understanding_lab import main as lab_main
from business_prompt_lab.repo_understanding_lab.repo_understanding.context_pack import build_context_pack
from business_prompt_lab.repo_understanding_lab.repo_understanding.docs_reader import read_docs
from business_prompt_lab.repo_understanding_lab.repo_understanding.graphs import build_graph, build_test_map
from business_prompt_lab.repo_understanding_lab.repo_understanding.manifests import read_manifests
from business_prompt_lab.repo_understanding_lab.repo_understanding.scanner import scan_repo
from business_prompt_lab.repo_understanding_lab.repo_understanding.symbols import extract_python_symbols


class RepoUnderstandingLabTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = lab_main.fixture_repo_path()

    def test_scanner_classifies_fixture_files(self) -> None:
        file_map = scan_repo(self.repo)
        paths = {node["path"]: node for node in file_map}

        self.assertIn("src/planner.py", paths)
        self.assertEqual(paths["src/planner.py"]["role"], "source")
        self.assertTrue(paths["tests/test_planner.py"]["is_test"])
        self.assertEqual(paths["requirements.txt"]["role"], "manifest")

    def test_symbol_extractor_finds_planner_method(self) -> None:
        file_map = scan_repo(self.repo)
        symbol_index = extract_python_symbols(self.repo, file_map)
        names = {symbol["qualified_name"] for symbol in symbol_index["symbols"]}

        self.assertIn("src.planner.PlannerAgent", names)
        self.assertIn("src.planner.PlannerAgent.plan", names)

    def test_context_pack_links_question_to_symbol_and_tests(self) -> None:
        file_map = scan_repo(self.repo)
        profile = read_manifests(self.repo, file_map)
        docs = read_docs(self.repo, file_map)
        symbol_index = extract_python_symbols(self.repo, file_map)
        graph = build_graph(file_map, symbol_index, docs)
        test_map = build_test_map(file_map, symbol_index)
        context = build_context_pack(
            question="How does PlannerAgent plan work?",
            repo_profile=profile,
            file_map=file_map,
            symbol_index=symbol_index,
            graph=graph,
            docs=docs,
            test_map=test_map,
            runtime_map=[],
        )

        self.assertEqual(context["task"]["intent"], "symbol_question")
        self.assertTrue(any(symbol["qualified_name"] == "src.planner.PlannerAgent.plan" for symbol in context["relevant_symbols"]))
        self.assertTrue(context["tests"])

    def test_mock_ask_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = lab_main.run(["--mock", "--out-dir", tmp, "ask", "How does PlannerAgent work?"])

            self.assertEqual(code, 0)
            out_dir = Path(tmp)
            self.assertTrue((out_dir / "maps" / "file_map.json").exists())
            self.assertTrue((out_dir / "context" / "context_pack.json").exists())
            self.assertTrue((out_dir / "reports" / "observer_report.json").exists())
            self.assertTrue((out_dir / "admin" / "full_trace.json").exists())
            self.assertTrue((out_dir / "final_answer.md").exists())

    def test_business_prompt_lab_question_prioritizes_lab_runners_and_docs(self) -> None:
        repo = lab_main.PROJECT_DIR / "business_prompt_lab"
        with tempfile.TemporaryDirectory() as tmp:
            baseline = lab_main.run_ask(
                repo,
                Path(tmp),
                "Doc hieu business_prompt_lab: repo nay co nhung runner nao, agent room chay ra sao, output artifacts nam dau?",
            )
            context = baseline["context_pack"]
            selected_paths = {node["path"] for node in context["relevant_files"]}

            self.assertIn("agent_room.py", selected_paths)
            self.assertIn("run.py", selected_paths)
            self.assertIn("README.md", selected_paths)
            self.assertIn("NO_CODE_AGENT_FLOW.md", selected_paths)
            self.assertTrue(context["tests"])
            self.assertGreaterEqual(context["understanding_report"]["score_5"], 3.0)
            self.assertTrue(context["repo_flow"]["agent_room_flow"])
            self.assertTrue((Path(baseline["summary"]["out_dir"]) / "admin" / "full_trace.json").exists())
            self.assertTrue((Path(baseline["summary"]["out_dir"]) / "reports" / "understanding_report.json").exists())


if __name__ == "__main__":
    unittest.main()
