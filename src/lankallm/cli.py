"""Command-line interface: ``lankallm ...`` (works without the web app)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from lankallm.benchmark import balance_table, check_questions, load_questions
from lankallm.evaluation import (
    language_gap,
    paired_comparison,
    read_scores,
    score_run,
    summarise,
    write_summary_csv,
)
from lankallm.models import build_client
from lankallm.runner import (
    SelectionError,
    load_config,
    run_experiment,
    select_questions,
)

app = typer.Typer(help="LankaLLM benchmark and evaluation tools.", no_args_is_help=True)
benchmark_app = typer.Typer(help="Benchmark data tools.", no_args_is_help=True)
app.add_typer(benchmark_app, name="benchmark")


@benchmark_app.command("validate")
def validate(
    path: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    allow_placeholders: Annotated[
        bool, typer.Option(help="Do not fail on items marked is_placeholder.")
    ] = False,
) -> None:
    """Check a benchmark JSONL file and report every problem found."""
    loaded = load_questions(path)
    problems = list(loaded.issues)
    quality = check_questions(loaded.questions)
    if allow_placeholders:
        quality = [i for i in quality if not i.message.startswith("placeholder")]

    for issue in problems:
        typer.echo(f"line {issue.line}: {issue.message}")
    for item in quality:
        typer.echo(f"{item.question_id}: {item.message}")

    typer.echo(f"\n{len(loaded.questions)} valid question(s) read from {path}")
    typer.echo("\nBalance (category: si / ta)")
    for category, counts in balance_table(loaded.questions).items():
        values = list(counts.values())
        typer.echo(f"  {category.value:<24} {values[0]:>3} / {values[1]:>3}")

    if problems or quality:
        typer.echo(f"\n{len(problems) + len(quality)} issue(s) found.")
        raise typer.Exit(code=1)
    typer.echo("\nNo issues found.")


RESULTS_ROOT = Path("data/results")


@app.command("run")
def run(
    config_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    resume: Annotated[str | None, typer.Option(help="Run ID to resume.")] = None,
    results_root: Annotated[Path, typer.Option()] = RESULTS_ROOT,
) -> None:
    """Run every selected question through every model in the config."""
    config = load_config(config_path)
    try:
        questions = select_questions(config)
        clients = [build_client(spec) for spec in config.models]
    except (SelectionError, ValueError) as exc:
        typer.echo(f"error: {exc}")
        raise typer.Exit(code=1) from exc
    typer.echo(f"{len(questions)} question(s) x {len(clients)} model(s)")
    out_dir = run_experiment(config, questions, clients, results_root, run_id=resume)
    typer.echo(f"saved to {out_dir}")


@app.command("score")
def score(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    benchmark: Annotated[Path, typer.Option(exists=True, dir_okay=False)],
) -> None:
    """Score a finished run and write scores.jsonl."""
    loaded = load_questions(benchmark)
    scores = score_run(run_dir, loaded.questions)
    human = sum(s.needs_human for s in scores)
    typer.echo(f"{len(scores)} response(s) scored, {human} flagged for human review")


@app.command("report")
def report(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
) -> None:
    """Print per-model results with confidence intervals and write summary.csv."""
    scores = read_scores(run_dir / "scores.jsonl")
    rows = summarise(scores)
    write_summary_csv(rows, run_dir / "summary.csv")
    typer.echo("model | lang | category | n | failed | acc [95% CI]")
    for r in rows:
        acc = "n/a" if r.accuracy is None else f"{r.accuracy:.2f}"
        ci = "" if r.ci_low is None else f" [{r.ci_low:.2f}, {r.ci_high:.2f}]"
        typer.echo(
            f"{r.model} | {r.language} | {r.category} | {r.n_scored}/{r.n_total} | "
            f"{r.n_failed} | {acc}{ci}"
        )
    models = sorted({s.model for s in scores})
    for i, a in enumerate(models):
        for b in models[i + 1 :]:
            pairs, only_a, only_b, p = paired_comparison(scores, a, b)
            typer.echo(
                f"\n{a} vs {b}: {pairs} pairs, {only_a}/{only_b} discordant, p={p:.3f}"
            )
    for m in models:
        si, ta, p = language_gap(scores, m)
        if si is not None and ta is not None:
            typer.echo(f"{m}: Sinhala {si:.2f} vs Tamil {ta:.2f}, p={p:.3f}")
    typer.echo(f"\nwrote {run_dir / 'summary.csv'}")


if __name__ == "__main__":
    app()
