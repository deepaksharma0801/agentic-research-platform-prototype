from research_agent.summarization import _format_paper, summarize_local


def test_format_paper_includes_core_metadata() -> None:
    text = _format_paper(
        {
            "title": "A Useful Paper",
            "year": 2024,
            "authors": ["Ada Lovelace"],
            "abstract": "A concise abstract.",
        }
    )
    assert "A Useful Paper" in text
    assert "2024" in text
    assert "Ada Lovelace" in text
    assert "A concise abstract." in text


def test_summarize_local_includes_retrieved_and_related_papers() -> None:
    summary = summarize_local(
        query="biomedicine transformers",
        papers=[
            {
                "title": "Transformers in Biomedicine",
                "year": 2024,
                "abstract": "Transformer models support biomedical retrieval. More text.",
            }
        ],
        related_papers=[{"title": "Clinical NLP", "year": 2022}],
    )
    assert "Local summary for query: biomedicine transformers" in summary
    assert "Transformers in Biomedicine (2024)" in summary
    assert "Clinical NLP (2022)" in summary
