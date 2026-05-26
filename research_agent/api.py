from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .pipeline import answer_query, ingest_pipeline


app = FastAPI(title="Agentic AI Research Platform Prototype")


class IngestRequest(BaseModel):
    query: str = Field(..., examples=["machine learning in healthcare"])
    limit: int = Field(default=25, ge=1, le=200)


class QueryRequest(BaseModel):
    query: str = Field(..., examples=["How are transformers used in biomedicine?"])
    top_k: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict[str, int]:
    return ingest_pipeline(query=request.query, limit=request.limit)


@app.post("/query")
def query(request: QueryRequest) -> dict:
    return answer_query(query=request.query, top_k=request.top_k)
