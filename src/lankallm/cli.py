"""Command-line interface: ``lankallm ...`` (works without the web app)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from lankallm.benchmark import balance_table, check_questions, load_questions

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


if __name__ == "__main__":
    app()
