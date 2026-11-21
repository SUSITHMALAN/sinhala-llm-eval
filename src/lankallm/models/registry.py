"""Build model clients from the [[models]] tables of an experiment config."""

from __future__ import annotations

import os
from typing import Any

from lankallm.models.base import ModelClient
from lankallm.models.mock import MockClient
from lankallm.models.openai_compatible import OpenAICompatibleClient


def build_client(spec: dict[str, Any]) -> ModelClient:
    provider = spec.get("provider")
    name = str(spec["name"])
    if provider == "mock":
        return MockClient(name=name)
    if provider == "openai_compatible":
        key_env = spec.get("api_key_env")
        api_key = os.environ.get(str(key_env)) if key_env else None
        if key_env and not api_key:
            raise ValueError(f"environment variable {key_env} is not set")
        return OpenAICompatibleClient(
            name=name,
            base_url=str(spec["base_url"]),
            model=str(spec["model"]),
            api_key=api_key,
            price_per_1k_input=float(spec.get("price_per_1k_input", 0.0)),
            price_per_1k_output=float(spec.get("price_per_1k_output", 0.0)),
        )
    raise ValueError(f"unknown provider {provider!r} for model {name!r}")
