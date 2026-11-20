# Architecture

## Project boundaries

`src/lankallm` is the standalone benchmark and evaluation package. It owns
benchmark data loading and validation, model client interfaces, experiment
execution, scoring, and statistical analysis. Its CLI must remain useful without
the web application.

`backend/app` is the HTTP and persistence boundary. FastAPI exposes benchmark
and experiment operations; SQLAlchemy and Alembic manage PostgreSQL persistence
and schema evolution. The backend should call the package rather than duplicate
evaluation logic.

`frontend` is a React, TypeScript, and Vite dashboard. It consumes the backend
API and must not contain model-provider credentials. Sinhala and Tamil text must
be preserved as UTF-8 and rendered with suitable fonts.

## Experiment data flow

Versioned benchmark records and experiment configuration feed the runner. The
runner invokes a registered model client and persists one result or explicit
failure per question. A manifest records the configuration, source revision,
seed, and software/model versions. Evaluation and statistical summaries are
derived from those stored outputs.

## Deferred capabilities

RAG ingestion, retrieval, citation handling, and PEFT/LoRA fine-tuning are
documented extension points only until a baseline evaluation pipeline has been
implemented and validated.
