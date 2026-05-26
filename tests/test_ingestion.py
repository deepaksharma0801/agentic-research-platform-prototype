from research_agent.ingestion import reconstruct_abstract


def test_reconstruct_abstract_from_openalex_inverted_index() -> None:
    inverted = {"hello": [0], "research": [2], "agentic": [1]}
    assert reconstruct_abstract(inverted) == "hello agentic research"


def test_reconstruct_abstract_handles_missing_value() -> None:
    assert reconstruct_abstract(None) is None
