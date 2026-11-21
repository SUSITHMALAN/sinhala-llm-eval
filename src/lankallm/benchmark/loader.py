"""Read benchmark JSONL files without stopping at the first bad line."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from lankallm.benchmark.schema import Question


@dataclass(frozen=True)
class LoadIssue:
    """A problem found while reading a file (reported with its line number)."""

    line: int
    message: str


@dataclass
class LoadResult:
    questions: list[Question] = field(default_factory=list)
    issues: list[LoadIssue] = field(default_factory=list)


def load_questions(path: Path) -> LoadResult:
    """Parse a UTF-8 JSONL file. Blank lines are ignored.

    Every malformed line becomes a ``LoadIssue``; nothing is dropped silently.
    """
    result = LoadResult()
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            text = raw.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                result.issues.append(LoadIssue(line_number, f"invalid JSON: {exc.msg}"))
                continue
            try:
                result.questions.append(Question.model_validate(payload))
            except ValidationError as exc:
                for error in exc.errors():
                    where = ".".join(str(part) for part in error["loc"]) or "<record>"
                    result.issues.append(
                        LoadIssue(line_number, f"{where}: {error['msg']}")
                    )
    return result
