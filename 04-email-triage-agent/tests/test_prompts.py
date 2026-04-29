import pytest
from core.prompts import classify_prompt, response_prompt


def test_classify_prompt_contains_email():
    """Verify the classify prompt includes the email text."""
    email = "I need a refund immediately!"
    prompt = classify_prompt(email)
    assert email in prompt
    assert "urgent" in prompt
    assert "complaint" in prompt
    assert "JSON" in prompt


def test_response_prompt_contains_context():
    """Verify the response prompt includes email and classification."""
    email = "Where is my order?"
    classification = '{"priority": "normal", "type": "request"}'
    prompt = response_prompt(email, classification)
    assert email in prompt
    assert classification in prompt
    assert "professional" in prompt.lower()


def test_classify_prompt_returns_string():
    """Ensure prompt builder returns a string."""
    result = classify_prompt("test email")
    assert isinstance(result, str)
    assert len(result) > 0
