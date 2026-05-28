from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from neo4j.exceptions import Neo4jError
from openai import OpenAIError
from pydantic import BaseModel, Field
from sqlalchemy.exc import OperationalError

from .pipeline import (
    answer_query,
    dashboard_stats,
    hydrate_citation_metadata,
    ingest_demo_pipeline,
    ingest_pipeline,
)


app = FastAPI(title="Agentic AI Research Platform Prototype")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class IngestRequest(BaseModel):
    query: str = Field(..., examples=["machine learning in healthcare"])
    limit: int = Field(default=25, ge=1, le=200)


class QueryRequest(BaseModel):
    query: str = Field(..., examples=["How are transformers used in biomedicine?"])
    top_k: int = Field(default=5, ge=1, le=20)


class DemoSeedRequest(BaseModel):
    limit_per_topic: int = Field(default=15, ge=1, le=50)


class HydrateRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)


def _raise_http_error(error: Exception) -> None:
    message = str(error)
    if isinstance(error, OperationalError):
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL is unavailable or DATABASE_URL is incorrect.",
        ) from error
    if isinstance(error, Neo4jError):
        raise HTTPException(
            status_code=503,
            detail="Neo4j is unavailable or graph credentials are incorrect.",
        ) from error
    if isinstance(error, OpenAIError) and "insufficient_quota" in message:
        raise HTTPException(
            status_code=402,
            detail="OpenAI quota is unavailable. Set EMBEDDING_PROVIDER=local and SUMMARY_PROVIDER=local.",
        ) from error
    if "OPENAI_API_KEY" in message:
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY is missing. Set local providers or add a valid key.",
        ) from error
    raise HTTPException(status_code=500, detail=message) from error


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats")
def stats() -> dict:
    try:
        return dashboard_stats()
    except Exception as error:
        _raise_http_error(error)


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict[str, int]:
    try:
        return ingest_pipeline(query=request.query, limit=request.limit)
    except Exception as error:
        _raise_http_error(error)


@app.post("/query")
def query(request: QueryRequest) -> dict:
    try:
        result = answer_query(query=request.query, top_k=request.top_k)
    except Exception as error:
        _raise_http_error(error)
    if not result["papers"]:
        raise HTTPException(
            status_code=404,
            detail="No embedded papers found. Ingest papers before querying.",
        )
    return result


@app.post("/demo-seed")
def demo_seed(request: DemoSeedRequest) -> dict:
    try:
        return ingest_demo_pipeline(limit_per_topic=request.limit_per_topic)
    except Exception as error:
        _raise_http_error(error)


@app.post("/hydrate-citations")
def hydrate_citations(request: HydrateRequest) -> dict:
    try:
        return hydrate_citation_metadata(limit=request.limit)
    except Exception as error:
        _raise_http_error(error)
