from research_agent.pipeline import build_query_response


def test_build_query_response_adds_providers_counts_and_sources() -> None:
    response = build_query_response(
        query="test query",
        summary="A useful summary.",
        embedding_provider="local",
        summary_provider="local",
        results={
            "papers": [
                {
                    "source": "semantic",
                    "openalex_id": "https://openalex.org/W1",
                    "title": "Paper",
                }
            ],
            "related_papers": [
                {
                    "source": "citation",
                    "openalex_id": "https://openalex.org/W2",
                    "title": "Related Paper",
                }
            ],
        },
    )

    assert response["providers"] == {"embedding": "local", "summary": "local"}
    assert response["counts"] == {"papers": 1, "related_papers": 1}
    assert response["papers"][0]["source"] == "semantic"
    assert response["related_papers"][0]["source"] == "citation"
