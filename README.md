# Agentic AI Research Platform Prototype

This prototype demonstrates an end-to-end AI research pipeline:

1. Download open-access scientific metadata from OpenAlex.
2. Store paper metadata in PostgreSQL.
3. Generate OpenAI embeddings for abstracts.
4. Store vectors in pgvector and run semantic search.
5. Store citation links in Neo4j.
6. Retrieve top-k papers plus citation-related papers.
7. Use an OpenAI chat model to summarize the retrieved context.
8. Test everything through a CLI or FastAPI.

## Prerequisites

- Python 3.10+
- Docker Desktop
- An OpenAI API key

## 1. Start PostgreSQL, pgvector, and Neo4j

```bash
docker compose up -d
```

PostgreSQL runs at `localhost:5433`, and Neo4j runs at:

- Browser: <http://localhost:7474>
- Bolt URI: `bolt://localhost:7687`
- Username: `neo4j`
- Password: `research-password`

The app enables `pgvector` automatically when you run database initialization.

## 2. Create a Python environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10-3.12 is recommended. Python 3.14 may try to build `psycopg2-binary`
from source if a wheel is unavailable.

## 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set your API key. For example:

```bash
OPENAI_API_KEY=your-key-here
```

Optional but recommended for OpenAlex etiquette:

```bash
OPENALEX_EMAIL=you@example.com
```

If OpenAI quota is unavailable, run the prototype in local fallback mode:

```bash
EMBEDDING_PROVIDER=local
SUMMARY_PROVIDER=local
```

Local mode uses dependency-free hash embeddings and an extractive summary. It is
lower quality than OpenAI, but it demonstrates the full database and retrieval
pipeline without API spend.

## 4. Initialize the database

```bash
python -m research_agent.cli init
```

This creates the `papers` table, enables `pgvector`, and creates an HNSW vector index.

## 5. Ingest papers

```bash
python -m research_agent.cli ingest \
  --query "machine learning in healthcare" \
  --limit 25
```

This command:

- downloads OpenAlex metadata
- writes paper metadata to PostgreSQL
- writes citation relationships to Neo4j
- embeds abstracts with OpenAI
- stores vectors in pgvector

## 6. Query from the CLI

```bash
python -m research_agent.cli query \
  "How are transformers used in biomedicine?" \
  --top-k 5
```

The command returns an LLM summary and a table of retrieved papers.

## 7. Query from FastAPI

Start the API:

```bash
uvicorn research_agent.api:app --reload
```

Open docs:

<http://127.0.0.1:8000/docs>

Or query with curl:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"How are transformers used in biomedicine?","top_k":5}'
```

You can also ingest through the API:

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning in healthcare","limit":25}'
```

## Troubleshooting

If `docker compose up -d` says it cannot connect to the Docker daemon, start Docker
Desktop first and wait until it says Docker is running.

If Postgres reports `Connection refused`, the containers did not start yet. Run:

```bash
docker compose ps
docker compose up -d
```

If zsh prints `command not found: #`, you copied a comment line into the terminal.
Skip lines that begin with `#`.

## Project Layout

```text
research_agent/
  api.py             # FastAPI app
  cli.py             # CLI commands
  config.py          # environment-backed settings
  db.py              # SQLAlchemy + pgvector models
  embeddings.py      # OpenAI embeddings
  graph.py           # Neo4j citation graph
  ingestion.py       # OpenAlex fetch/normalize
  pipeline.py        # end-to-end orchestration
  retrieval.py       # pgvector search + graph expansion
  summarization.py   # OpenAI summary generation
tests/
```

## Notes

- OpenAlex citation references often point to papers that were not part of your local ingestion batch. Neo4j still stores those related IDs, and retrieval will hydrate full metadata only when a referenced paper exists in PostgreSQL.
- This is a prototype, not production infrastructure. Real deployments should add background jobs, retries, migrations, auth, observability, and stricter rate-limit handling.
