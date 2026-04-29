from core.prompts import rag_prompt


def test_rag_prompt_contains_context_and_question():
    """Verify the RAG prompt includes both context and question."""
    context = "[1] The UK AI Act requires transparency."
    question = "What does the UK AI Act say?"
    prompt = rag_prompt(question, context)
    assert context in prompt
    assert question in prompt
    assert "citation" in prompt.lower() or "cite" in prompt.lower()


def test_rag_prompt_is_string():
    """Ensure prompt builder returns a non-empty string."""
    result = rag_prompt("test question", "test context")
    assert isinstance(result, str)
    assert len(result) > 0
