"""Quality checks that go beyond per-field schema validation."""

from __future__ import annotations

import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from lankallm.benchmark.schema import (
    Category,
    EvaluationMethod,
    Language,
    Question,
)

# Unicode blocks: Sinhala U+0D80-0DFF, Tamil U+0B80-0BFF.
_SCRIPT_RANGES: dict[Language, tuple[int, int]] = {
    Language.SINHALA: (0x0D80, 0x0DFF),
    Language.TAMIL: (0x0B80, 0x0BFF),
}

# A question tagged with a language should be mostly written in that script.
# Code-mixed questions legitimately contain Latin text, so the bar is low.
MIN_SCRIPT_RATIO = 0.3


@dataclass(frozen=True)
class Issue:
    question_id: str
    message: str


def script_ratio(text: str, language: Language) -> float:
    """Share of letters in ``text`` that belong to the language's script."""
    low, high = _SCRIPT_RANGES[language]
    letters = [ch for ch in text if unicodedata.category(ch).startswith(("L", "M"))]
    if not letters:
        return 0.0
    return sum(low <= ord(ch) <= high for ch in letters) / len(letters)


def check_questions(questions: Iterable[Question]) -> list[Issue]:
    """Return every quality problem found in a set of questions."""
    items = list(questions)
    issues: list[Issue] = []

    for question_id, count in Counter(q.question_id for q in items).items():
        if count > 1:
            issues.append(Issue(question_id, f"duplicate question_id ({count} times)"))

    for q in items:
        if unicodedata.normalize("NFC", q.question) != q.question:
            issues.append(Issue(q.question_id, "question text is not NFC-normalised"))

        if script_ratio(q.question, q.language) < MIN_SCRIPT_RATIO:
            issues.append(
                Issue(
                    q.question_id,
                    f"question text does not look like language '{q.language}'",
                )
            )

        if q.category is Category.FACTUAL and not (q.expected_answer and q.evidence):
            issues.append(
                Issue(
                    q.question_id, "factual question needs expected_answer and evidence"
                )
            )

        if q.evaluation_method is EvaluationMethod.REFERENCE_MATCH and not (
            q.expected_answer
        ):
            issues.append(
                Issue(q.question_id, "reference_match needs an expected_answer")
            )

        if q.is_placeholder:
            issues.append(
                Issue(q.question_id, "placeholder: exclude from research claims")
            )

    return issues


def balance_table(
    questions: Iterable[Question],
) -> dict[Category, dict[Language, int]]:
    """Count questions per category and language (Sinhala/Tamil should match)."""
    table: dict[Category, dict[Language, int]] = {
        category: {language: 0 for language in Language} for category in Category
    }
    for q in questions:
        table[q.category][q.language] += 1
    return table
