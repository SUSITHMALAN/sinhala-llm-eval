"""Choose which benchmark questions an experiment will run."""

from __future__ import annotations

from lankallm.benchmark import Question, check_questions, load_questions
from lankallm.runner.config import RunConfig


class SelectionError(Exception):
    """The benchmark file is not fit to run."""


def select_questions(config: RunConfig) -> list[Question]:
    loaded = load_questions(config.benchmark)
    if loaded.issues:
        first = loaded.issues[0]
        raise SelectionError(
            f"{len(loaded.issues)} problem(s) in {config.benchmark}, "
            f"first: line {first.line}: {first.message}. "
            "Run `lankallm benchmark validate` for the full list."
        )
    problems = [
        i
        for i in check_questions(loaded.questions)
        if not (config.allow_placeholders and i.message.startswith("placeholder"))
    ]
    if problems:
        raise SelectionError(
            f"{len(problems)} quality problem(s), first: "
            f"{problems[0].question_id}: {problems[0].message}"
        )
    items = loaded.questions
    if config.split is not None:
        items = [q for q in items if q.split.value == config.split]
    if config.limit is not None:
        items = items[: config.limit]
    if not items:
        raise SelectionError("no questions selected (check split and limit)")
    return items
