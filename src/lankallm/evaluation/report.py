"""Summaries and model/language comparisons built from scores."""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from lankallm.benchmark import Language
from lankallm.evaluation.scoring import Score
from lankallm.stats import mcnemar_exact, two_proportion_z, wilson_interval


@dataclass(frozen=True)
class SummaryRow:
    model: str
    language: str
    category: str
    n_total: int
    n_failed: int
    n_scored: int
    n_needs_human: int
    accuracy: float | None
    ci_low: float | None
    ci_high: float | None


def summarise(scores: Sequence[Score]) -> list[SummaryRow]:
    groups: dict[tuple[str, str, str], list[Score]] = defaultdict(list)
    for s in scores:
        groups[(s.model, s.language.value, s.category.value)].append(s)
    rows: list[SummaryRow] = []
    for (model, language, category), items in sorted(groups.items()):
        scored = [s.score for s in items if s.score is not None]
        correct = int(sum(scored))
        low = high = accuracy = None
        if scored:
            accuracy = correct / len(scored)
            low, high = wilson_interval(correct, len(scored))
        rows.append(
            SummaryRow(
                model=model,
                language=language,
                category=category,
                n_total=len(items),
                n_failed=sum(s.status == "failed" for s in items),
                n_scored=len(scored),
                n_needs_human=sum(s.needs_human for s in items),
                accuracy=accuracy,
                ci_low=low,
                ci_high=high,
            )
        )
    return rows


def write_summary_csv(rows: Sequence[SummaryRow], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(asdict(rows[0])) if rows else []
        )
        if rows:
            writer.writeheader()
            writer.writerows(asdict(r) for r in rows)


def paired_comparison(
    scores: Sequence[Score], model_a: str, model_b: str
) -> tuple[int, int, int, float]:
    """McNemar test on questions both models were scored on.

    Returns (n_pairs, only_a_right, only_b_right, p_value).
    """
    a = {s.question_id: s.score for s in scores if s.model == model_a}
    b = {s.question_id: s.score for s in scores if s.model == model_b}
    only_a = only_b = pairs = 0
    for qid, sa in a.items():
        sb = b.get(qid)
        if sa is None or sb is None:
            continue
        pairs += 1
        only_a += int(sa == 1.0 and sb == 0.0)
        only_b += int(sa == 0.0 and sb == 1.0)
    return pairs, only_a, only_b, mcnemar_exact(only_a, only_b)


def language_gap(
    scores: Sequence[Score], model: str
) -> tuple[float | None, float | None, float]:
    """Sinhala vs Tamil accuracy for one model -> (acc_si, acc_ta, p_value)."""
    si = [
        s.score for s in scores if s.model == model and s.language is Language.SINHALA
    ]
    ta = [s.score for s in scores if s.model == model and s.language is Language.TAMIL]
    si_ok = [v for v in si if v is not None]
    ta_ok = [v for v in ta if v is not None]
    if not si_ok or not ta_ok:
        return None, None, 1.0
    _, p = two_proportion_z(int(sum(si_ok)), len(si_ok), int(sum(ta_ok)), len(ta_ok))
    return sum(si_ok) / len(si_ok), sum(ta_ok) / len(ta_ok), p
