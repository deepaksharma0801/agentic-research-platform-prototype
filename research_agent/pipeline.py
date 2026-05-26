from __future__ import annotations

from typing import Any

from .embeddings import embed_unembedded_papers
from .graph import CitationGraph
from .ingestion import ingest_openalex, paper_graph_payloads
from .retrieval import retrieve
from .summarization import summarize


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


def answer_query(query: str, top_k: int = 5) -> dict[str, Any]:
    results = retrieve(query=query, top_k=top_k)
    summary = summarize(
        query=query,
        papers=results["papers"],
        related_papers=results["related_papers"],
    )
    return {"query": query, "summary": summary, **results}
