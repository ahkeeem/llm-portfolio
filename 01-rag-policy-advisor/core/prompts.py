def rag_prompt(question: str, context: str) -> str:
    """Build the RAG prompt with retrieved context and user question."""
    return f"""You are a policy research assistant. Answer the question using ONLY the provided context.
If the context doesn't contain enough information, say so clearly.
Always cite your sources using [1], [2], etc. notation.

Context:
{context}

Question:
{question}

Answer (with source citations):"""
