from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from lankallm.benchmark import Language, balance_table, check_questions, load_questions
from lankallm.benchmark.validation import script_ratio
from lankallm.cli import app

SI_TEXT = "ශ්‍රී ලංකාවේ අගනුවර කුමක්ද?"  # TODO placeholder, needs native review
TA_TEXT = "இலங்கையின் தலைநகரம் எது?"  # TODO placeholder, needs native review


def record(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "question_id": "si-fact-001",
        "language": "si",
        "category": "factual",
        "question": SI_TEXT,
        "expected_answer": "TODO",
        "evidence": "TODO",
        "difficulty": "easy",
        "evaluation_method": "reference_match",
        "benchmark_version": "0.1",
    }
    base.update(overrides)
    return base


def write_jsonl(path: Path, records: list[dict[str, Any]], extra: str = "") -> Path:
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    path.write_text("\n".join(lines) + "\n" + extra, encoding="utf-8")
    return path


def test_valid_file_loads_and_has_no_issues(tmp_path: Path) -> None:
    path = write_jsonl(
        tmp_path / "q.jsonl",
        [record(), record(question_id="ta-fact-001", language="ta", question=TA_TEXT)],
    )
    result = load_questions(path)
    assert len(result.questions) == 2
    assert result.issues == []
    assert check_questions(result.questions) == []


def test_bad_lines_are_reported_with_line_numbers(tmp_path: Path) -> None:
    path = write_jsonl(
        tmp_path / "q.jsonl",
        [record(), record(question_id="x", difficulty="impossible")],
        extra="{not json}\n",
    )
    result = load_questions(path)
    assert len(result.questions) == 1
    assert {i.line for i in result.issues} == {2, 3}


def test_unknown_field_is_rejected(tmp_path: Path) -> None:
    path = write_jsonl(tmp_path / "q.jsonl", [record(difficult="easy")])
    result = load_questions(path)
    assert result.questions == []
    assert any("difficult" in i.message for i in result.issues)


def test_duplicate_ids_are_flagged(tmp_path: Path) -> None:
    path = write_jsonl(tmp_path / "q.jsonl", [record(), record()])
    issues = check_questions(load_questions(path).questions)
    assert any("duplicate" in i.message for i in issues)


def test_language_script_mismatch_is_flagged(tmp_path: Path) -> None:
    path = write_jsonl(tmp_path / "q.jsonl", [record(language="ta")])  # Sinhala text
    issues = check_questions(load_questions(path).questions)
    assert any("does not look like" in i.message for i in issues)


def test_factual_question_needs_evidence(tmp_path: Path) -> None:
    path = write_jsonl(tmp_path / "q.jsonl", [record(evidence=None)])
    issues = check_questions(load_questions(path).questions)
    assert any("evidence" in i.message for i in issues)


def test_placeholders_are_flagged(tmp_path: Path) -> None:
    path = write_jsonl(tmp_path / "q.jsonl", [record(is_placeholder=True)])
    issues = check_questions(load_questions(path).questions)
    assert any("placeholder" in i.message for i in issues)


def test_balance_table_counts_per_language(tmp_path: Path) -> None:
    path = write_jsonl(
        tmp_path / "q.jsonl",
        [
            record(),
            record(question_id="a"),
            record(question_id="b", language="ta", question=TA_TEXT),
        ],
    )
    table = balance_table(load_questions(path).questions)
    factual = next(v for k, v in table.items() if k.value == "factual")
    assert factual[Language.SINHALA] == 2
    assert factual[Language.TAMIL] == 1


def test_script_ratio_handles_empty_and_mixed_text() -> None:
    assert script_ratio("123 ?!", Language.SINHALA) == 0.0
    assert 0.0 < script_ratio(SI_TEXT + " hello", Language.SINHALA) < 1.0


def test_cli_validate_exit_codes(tmp_path: Path) -> None:
    runner = CliRunner()
    good = write_jsonl(tmp_path / "good.jsonl", [record()])
    bad = write_jsonl(tmp_path / "bad.jsonl", [record(evidence=None)])
    assert runner.invoke(app, ["benchmark", "validate", str(good)]).exit_code == 0
    assert runner.invoke(app, ["benchmark", "validate", str(bad)]).exit_code == 1
