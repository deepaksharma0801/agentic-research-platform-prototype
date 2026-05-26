from __future__ import annotations

import hashlib
import math
import re

from openai import OpenAI

from .config import get_settings
from .db import Paper, papers_missing_embeddings, session_scope


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def get_openai_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for embeddings and summaries.")
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts_local(texts: list[str]) -> list[list[float]]:
    """Create dependency-free semantic-ish vectors for local prototype runs."""
    dimensions = get_settings().embedding_dimensions
    vectors: list[list[float]] = []
    for text in texts:
        vector = [0.0] * dimensions
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        vectors.append([value / norm for value in vector] if norm else vector)
    return vectors


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using OpenAI or the local prototype fallback."""
    settings = get_settings()
    if settings.embedding_provider == "local":
        return embed_texts_local(texts)
    client = get_openai_client()
    response = client.embeddings.create(model=settings.openai_embedding_model, input=texts)
    return [item.embedding for item in response.data]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]


def embed_unembedded_papers(limit: int = 100) -> int:
    """Find papers without vectors, embed abstracts, and persist vectors to pgvector."""
    with session_scope() as session:
        papers: list[Paper] = list(papers_missing_embeddings(session, limit=limit))
        if not papers:
            return 0

        embeddings = embed_texts([paper.abstract or "" for paper in papers])
        for paper, embedding in zip(papers, embeddings):
            paper.embedding = embedding
        return len(papers)
