from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from .db import Paper, init_db, session_scope
from .embeddings import embed_query
from .graph import CitationGraph


@dataclass
class RetrievedPaper:
    source: str
    openalex_id: str
    title: str
    abstract: str | None
    authors: list[str]
    year: int | None
    distance: float | None = None


def semantic_search(query: str, top_k: int = 5) -> list[RetrievedPaper]:
    """Embed a user query and rank papers by cosine distance in pgvector."""
    init_db()
    query_embedding = embed_query(query)
    with session_scope() as session:
        distance = Paper.embedding.cosine_distance(query_embedding).label("distance")
        rows = session.execute(
            select(
                Paper.openalex_id,
                Paper.title,
                Paper.abstract,
                Paper.authors,
                Paper.year,
                distance,
            )
            .where(Paper.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
        ).mappings()
        return [
            RetrievedPaper(
                source="semantic",
                openalex_id=row["openalex_id"],
                title=row["title"],
                abstract=row["abstract"],
                authors=list(row["authors"] or []),
                year=row["year"],
                distance=float(row["distance"]),
            )
            for row in rows
        ]


def hydrate_related_metadata(related_graph_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = [row["openalex_id"] for row in related_graph_rows]
    if not ids:
        return []
    graph_by_id = {row["openalex_id"]: row for row in related_graph_rows}
    with session_scope() as session:
        papers = session.query(Paper).filter(Paper.openalex_id.in_(ids)).all()
        hydrated = [
                {
                    "source": "citation",
                    "openalex_id": paper.openalex_id,
                    "title": paper.title,
                "abstract": paper.abstract,
                "authors": paper.authors or [],
                "year": paper.year,
            }
            for paper in papers
        ]
    known_ids = {paper["openalex_id"] for paper in hydrated}
    for openalex_id, row in graph_by_id.items():
        if openalex_id not in known_ids:
            hydrated.append(
                {
                    "source": "citation",
                    "openalex_id": openalex_id,
                    "title": row.get("title") or openalex_id,
                    "abstract": None,
                    "authors": [],
                    "year": row.get("year"),
                }
            )
    return hydrated


def retrieve(query: str, top_k: int = 5) -> dict[str, Any]:
    papers = semantic_search(query, top_k=top_k)
    graph = CitationGraph()
    try:
        related = graph.related_papers([paper.openalex_id for paper in papers], limit=top_k * 3)
    finally:
        graph.close()

    return {
        "papers": [paper.__dict__ for paper in papers],
        "related_papers": hydrate_related_metadata(related),
    }
