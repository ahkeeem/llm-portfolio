from unittest.mock import patch
from core.agent import process_email


@patch("core.agent.call_llm")
def test_process_email_returns_expected_keys(mock_llm):
    """Verify the agent pipeline returns classification, response, and approval flag."""
    mock_llm.side_effect = [
        '{"priority": "urgent", "type": "complaint"}',
        "Dear customer, we apologize for the inconvenience.",
    ]

    result = process_email("I want a refund now!")

    assert "classification" in result
    assert "response" in result
    assert "requires_approval" in result
    assert result["requires_approval"] is True


@patch("core.agent.call_llm")
def test_process_email_makes_two_llm_calls(mock_llm):
    """Verify the agent makes exactly 2 LLM calls (classify + respond)."""
    mock_llm.return_value = "mock response"

    process_email("Test email")

    assert mock_llm.call_count == 2
