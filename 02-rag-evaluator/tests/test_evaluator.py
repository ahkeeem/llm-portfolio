from core.metrics import score_faithfulness, score_relevancy, score_correctness
from unittest.mock import patch


@patch("core.metrics.call_llm")
def test_score_faithfulness_returns_float(mock_llm):
    """Score faithfulness should return a float between 0 and 1."""
    mock_llm.return_value = "0.85"
    result = score_faithfulness("The policy states X.", "The policy says X.")
    assert 0.0 <= result <= 1.0


@patch("core.metrics.call_llm")
def test_score_relevancy_returns_float(mock_llm):
    """Score relevancy should return a float between 0 and 1."""
    mock_llm.return_value = "0.9"
    result = score_relevancy("AI transparency is required.", "What are the AI rules?")
    assert 0.0 <= result <= 1.0


def test_empty_inputs_return_zero():
    """Empty inputs should return 0.0 without calling LLM."""
    assert score_faithfulness("", "") == 0.0
    assert score_relevancy("", "") == 0.0
    assert score_correctness("", "") == 0.0
