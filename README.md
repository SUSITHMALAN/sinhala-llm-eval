# LankaLLM

LankaLLM is a research-first benchmark and evaluation platform for measuring
large language model reliability in Sinhala and Tamil. Its goals include factual
accuracy, hallucination, bias, safety, and language understanding. A RAG-based
chatbot is a later project phase; the benchmark and reproducible baseline come
first.

The evaluation core is designed as an installable Python package so benchmark
validation and experiments can run from a command line independently of the web
application.

## Project status

The repository is being built in reviewable stages. The current foundation
provides Python packaging, development tooling, CI, PostgreSQL for local
development, and project documentation. Benchmark validation, model execution,
evaluation, the API, and the dashboard will be added in subsequent stages.

All benchmark examples are placeholders for native Sinhala and Tamil review.
They must not be used as evidence of benchmark quality until that review and
adjudication are complete.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL (when using backend persistence)
- Node.js LTS (for the frontend when that stage is available)

## Setup

```powershell
uv sync --all-groups
Copy-Item .env.example .env
uv run pytest
```

The `lankallm` package uses a `src/` layout and is installed in editable mode by
`uv sync`. Configure `DATABASE_URL` in the local `.env` file for a separately
running PostgreSQL instance. API keys belong in environment variables or a local
`.env` file; never put credentials in source code or frontend configuration.

## Development commands

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the team workflow and role split.
Research design and annotation materials are in [docs/](docs/).

## Reproducibility principles

- Version benchmark data, prompts, model identifiers, and experiment configs.
- Record seeds and runtime/dependency versions with each experiment.
- Keep held-out test data private and out of Git.
- Store every question's response and record failures explicitly; do not silently
  omit failed examples.
- Treat automated or LLM-judge scores as supplementary unless independently
  validated.

## License

This project is distributed under the Apache License 2.0; see [LICENSE](LICENSE).
