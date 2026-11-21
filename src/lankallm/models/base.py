"""The one interface every model provider must implement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelResponse:
    text: str
    latency_s: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    model_version: str | None = None


class ModelError(Exception):
    """A provider call failed. The runner retries, then records the failure."""


class ModelClient(Protocol):
    name: str

    def generate(
        self, prompt: str, *, temperature: float, max_tokens: int, seed: int | None
    ) -> ModelResponse: ...
