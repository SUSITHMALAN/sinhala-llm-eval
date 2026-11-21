"""Send every question to every model; save every result or failure."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from lankallm.benchmark import Question
from lankallm.models import ModelClient, ModelError
from lankallm.runner.config import RunConfig
from lankallm.runner.manifest import build_manifest
from lankallm.runner.prompts import render_prompt
from lankallm.runner.records import ResponseRecord, latest_responses


def _now() -> str:
    return datetime.now(UTC).isoformat()


def new_run_id(name: str) -> str:
    return f"{name}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}"


def _call_with_retries(
    client: ModelClient,
    question: Question,
    config: RunConfig,
    run_id: str,
    sleep: Callable[[float], None],
) -> ResponseRecord:
    prompt = render_prompt(config.prompt_version, question.question)
    base = {
        "run_id": run_id,
        "model": client.name,
        "question_id": question.question_id,
        "language": question.language,
        "category": question.category,
        "prompt": prompt,
    }
    error = ""
    for attempt in range(1, config.max_retries + 2):
        try:
            reply = client.generate(
                prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                seed=config.seed,
            )
        except ModelError as exc:
            error = str(exc)
            if attempt <= config.max_retries:
                sleep(min(2.0**attempt, 30.0))
            continue
        return ResponseRecord(
            **base,  # type: ignore[arg-type]
            response=reply.text,
            status="ok",
            attempts=attempt,
            latency_s=reply.latency_s,
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
            cost_usd=reply.cost_usd,
            model_version=reply.model_version,
            timestamp=_now(),
        )
    return ResponseRecord(
        **base,  # type: ignore[arg-type]
        response=None,
        status="failed",
        error=error,
        attempts=config.max_retries + 1,
        timestamp=_now(),
    )


def run_experiment(
    config: RunConfig,
    questions: Sequence[Question],
    clients: Sequence[ModelClient],
    results_root: Path,
    *,
    run_id: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Path:
    """Run (or resume) an experiment and return its output directory.

    Resuming skips (model, question) pairs that already succeeded and retries
    the ones that failed. Failures are saved, never dropped.
    """
    run_id = run_id or new_run_id(config.name)
    out_dir = results_root / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        manifest = build_manifest(config, run_id, config.benchmark, len(questions))
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    responses_path = out_dir / "responses.jsonl"
    done = {
        key
        for key, rec in latest_responses(responses_path).items()
        if rec.status == "ok"
    }
    with responses_path.open("a", encoding="utf-8") as handle:
        for client in clients:
            for question in questions:
                if (client.name, question.question_id) in done:
                    continue
                record = _call_with_retries(client, question, config, run_id, sleep)
                handle.write(record.model_dump_json() + "\n")
                handle.flush()
    return out_dir
