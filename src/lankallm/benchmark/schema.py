"""Benchmark question schema.

This is the single source of truth for what a benchmark question looks like.
Field names follow docs/annotation_guidelines.md. Any change to this file is a
change to the benchmark format and must be agreed with the data lead.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Language(StrEnum):
    SINHALA = "si"
    TAMIL = "ta"


class Category(StrEnum):
    FACTUAL = "factual"
    HALLUCINATION = "hallucination"
    BIAS = "bias"
    SAFETY = "safety"
    LANGUAGE_UNDERSTANDING = "language_understanding"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    DIFFICULT = "difficult"


class EvaluationMethod(StrEnum):
    """How a response to this question is judged."""

    REFERENCE_MATCH = "reference_match"  # compare against expected_answer
    PREMISE_CHECK = "premise_check"  # model must correct a false premise / abstain
    REFUSAL_CHECK = "refusal_check"  # model must refuse or redirect
    HUMAN_RUBRIC = "human_rubric"  # human scores against the guideline


class Split(StrEnum):
    DEV = "dev"
    TEST = "test"


class Question(BaseModel):
    """One benchmark item (one line of a JSONL file)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str = Field(min_length=1)
    language: Language
    category: Category
    subcategory: str | None = None
    question: str = Field(min_length=1)
    expected_answer: str | None = None
    evidence: str | None = None
    difficulty: Difficulty
    evaluation_method: EvaluationMethod
    split: Split = Split.DEV
    benchmark_version: str = Field(min_length=1)
    annotator_ids: list[str] = Field(default_factory=list)
    is_placeholder: bool = False
    notes: str | None = None
