"""Tests for RAG evaluation metrics and pipeline."""

from core.metrics import score_rouge_l, _lcs_length


class TestRougeL:
    """Test the ROUGE-L lexical metric."""

    def test_identical_strings(self):
        score = score_rouge_l("the cat sat on the mat", "the cat sat on the mat")
        assert score == 1.0

    def test_completely_different(self):
        score = score_rouge_l("alpha beta gamma", "one two three four five")
        assert score == 0.0

    def test_partial_overlap(self):
        score = score_rouge_l(
            "the UK follows a pro-innovation approach to AI regulation",
            "the UK has a pro-innovation approach to AI"
        )
        assert 0.5 < score < 1.0

    def test_empty_input(self):
        assert score_rouge_l("", "something") == 0.0
        assert score_rouge_l("something", "") == 0.0
        assert score_rouge_l("", "") == 0.0


class TestLCS:
    """Test the longest common subsequence helper."""

    def test_basic_lcs(self):
        assert _lcs_length(list("abcde"), list("ace")) == 3

    def test_identical(self):
        assert _lcs_length(list("abc"), list("abc")) == 3

    def test_no_common(self):
        assert _lcs_length(list("abc"), list("xyz")) == 0


class TestPrompts:
    """Test that prompt builders produce valid strings."""

    def test_rag_prompt_contains_context_and_question(self):
        from core.prompts import rag_prompt
        context = "[1] The UK AI Act requires transparency."
        question = "What does the UK AI Act say?"
        prompt = rag_prompt(question, context)
        assert context in prompt
        assert question in prompt
        assert "citation" in prompt.lower() or "cite" in prompt.lower()

    def test_rag_prompt_is_string(self):
        from core.prompts import rag_prompt
        result = rag_prompt("test question", "test context")
        assert isinstance(result, str)
        assert len(result) > 0
