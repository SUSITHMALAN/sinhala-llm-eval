from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    run = tmp_path / "run1"
    run.mkdir()
    (run / "manifest.json").write_text(json.dumps({"run_id": "run1"}), encoding="utf-8")
    score = {
        "run_id": "run1",
        "model": "m",
        "question_id": "q1",
        "language": "si",
        "category": "factual",
        "method": "reference_match",
        "status": "ok",
        "score": 1.0,
        "needs_human": False,
    }
    (run / "scores.jsonl").write_text(json.dumps(score) + "\n", encoding="utf-8")
    monkeypatch.setenv("LANKALLM_RESULTS", str(tmp_path))
    return TestClient(app)


def test_lists_runs_and_summary(client: TestClient) -> None:
    assert client.get("/api/runs").json() == ["run1"]
    rows = client.get("/api/runs/run1/summary").json()
    assert rows[0]["accuracy"] == 1.0
    assert client.get("/api/runs/run1/summary.csv").status_code == 200


def test_unknown_run_and_path_tricks_are_404(client: TestClient) -> None:
    assert client.get("/api/runs/nope/summary").status_code == 404
    assert client.get("/api/runs/..%2F..%2Fetc/summary").status_code == 404


def test_dashboard_page_is_served(client: TestClient) -> None:
    assert "LankaLLM results" in client.get("/").text
