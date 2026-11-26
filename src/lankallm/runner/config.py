"""Experiment configuration, loaded from a TOML file."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunConfig:
    name: str
    benchmark: Path
    prompt_version: str
    seed: int
    temperature: float
    max_tokens: int
    max_retries: int
    split: str | None
    limit: int | None
    allow_placeholders: bool
    models: list[dict[str, Any]]
    raw: dict[str, Any]


def load_config(path: Path) -> RunConfig:
    with path.open("rb") as handle:
        raw: dict[str, Any] = tomllib.load(handle)
    exp: dict[str, Any] = raw["experiment"]
    models: list[dict[str, Any]] = raw["models"]
    if not models:
        raise ValueError("config needs at least one [[models]] table")
    return RunConfig(
        name=str(exp["name"]),
        benchmark=Path(str(exp["benchmark"])),
        prompt_version=str(exp.get("prompt_version", "p1")),
        seed=int(exp.get("seed", 42)),
        temperature=float(exp.get("temperature", 0.0)),
        max_tokens=int(exp.get("max_tokens", 512)),
        max_retries=int(exp.get("max_retries", 3)),
        split=str(exp["split"]) if "split" in exp else None,
        limit=int(exp["limit"]) if "limit" in exp else None,
        allow_placeholders=bool(exp.get("allow_placeholders", False)),
        models=models,
        raw=raw,
    )
