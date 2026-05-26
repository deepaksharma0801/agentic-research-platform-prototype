from __future__ import annotations

from typing import Any

from .config import get_settings
from .embeddings import get_openai_client


def _format_paper(paper: dict[str, Any]) -> str:
    authors = ", ".join(paper.get("authors") or [])
    abstract = paper.get("abstract") or "No abstract available."
    return (
        f"Title: {paper.get('title')}\n"
        f"Year: {paper.get('year')}\n"
        f"Authors: {authors or 'Unknown'}\n"
        f"Abstract: {abstract[:1200]}"
    )


def summarize(query: str, papers: list[dict[str, Any]], related_papers: list[dict[str, Any]]) -> str:
    """Ask an LLM to synthesize retrieved papers into a compact answer."""
    settings = get_settings()
    if settings.summary_provider == "local":
        return summarize_local(query=query, papers=papers, related_papers=related_papers)

    client = get_openai_client()
    context = "\n\n---\n\n".join(
        [_format_paper(paper) for paper in papers]
        + [_format_paper(paper) for paper in related_papers[:5]]
    )
    response = client.chat.completions.create(
        model=settings.openai_summary_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You summarize scientific search results. Be concise, cite papers by "
                    "title and year when possible, and clearly separate strong evidence "
                    "from tentative connections."
                ),
            },
            {
                "role": "user",
                "content": f"User query: {query}\n\nRetrieved paper context:\n{context}",
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def summarize_local(
    query: str, papers: list[dict[str, Any]], related_papers: list[dict[str, Any]]
) -> str:
    """Generate a simple extractive summary when no LLM quota is available."""
    if not papers:
        return f"No embedded papers were found for query: {query}"

    lines = [f"Local summary for query: {query}", ""]
    lines.append("Most relevant papers:")
    for paper in papers[:5]:
        title = paper.get("title") or "Untitled paper"
        year = paper.get("year") or "n.d."
        abstract = (paper.get("abstract") or "No abstract available.").strip()
        first_sentence = abstract.split(". ")[0][:350]
        lines.append(f"- {title} ({year}): {first_sentence}")

    if related_papers:
        lines.append("")
        lines.append("Citation-near related papers:")
        for paper in related_papers[:5]:
            title = paper.get("title") or paper.get("openalex_id") or "Unknown related paper"
            year = paper.get("year") or "n.d."
            lines.append(f"- {title} ({year})")

    return "\n".join(lines)
