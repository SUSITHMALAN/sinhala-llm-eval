# Contributing

LankaLLM is developed by a two-person team with complementary responsibilities.

## Responsibilities

- **Data Science:** benchmark design, sourcing and licensing evidence, Sinhala
  and Tamil annotation, annotation guidelines, adjudication, metric selection,
  statistical analysis, and interpretation of results.
- **AI Engineering:** package and service architecture, model clients, experiment
  execution, reproducibility manifests, API, dashboard, CI, and deployment
  tooling.
- **Shared ownership:** review benchmark changes for leakage and ambiguity,
  review experiment methodology, and document decisions that affect reported
  results.

These are default areas of focus, not barriers to cross-review.

## Development workflow

1. Use a focused branch and a pull request for changes.
2. Keep benchmark records and experiment configurations versioned and reviewable.
   Never commit credentials or private held-out examples.
3. Before opening a pull request, run:

   ```powershell
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src
   uv run pytest
   ```

4. Describe data provenance, prompt/model versions, and methodology changes when
   applicable. Update the experiment log for decisions that affect results.
5. Sinhala and Tamil benchmark content requires review by fluent annotators;
   machine-generated examples remain explicitly marked as placeholders until
   reviewed and adjudicated.

## Research integrity

Do not tune prompts or model configurations against the held-out test split.
Report benchmark and prompt versions, model identifiers, seeds, and relevant
runtime details. Preserve failed and incomplete responses in experiment output
and report them rather than removing them from denominators without explanation.
