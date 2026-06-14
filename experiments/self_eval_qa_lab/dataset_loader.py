from __future__ import annotations

import json
import random
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


LAB_DIR = Path(__file__).resolve().parent
ROOT_DIR = LAB_DIR.parent.parent
MANIFEST_PATH = LAB_DIR / "datasets" / "logikon_bench_manifest.json"
DEFAULT_CACHE_DIR = ROOT_DIR / "var" / "self_eval_qa_lab" / "datasets"
OPTION_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass(frozen=True)
class DatasetCase:
    case_id: str
    dataset_id: str
    subset: str
    split: str
    passage: str
    question: str
    options: list[str]
    answer_index: int
    source_path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def answer_letter(self) -> str:
        return option_letter(self.answer_index)

    @property
    def answer_text(self) -> str:
        if 0 <= self.answer_index < len(self.options):
            return self.options[self.answer_index]
        return ""


def option_letter(index: int) -> str:
    if index < 0 or index >= len(OPTION_LETTERS):
        raise ValueError(f"Option index out of range: {index}")
    return OPTION_LETTERS[index]


def option_index(letter: str) -> int:
    normalized = letter.strip().upper()
    if normalized not in OPTION_LETTERS:
        raise ValueError(f"Option letter out of range: {letter!r}")
    return OPTION_LETTERS.index(normalized)


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def available_subsets(manifest: dict[str, Any] | None = None) -> list[str]:
    data = manifest or load_manifest()
    return [str(item["id"]) for item in data.get("subsets", [])]


