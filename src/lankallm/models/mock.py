"""Offline model used for tests, dry runs and pilots without API keys."""

from __future__ import annotations

from lankallm.models.base import ModelError, ModelResponse


class MockClient:
    def __init__(
        self,
        name: str = "mock",
        replies: dict[str, str] | None = None,
        fail_first: int = 0,
    ) -> None:
        self.name = name
        self.replies = replies or {}
        self.fail_first = fail_first
        self.calls = 0

    def generate(
        self, prompt: str, *, temperature: float, max_tokens: int, seed: int | None
    ) -> ModelResponse:
        self.calls += 1
        if self.calls <= self.fail_first:
            raise ModelError("simulated provider failure")
        text = self.replies.get(prompt, "mock answer")
        return ModelResponse(
            text=text,
            latency_s=0.0,
            input_tokens=len(prompt.split()),
            output_tokens=len(text.split()),
            cost_usd=0.0,
            model_version="mock-1",
        )
