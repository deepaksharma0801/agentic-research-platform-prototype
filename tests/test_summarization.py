from research_agent.summarization import _format_paper


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
