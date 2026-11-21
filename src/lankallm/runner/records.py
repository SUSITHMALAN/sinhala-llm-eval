"""On-disk record for one model response (one line of responses.jsonl)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from lankallm.benchmark import Category, Language


class ResponseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    model: str
    question_id: str
    language: Language
    category: Category
    prompt: str
    response: str | None
    status: Literal["ok", "failed"]
    error: str | None = None
    attempts: int
    latency_s: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    model_version: str | None = None
    timestamp: str


def read_responses(path: Path) -> Iterator[ResponseRecord]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield ResponseRecord.model_validate_json(line)


def latest_responses(path: Path) -> dict[tuple[str, str], ResponseRecord]:
    """Newest record per (model, question_id); a retry after a failure wins."""
    latest: dict[tuple[str, str], ResponseRecord] = {}
    for record in read_responses(path):
        latest[(record.model, record.question_id)] = record
    return latest
