import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    openai_api_key: str | None
    openai_embedding_model: str
    openai_summary_model: str
    embedding_provider: str
    summary_provider: str
    openalex_email: str | None
    embedding_dimensions: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://research:research@localhost:5433/research",
        ),
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "research-password"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        openai_summary_model=os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "openai").lower(),
        summary_provider=os.getenv("SUMMARY_PROVIDER", "openai").lower(),
        openalex_email=os.getenv("OPENALEX_EMAIL"),
        embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1536")),
    )
