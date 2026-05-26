from __future__ import annotations

from typing import Any, Iterable
from urllib.parse import quote

import requests

from .config import get_settings
from .db import Paper, init_db, session_scope, upsert_paper


OPENALEX_WORKS_URL = "https://api.openalex.org/works"


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """OpenAlex stores abstracts as word -> positions; restore readable text."""
    if not inverted_index:
        return None
    positioned_words: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        positioned_words.extend((position, word) for position in positions)
    positioned_words.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned_words)


def fetch_openalex_works(query: str, limit: int = 25) -> list[dict[str, Any]]:
    settings = get_settings()
    params: dict[str, Any] = {
        "search": query,
        "per-page": min(limit, 200),
        "filter": "is_oa:true",
        "select": ",".join(
            [
                "id",
                "doi",
                "title",
                "abstract_inverted_index",
                "authorships",
                "publication_year",
                "referenced_works",
            ]
        ),
    }
    if settings.openalex_email:
        params["mailto"] = settings.openalex_email

    response = requests.get(OPENALEX_WORKS_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])[:limit]


def fetch_openalex_work(openalex_id: str) -> dict[str, Any] | None:
    """Fetch one OpenAlex work by URL or compact ID, returning None if absent."""
    compact_id = openalex_id.rstrip("/").split("/")[-1]
    response = requests.get(
        f"{OPENALEX_WORKS_URL}/{quote(compact_id)}",
        params={"mailto": get_settings().openalex_email} if get_settings().openalex_email else None,
        timeout=30,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def normalize_openalex_work(work: dict[str, Any]) -> dict[str, Any]:
    authors = [
        authorship.get("author", {}).get("display_name")
        for authorship in work.get("authorships", [])
        if authorship.get("author", {}).get("display_name")
    ]
    return {
        "openalex_id": work["id"],
        "doi": work.get("doi"),
        "title": work.get("title") or "Untitled paper",
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "authors": authors,
        "year": work.get("publication_year"),
        "referenced_openalex_ids": work.get("referenced_works") or [],
    }


def ingest_openalex(query: str, limit: int = 25) -> list[Paper]:
    """Download OpenAlex papers, store metadata in Postgres, and return rows."""
    init_db()
    works = fetch_openalex_works(query=query, limit=limit)
    with session_scope() as session:
        papers = [upsert_paper(session, normalize_openalex_work(work)) for work in works]
        session.flush()
        for paper in papers:
            session.refresh(paper)
        return papers


def ingest_openalex_ids(openalex_ids: Iterable[str]) -> list[Paper]:
    """Hydrate known OpenAlex IDs into local Postgres metadata where available."""
    init_db()
    works = [
        work
        for openalex_id in openalex_ids
        if (work := fetch_openalex_work(openalex_id)) is not None
    ]
    with session_scope() as session:
        papers = [upsert_paper(session, normalize_openalex_work(work)) for work in works]
        session.flush()
        for paper in papers:
            session.refresh(paper)
        return papers


def paper_graph_payloads(papers: Iterable[Paper]) -> list[dict[str, Any]]:
    """Convert ORM rows into a graph-friendly payload before the session closes."""
    return [
        {
            "openalex_id": paper.openalex_id,
            "title": paper.title,
            "year": paper.year,
            "referenced_openalex_ids": paper.referenced_openalex_ids or [],
        }
        for paper in papers
    ]
