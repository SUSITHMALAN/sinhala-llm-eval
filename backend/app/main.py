"""HTTP API over saved experiment results (the dashboard reads this)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lankallm.evaluation import read_scores, summarise, write_summary_csv

app = FastAPI(title="LankaLLM")
STATIC_DIR = Path(__file__).parent / "static"


def results_root() -> Path:
    return Path(os.environ.get("LANKALLM_RESULTS", "data/results"))


def run_dir(run_id: str) -> Path:
    # Reject anything that is not a plain folder name (blocks ../ path tricks).
    if run_id != Path(run_id).name or run_id in {"", ".", ".."}:
        raise HTTPException(status_code=404, detail="run not found")
    path = results_root() / run_id
    if not path.is_dir():
        raise HTTPException(status_code=404, detail="run not found")
    return path


@app.get("/api/runs")
def list_runs() -> list[str]:
    root = results_root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if (p / "manifest.json").exists())


@app.get("/api/runs/{run_id}/manifest")
def manifest(run_id: str) -> dict[str, Any]:
    path = run_dir(run_id) / "manifest.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="manifest not found")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


@app.get("/api/runs/{run_id}/summary")
def summary(run_id: str) -> list[dict[str, Any]]:
    path = run_dir(run_id) / "scores.jsonl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="run has not been scored yet")
    return [asdict(row) for row in summarise(read_scores(path))]


@app.get("/api/runs/{run_id}/summary.csv")
def summary_csv(run_id: str) -> FileResponse:
    directory = run_dir(run_id)
    scores = directory / "scores.jsonl"
    if not scores.exists():
        raise HTTPException(status_code=404, detail="run has not been scored yet")
    target = directory / "summary.csv"
    write_summary_csv(summarise(read_scores(scores)), target)
    return FileResponse(target, media_type="text/csv", filename=f"{run_id}-summary.csv")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
