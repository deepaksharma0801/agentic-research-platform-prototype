from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Iterable, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text, create_engine, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    openalex_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authors: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    referenced_openalex_ids: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(get_settings().embedding_dimensions), nullable=True
    )


engine = create_engine(get_settings().database_url, future=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create pgvector extension, tables, and a vector index for semantic search."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_papers_embedding_hnsw
                ON papers USING hnsw (embedding vector_cosine_ops)
                WHERE embedding IS NOT NULL
                """
            )
        )


def upsert_paper(session: Session, paper_data: dict) -> Paper:
    paper = session.query(Paper).filter_by(openalex_id=paper_data["openalex_id"]).one_or_none()
    if paper is None:
        paper = Paper(**paper_data)
        session.add(paper)
    else:
        for key, value in paper_data.items():
            setattr(paper, key, value)
    return paper


def papers_missing_embeddings(session: Session, limit: int = 100) -> Iterable[Paper]:
    return (
        session.query(Paper)
        .filter(Paper.abstract.is_not(None), Paper.embedding.is_(None))
        .limit(limit)
        .all()
    )
