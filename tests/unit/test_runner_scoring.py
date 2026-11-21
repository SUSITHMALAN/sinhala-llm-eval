from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from lankallm.benchmark import Language, load_questions
from lankallm.evaluation import (
    is_refusal,
    language_gap,
    normalise,
    paired_comparison,
    read_scores,
    reference_match,
    score_run,
    summarise,
)
from lankallm.models import MockClient
from lankallm.runner import (
    RunConfig,
    SelectionError,
    latest_responses,
    load_config,
    run_experiment,
    select_questions,
)

SI = "ශ්‍රී ලංකාවේ අගනුවර කුමක්ද?"
TA = "இலங்கையின் தலைநகரம் எது?"


def question(qid: str, lang: str, text: str, **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "question_id": qid,
        "language": lang,
        "category": "factual",
        "question": text,
        "expected_answer": "Kotte",
        "evidence": "TODO",
        "difficulty": "easy",
        "evaluation_method": "reference_match",
        "benchmark_version": "0.1",
    }
    base.update(extra)
    return base


@pytest.fixture
def benchmark(tmp_path: Path) -> Path:
    path = tmp_path / "q.jsonl"
    rows = [question("si-1", "si", SI), question("ta-1", "ta", TA)]
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    return path


def make_config(benchmark: Path, **over: Any) -> RunConfig:
    values: dict[str, Any] = {
        "name": "t",
        "benchmark": benchmark,
        "prompt_version": "p1",
        "seed": 1,
        "temperature": 0.0,
        "max_tokens": 50,
        "max_retries": 2,
        "split": None,
        "limit": None,
        "allow_placeholders": False,
        "models": [{"name": "mock", "provider": "mock"}],
        "raw": {},
    }
    values.update(over)
    return RunConfig(**values)


def test_run_saves_every_response_and_manifest(benchmark: Path, tmp_path: Path) -> None:
    config = make_config(benchmark)
    qs = select_questions(config)
    out = run_experiment(config, qs, [MockClient("a")], tmp_path / "res", run_id="r1")
    assert len(latest_responses(out / "responses.jsonl")) == 2
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["prompt_version"] == "p1"
    assert len(manifest["benchmark_sha256"]) == 64


def test_failures_are_retried_then_recorded_not_dropped(
    benchmark: Path, tmp_path: Path
) -> None:
    config = make_config(benchmark, max_retries=1)
    qs = select_questions(config)
    sleeps: list[float] = []
    client = MockClient("flaky", fail_first=100)
    out = run_experiment(
        config, qs, [client], tmp_path / "res", run_id="r1", sleep=sleeps.append
    )
    records = latest_responses(out / "responses.jsonl")
    assert len(records) == 2
    assert all(r.status == "failed" and r.attempts == 2 for r in records.values())
    assert len(sleeps) == 2  # one backoff per question


def test_resume_skips_successes_and_retries_failures(
    benchmark: Path, tmp_path: Path
) -> None:
    config = make_config(benchmark, max_retries=0)
    qs = select_questions(config)
    root = tmp_path / "res"
    run_experiment(
        config,
        qs,
        [MockClient("m", fail_first=1)],
        root,
        run_id="r",
        sleep=lambda _: None,
    )
    healthy = MockClient("m")
    out = run_experiment(config, qs, [healthy], root, run_id="r", sleep=lambda _: None)
    assert healthy.calls == 1  # only the failed question was retried
    assert all(
        r.status == "ok" for r in latest_responses(out / "responses.jsonl").values()
    )


def test_placeholders_block_a_real_run(tmp_path: Path) -> None:
    path = tmp_path / "q.jsonl"
    row = question("si-1", "si", SI, is_placeholder=True)
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    with pytest.raises(SelectionError):
        select_questions(make_config(path))
    assert select_questions(make_config(path, allow_placeholders=True))


def test_scoring_and_report(benchmark: Path, tmp_path: Path) -> None:
    config = make_config(benchmark)
    qs = select_questions(config)
    root = tmp_path / "res"
    good = MockClient("good", replies={SI: "It is Kotte.", TA: "Kotte"})
    bad = MockClient("bad", replies={SI: "no idea", TA: "Kotte"})
    out = run_experiment(config, qs, [good, bad], root, run_id="r1")
    scores = score_run(out, load_questions(benchmark).questions)
    assert len(read_scores(out / "scores.jsonl")) == 4

    rows = summarise(scores)
    good_si = next(r for r in rows if r.model == "good" and r.language == "si")
    assert good_si.accuracy == 1.0
    bad_si = next(r for r in rows if r.model == "bad" and r.language == "si")
    assert bad_si.accuracy == 0.0 and bad_si.n_needs_human == 1

    pairs, only_good, only_bad, _ = paired_comparison(scores, "good", "bad")
    assert (pairs, only_good, only_bad) == (2, 1, 0)
    acc_si, acc_ta, _ = language_gap(scores, "bad")
    assert (acc_si, acc_ta) == (0.0, 1.0)


def test_text_helpers() -> None:
    assert normalise("  Kotte!!  ") == "kotte"
    assert reference_match("Kotte", "The capital is KOTTE.")
    assert is_refusal("I'm sorry, I can't help with that", Language.SINHALA)
    assert not is_refusal("Sure, here you go", Language.TAMIL)


def test_config_loader(tmp_path: Path) -> None:
    path = tmp_path / "c.toml"
    path.write_text(
        '[experiment]\nname="x"\nbenchmark="b.jsonl"\nlimit=5\n'
        '[[models]]\nname="m"\nprovider="mock"\n',
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg.name == "x" and cfg.limit == 5 and cfg.max_retries == 3
