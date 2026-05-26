from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase

from .config import get_settings


class CitationGraph:
    def __init__(self) -> None:
        settings = get_settings()
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self) -> None:
        self.driver.close()

    def init_constraints(self) -> None:
        with self.driver.session() as session:
            session.run(
                """
                CREATE CONSTRAINT paper_openalex_id IF NOT EXISTS
                FOR (p:Paper) REQUIRE p.openalex_id IS UNIQUE
                """
            )

    def upsert_papers_and_citations(self, papers: list[dict[str, Any]]) -> None:
        """Create paper nodes and CITES relationships from OpenAlex references."""
        self.init_constraints()
        with self.driver.session() as session:
            session.execute_write(self._upsert_batch, papers)

    @staticmethod
    def _upsert_batch(tx, papers: list[dict[str, Any]]) -> None:
        tx.run(
            """
            UNWIND $papers AS paper
            MERGE (p:Paper {openalex_id: paper.openalex_id})
            SET p.title = paper.title, p.year = paper.year
            WITH p, paper
            UNWIND paper.referenced_openalex_ids AS ref_id
            MERGE (r:Paper {openalex_id: ref_id})
            MERGE (p)-[:CITES]->(r)
            """,
            papers=papers,
        )

    def related_papers(self, openalex_ids: list[str], limit: int = 20) -> list[dict[str, Any]]:
        """Find directly cited or citing papers near retrieved vector hits."""
        if not openalex_ids:
            return []
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (seed:Paper)
                WHERE seed.openalex_id IN $openalex_ids
                MATCH (seed)-[:CITES]-(related:Paper)
                WHERE NOT related.openalex_id IN $openalex_ids
                RETURN DISTINCT related.openalex_id AS openalex_id,
                       related.title AS title,
                       related.year AS year
                LIMIT $limit
                """,
                openalex_ids=openalex_ids,
                limit=limit,
            )
            return [dict(record) for record in result]

    def unhydrated_paper_ids(self, limit: int = 50) -> list[str]:
        """Return graph-only paper IDs that do not have OpenAlex metadata yet."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title STARTS WITH "https://openalex.org/"
                RETURN p.openalex_id AS openalex_id
                LIMIT $limit
                """,
                limit=limit,
            )
            return [record["openalex_id"] for record in result]
