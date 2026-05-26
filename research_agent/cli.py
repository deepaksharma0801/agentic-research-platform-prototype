from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.exc import OperationalError

from .db import init_db
from .pipeline import answer_query, hydrate_citation_metadata, ingest_demo_pipeline, ingest_pipeline


app = typer.Typer(help="Agentic AI Research Platform prototype")
console = Console()


def _explain_runtime_error(error: Exception) -> None:
    message = str(error)
    if isinstance(error, OperationalError) and "Connection refused" in message:
        console.print(
            "[red]Database connection failed.[/red] Start Docker Desktop, then run "
            "`docker compose up -d` from the project folder before this command."
        )
    elif "OPENAI_API_KEY" in message:
        console.print(
            "[red]OpenAI API key is missing.[/red] Add `OPENAI_API_KEY=...` to `.env`."
        )
    else:
        console.print(f"[red]Command failed:[/red] {error}")


@app.command()
def init() -> None:
    """Initialize Postgres tables, pgvector extension, and vector index."""
    try:
        init_db()
    except Exception as error:
        _explain_runtime_error(error)
        raise typer.Exit(1) from error
    console.print("[green]Database initialized.[/green]")


@app.command()
def ingest(
    query: str = typer.Option(..., "--query", "-q", help="OpenAlex search query"),
    limit: int = typer.Option(25, "--limit", "-n", help="Number of papers to ingest"),
) -> None:
    """Fetch OpenAlex papers, store metadata, create graph links, and embed abstracts."""
    try:
        result = ingest_pipeline(query=query, limit=limit)
    except Exception as error:
        _explain_runtime_error(error)
        raise typer.Exit(1) from error
    console.print_json(json.dumps(result))


@app.command("demo-seed")
def demo_seed(
    limit_per_topic: int = typer.Option(
        15, "--limit-per-topic", "-n", help="Papers to ingest for each demo topic"
    ),
) -> None:
    """Seed a useful demo corpus across healthcare AI topics."""
    try:
        result = ingest_demo_pipeline(limit_per_topic=limit_per_topic)
    except Exception as error:
        _explain_runtime_error(error)
        raise typer.Exit(1) from error
    console.print_json(json.dumps(result))


@app.command("hydrate-citations")
def hydrate_citations(
    limit: int = typer.Option(50, "--limit", "-n", help="Citation IDs to hydrate"),
) -> None:
    """Fetch OpenAlex metadata for citation graph nodes that only have IDs."""
    try:
        result = hydrate_citation_metadata(limit=limit)
    except Exception as error:
        _explain_runtime_error(error)
        raise typer.Exit(1) from error
    console.print_json(json.dumps(result))


@app.command("query")
def query_command(
    question: str = typer.Argument(..., help="Natural-language research question"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of vector hits"),
) -> None:
    """Run semantic retrieval, graph expansion, and LLM summarization."""
    try:
        result = answer_query(query=question, top_k=top_k)
    except Exception as error:
        _explain_runtime_error(error)
        raise typer.Exit(1) from error
    console.rule("Summary")
    console.print(result["summary"])

    table = Table(title="Retrieved papers")
    table.add_column("Year", justify="right")
    table.add_column("Title")
    table.add_column("Distance", justify="right")
    for paper in result["papers"]:
        table.add_row(
            str(paper.get("year") or ""),
            paper.get("title") or "",
            f"{paper.get('distance'):.4f}" if paper.get("distance") is not None else "",
        )
    console.print(table)


if __name__ == "__main__":
    app()