def resolve_subset_specs(subsets: Iterable[str] | None, manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = manifest or load_manifest()
    requested = [item.strip() for item in subsets or [] if item and item.strip()]
    if not requested:
        requested = available_subsets(data)
    specs_by_id = {str(item["id"]): item for item in data.get("subsets", [])}
    missing = [item for item in requested if item not in specs_by_id]
    if missing:
        known = ", ".join(specs_by_id)
        raise ValueError(f"Unknown subset(s): {', '.join(missing)}. Known: {known}")
    return [specs_by_id[item] for item in requested]


def split_subset_arg(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def download_logikon_subset(
    spec: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    refresh: bool = False,
) -> Path:
    data = manifest or load_manifest()
    source_path = str(spec["path"])
    cache_path = cache_dir / "logikon-bench" / source_path
    if cache_path.exists() and not refresh:
        return cache_path

    base_url = str(data["raw_base_url"])
    url = base_url.rstrip("/") + "/" + source_path
    request = urllib.request.Request(url, headers={"User-Agent": "self-eval-qa-lab"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(payload)
    return cache_path


def normalize_answer_index(raw_answer: Any) -> int:
    if isinstance(raw_answer, int):
        return raw_answer
    if isinstance(raw_answer, str):
        stripped = raw_answer.strip()
        if stripped.isdigit():
            return int(stripped)
        if len(stripped) == 1 and stripped.upper() in OPTION_LETTERS:
            return option_index(stripped)
    raise ValueError(f"Unsupported answer value: {raw_answer!r}")


def load_cases_from_jsonl(
    path: Path,
    *,
    dataset_id: str,
    subset: str,
    split: str = "test",
    source_path: str | None = None,
    start_index: int = 0,
) -> list[DatasetCase]:
    cases: list[DatasetCase] = []
    with path.open("r", encoding="utf-8") as handle:
        for row_index, line in enumerate(handle):
            if not line.strip():
                continue
            raw = json.loads(line)
            options = [str(item) for item in raw.get("options", [])]
            if not options:
                raise ValueError(f"Missing options in {path}:{row_index + 1}")
            answer_index = normalize_answer_index(raw.get("answer"))
            if answer_index >= len(options):
                raise ValueError(f"Answer index {answer_index} exceeds options in {path}:{row_index + 1}")
            absolute_index = start_index + row_index
            cases.append(
                DatasetCase(
                    case_id=f"{dataset_id}:{subset}:{split}:{absolute_index + 1:05d}",
                    dataset_id=dataset_id,
                    subset=subset,
                    split=split,
                    passage=str(raw.get("passage") or "").strip(),
                    question=str(raw.get("question") or "").strip(),
                    options=options,
                    answer_index=answer_index,
                    source_path=source_path or str(path),
                    metadata={
                        "row_index": absolute_index,
                        "raw_keys": sorted(raw.keys()),
                    },
                )
            )
    return cases


def load_logikon_cases(
    *,
    subsets: Iterable[str] | None = None,
    limit: int | None = None,
    offset: int = 0,
    shuffle: bool = False,
    seed: int = 13,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    refresh: bool = False,
) -> list[DatasetCase]:
    manifest = load_manifest()
    specs = resolve_subset_specs(subsets, manifest)
    all_cases: list[DatasetCase] = []
    for spec in specs:
        path = download_logikon_subset(spec, manifest=manifest, cache_dir=cache_dir, refresh=refresh)
        all_cases.extend(
            load_cases_from_jsonl(
                path,
                dataset_id=str(manifest["dataset_id"]),
                subset=str(spec["id"]),
                split=str(spec.get("split") or "test"),
                source_path=str(spec["path"]),
            )
        )

    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(all_cases)
    if offset:
        all_cases = all_cases[offset:]
    if limit is not None:
        all_cases = all_cases[:limit]
    return all_cases


def render_case_question(case: DatasetCase, *, prompt_style: str = "standard") -> str:
    option_lines = "\n".join(f"{option_letter(index)}. {text}" for index, text in enumerate(case.options))
    style_notes = {
        "standard": [
            "Choose exactly one option.",
            "Give a concise visible rationale.",
            "End with a final line in this exact format: Answer: <letter>",
        ],
        "strict_final": [
            "Choose exactly one option.",
            "Do not restate every option.",
            "Keep the visible rationale to at most 4 sentences.",
            "The last non-empty line must be exactly: Answer: <letter>",
        ],
        "deliberate": [
            "Choose exactly one option.",
            "Check the constraints carefully before answering.",
            "Publish only a concise rationale, not a long chain-of-thought.",
            "The last non-empty line must be exactly: Answer: <letter>",
        ],
    }
    notes = style_notes.get(prompt_style, style_notes["standard"])
    blocks = [
        "Benchmark task: multiple-choice reasoning.",
        "",
        f"Dataset: {case.dataset_id}",
        f"Subset: {case.subset}",
        f"Case ID: {case.case_id}",
        "",
    ]
    if case.passage:
        blocks.extend(["Passage:", case.passage, ""])
    blocks.extend(
        [
            "Question:",
            case.question,
            "",
            "Options:",
            option_lines,
            "",
            "Instructions:",
            "\n".join(f"- {note}" for note in notes),
        ]
    )
    return "\n".join(blocks).strip() + "\n"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def safe_case_filename(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "case"


def parse_multiple_choice_answer(text: str, options: list[str]) -> str | None:
    valid_letters = OPTION_LETTERS[: len(options)]
    if not text.strip():
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    tail_lines = lines[-5:]
    line_patterns = [
        r"(?i)^(?:final\s+answer|answer|ans)\s*[:\-]\s*\(?([A-Z])\)?\.?$",
        r"(?i)^(?:the\s+)?(?:answer|option|choice)\s+(?:is\s+)?(?:(?:option|choice)\s+)?\(?([A-Z])\)?\.?$",
        r"(?i)^\(?([A-Z])\)?\.?$",
    ]
    for line in reversed(tail_lines):
        for pattern in line_patterns:
            match = re.match(pattern, line)
            if match:
                letter = match.group(1).upper()
                if letter in valid_letters:
                    return letter

    normalized_output = normalize_text("\n".join(tail_lines))
    exact_option_hits = []
    for index, option in enumerate(options):
        normalized_option = normalize_text(option)
        if len(normalized_option) >= 12 and normalized_option in normalized_output:
            exact_option_hits.append(option_letter(index))
    unique_hits = sorted(set(exact_option_hits))
    if len(unique_hits) == 1:
        return unique_hits[0]
    return None
