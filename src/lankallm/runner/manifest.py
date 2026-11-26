"""Run manifest: everything needed to repeat or audit an experiment."""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from lankallm.runner.config import RunConfig
from lankallm.runner.prompts import PROMPTS


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip() or None


def _version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def build_manifest(
    config: RunConfig, run_id: str, benchmark_path: Path, n_questions: int
) -> dict[str, Any]:
    sha = hashlib.sha256(benchmark_path.read_bytes()).hexdigest()
    safe_models = [
        {k: v for k, v in m.items() if "key" not in k.lower()} for m in config.models
    ]
    return {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_commit(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {p: _version(p) for p in ("lankallm", "httpx", "pydantic")},
        "benchmark_file": str(benchmark_path),
        "benchmark_sha256": sha,
        "n_questions": n_questions,
        "prompt_version": config.prompt_version,
        "prompt_template": PROMPTS.get(config.prompt_version),
        "seed": config.seed,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "max_retries": config.max_retries,
        "models": safe_models,
    }
