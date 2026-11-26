# Runbook: running an evaluation (Project A)

All commands are run from the repo root (PowerShell).

## 1. Install

```powershell
uv sync --all-groups
Copy-Item .env.example .env      # then add any API keys to .env
```

## 2. Validate the benchmark

```powershell
uv run lankallm benchmark validate data/benchmark/v0.1/questions.jsonl
```

## 3. Configure an experiment

Copy `experiments/configs/pilot.example.toml` to `pilot.toml` and edit the models.
Never put keys in the file: use `api_key_env = "NAME_OF_ENV_VAR"`.

## 4. Run (pilot first, then the full set)

```powershell
uv run lankallm run experiments/configs/pilot.toml
uv run lankallm run experiments/configs/pilot.toml --resume <run_id>   # continue after a crash
```

Results go to `data/results/<run_id>/` (git-ignored): `manifest.json`, `responses.jsonl`.
Failed requests are saved with `status = "failed"`; a resume retries only those.

## 5. Score and report

```powershell
uv run lankallm score data/results/<run_id> --benchmark data/benchmark/v0.1/questions.jsonl
uv run lankallm report data/results/<run_id>
```

`score` writes `scores.jsonl`; items flagged `needs_human` go to the human-scoring queue.
`report` prints accuracy with 95% Wilson intervals, a paired McNemar test between models,
a Sinhala-vs-Tamil test per model, and writes `summary.csv`.

## 6. Dashboard

```powershell
uv run uvicorn app.main:app --app-dir backend --reload
```

Open http://127.0.0.1:8000. Set `LANKALLM_RESULTS` to read a different results folder.

## Rules that protect the results

- Scoring rules are fixed before the final run, never after seeing results.
- Do not run or tune on the private test split while developing.
- Add a new prompt version in `runner/prompts.py` instead of editing a released one.
