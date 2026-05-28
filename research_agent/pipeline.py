from __future__ import annotations

from typing import Any

from .config import get_settings
from .db import corpus_stats
from .embeddings import embed_unembedded_papers
from .graph import CitationGraph
from .ingestion import ingest_openalex, ingest_openalex_ids, paper_graph_payloads
from .retrieval import retrieve
from .summarization import summarize


DEMO_TOPICS = [
    "machine learning in healthcare",
    "transformers biomedicine healthcare",
    "federated learning clinical applications",
]


def ingest_pipeline(query: str, limit: int = 25) -> dict[str, int]:
    """Run metadata ingestion, graph creation, and embedding generation."""
    papers = ingest_openalex(query=query, limit=limit)
    graph_payloads = paper_graph_payloads(papers)

    graph = CitationGraph()
    try:
        graph.upsert_papers_and_citations(graph_payloads)
    finally:
        graph.close()

    embedded_count = embed_unembedded_papers(limit=limit)
    return {"papers_ingested": len(papers), "papers_embedded": embedded_count}


def ingest_demo_pipeline(limit_per_topic: int = 15) -> dict[str, Any]:
    """Seed a portfolio-friendly demo corpus across several research topics."""
    totals = {"topics": DEMO_TOPICS, "papers_ingested": 0, "papers_embedded": 0}
    for topic in DEMO_TOPICS:
        result = ingest_pipeline(query=topic, limit=limit_per_topic)
        totals["papers_ingested"] += result["papers_ingested"]
        totals["papers_embedded"] += result["papers_embedded"]
    hydrated = hydrate_citation_metadata(limit=50)
    totals["citation_papers_hydrated"] = hydrated["papers_hydrated"]
    return totals


def hydrate_citation_metadata(limit: int = 50) -> dict[str, int]:
    """Fetch metadata for citation graph IDs that are missing local details."""
    graph = CitationGraph()
    try:
        ids = graph.unhydrated_paper_ids(limit=limit)
    finally:
        graph.close()

    if not ids:
        return {"candidate_ids": 0, "papers_hydrated": 0, "papers_embedded": 0}

    papers = ingest_openalex_ids(ids)
    graph_payloads = paper_graph_payloads(papers)
    graph = CitationGraph()
    try:
        graph.upsert_papers_and_citations(graph_payloads)
    finally:
        graph.close()

    return {
        "candidate_ids": len(ids),
        "papers_hydrated": len(papers),
        "papers_embedded": embed_unembedded_papers(limit=len(papers)),
    }


def dashboard_stats() -> dict[str, Any]:
    """Summarize database, graph, vector, and model provider state."""
    graph = CitationGraph()
    try:
        graph_counts = graph.graph_stats()
    finally:
        graph.close()

    settings = get_settings()
    return {
        "corpus": corpus_stats(),
        "graph": graph_counts,
        "providers": {
            "embedding": settings.embedding_provider,
            "summary": settings.summary_provider,
        },
        "services": {
            "postgres": "connected",
            "pgvector": "enabled",
            "neo4j": "connected",
        },
    }


def answer_query(query: str, top_k: int = 5) -> dict[str, Any]:
    results = retrieve(query=query, top_k=top_k)
    summary = summarize(
        query=query,
        papers=results["papers"],
        related_papers=results["related_papers"],
    )
    settings = get_settings()
    return build_query_response(
        query=query,
        summary=summary,
        results=results,
        embedding_provider=settings.embedding_provider,
        summary_provider=settings.summary_provider,
    )


def build_query_response(
    query: str,
    summary: str,
    results: dict[str, Any],
    embedding_provider: str,
    summary_provider: str,
) -> dict[str, Any]:
    """Shape retrieval output for CLI/API/UI consumers."""
    return {
        "query": query,
        "summary": summary,
        "providers": {
            "embedding": embedding_provider,
            "summary": summary_provider,
        },
        "counts": {
            "papers": len(results["papers"]),
            "related_papers": len(results["related_papers"]),
        },
        **results,
    }
