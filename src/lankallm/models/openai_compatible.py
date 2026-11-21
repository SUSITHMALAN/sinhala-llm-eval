"""Client for any OpenAI-compatible /chat/completions endpoint.

One class covers many free options: Ollama (local), Groq, OpenRouter, the Gemini
OpenAI-compatible endpoint, and others. Check each provider's current free-tier
limits and base URL before relying on it.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from lankallm.models.base import ModelError, ModelResponse


class OpenAICompatibleClient:
    def __init__(
        self,
        name: str,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 60.0,
        price_per_1k_input: float = 0.0,
        price_per_1k_output: float = 0.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.price_in = price_per_1k_input
        self.price_out = price_per_1k_output
        self._http = http_client or httpx.Client(timeout=timeout)

    def generate(
        self, prompt: str, *, temperature: float, max_tokens: int, seed: int | None
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        start = time.perf_counter()
        try:
            reply = self._http.post(
                f"{self.base_url}/chat/completions", json=payload, headers=headers
            )
            reply.raise_for_status()
            data: dict[str, Any] = reply.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelError(f"{type(exc).__name__}: {exc}") from exc
        latency = time.perf_counter() - start

        try:
            text = str(data["choices"][0]["message"]["content"] or "")
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("unexpected response shape") from exc

        usage: dict[str, Any] = data.get("usage") or {}
        tokens_in = usage.get("prompt_tokens")
        tokens_out = usage.get("completion_tokens")
        cost = None
        if isinstance(tokens_in, int) and isinstance(tokens_out, int):
            cost = tokens_in / 1000 * self.price_in + tokens_out / 1000 * self.price_out
        return ModelResponse(
            text=text,
            latency_s=latency,
            input_tokens=tokens_in if isinstance(tokens_in, int) else None,
            output_tokens=tokens_out if isinstance(tokens_out, int) else None,
            cost_usd=cost,
            model_version=str(data.get("model") or self.model),
        )
