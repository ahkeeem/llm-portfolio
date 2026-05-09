"""Tests for PII redaction pipeline."""

from unittest.mock import patch
from core.agent import process_email, _redact_pii


class TestPIIRedaction:
    """Verify PII patterns are correctly detected and redacted."""

    def test_email_redaction(self):
        text = "Contact me at john@example.com for details."
        redacted, types = _redact_pii(text)
        assert "[EMAIL_REDACTED]" in redacted
        assert "john@example.com" not in redacted
        assert "EMAIL_REDACTED" in types

    def test_phone_redaction(self):
        text = "Call me at 555-123-4567 today."
        redacted, types = _redact_pii(text)
        assert "[PHONE_REDACTED]" in redacted
        assert "555-123-4567" not in redacted
        assert "PHONE_REDACTED" in types

    def test_ssn_redaction(self):
        text = "My SSN is 123-45-6789."
        redacted, types = _redact_pii(text)
        assert "[SSN_REDACTED]" in redacted
        assert "123-45-6789" not in redacted
        assert "SSN_REDACTED" in types

    def test_credit_card_redaction(self):
        text = "Card number: 4111 1111 1111 1111"
        redacted, types = _redact_pii(text)
        assert "[CARD_REDACTED]" in redacted
        assert "4111" not in redacted
        assert "CARD_REDACTED" in types

    def test_no_pii_returns_clean(self):
        text = "This is a normal email with no sensitive data."
        redacted, types = _redact_pii(text)
        assert redacted == text
        assert types == []

    def test_multiple_pii_types(self):
        text = "Email john@test.com, call 555-123-4567, SSN 123-45-6789."
        redacted, types = _redact_pii(text)
        assert "EMAIL_REDACTED" in types
        assert "PHONE_REDACTED" in types
        assert "SSN_REDACTED" in types
        assert "john@test.com" not in redacted
        assert "555-123-4567" not in redacted
        assert "123-45-6789" not in redacted


class TestAgentPipeline:
    """Verify the agent pipeline correctly processes emails."""

    @patch("core.agent.call_llm")
    def test_process_email_returns_expected_keys(self, mock_llm):
        mock_llm.side_effect = [
            '{"priority": "urgent", "type": "complaint"}',
            "Dear customer, we apologize for the inconvenience.",
        ]
        result = process_email("I want a refund now!")
        assert "classification" in result
        assert "response" in result
        assert "requires_approval" in result
        assert "privacy_scan" in result
        assert "pii_redacted" in result
        assert result["requires_approval"] is True

    @patch("core.agent.call_llm")
    def test_pii_email_is_flagged(self, mock_llm):
        mock_llm.side_effect = [
            '{"priority": "urgent", "type": "complaint"}',
            "We will look into this.",
        ]
        result = process_email("My email is user@test.com and SSN is 123-45-6789")
        assert result["pii_redacted"] is True
        assert "EMAIL_REDACTED" in result["privacy_scan"]
        assert "SSN_REDACTED" in result["privacy_scan"]

    @patch("core.agent.call_llm")
    def test_clean_email_passes_scan(self, mock_llm):
        mock_llm.side_effect = [
            '{"priority": "low", "type": "info"}',
            "Thank you for the update.",
        ]
        result = process_email("The deployment is complete. No action needed.")
        assert result["pii_redacted"] is False
        assert result["privacy_scan"] == "PASSED"

    @patch("core.agent.call_llm")
    def test_llm_never_sees_raw_pii(self, mock_llm):
        """The most critical test: verify the LLM only ever receives redacted text."""
        mock_llm.side_effect = [
            '{"priority": "urgent", "type": "complaint"}',
            "We will investigate.",
        ]
        process_email("Contact me at secret@email.com about SSN 111-22-3333")

        # Check all prompts sent to the LLM
        for call_args in mock_llm.call_args_list:
            prompt = call_args[0][0]
            assert "secret@email.com" not in prompt
            assert "111-22-3333" not in prompt

    @patch("core.agent.call_llm")
    def test_makes_two_llm_calls(self, mock_llm):
        mock_llm.return_value = "mock response"
        process_email("Test email")
        assert mock_llm.call_count == 2
