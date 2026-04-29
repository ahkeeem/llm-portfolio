from core.vectorstore import search_similar
from core.prompts import rag_prompt
from core.llm import call_llm


def query_rag(question: str, top_k: int = 5) -> dict:
    """
    RAG pipeline:
    1. Search vector store for relevant chunks
    2. Build context-augmented prompt
    3. Generate grounded answer with source citations

    Args:
        question: Natural language query
        top_k: Number of chunks to retrieve

    Returns:
        Dict with answer, sources, and metadata
    """
    # Step 1: Retrieve relevant chunks
    results = search_similar(question, top_k=top_k)

    # Step 2: Build context from retrieved chunks
    context_chunks = []
    sources = []
    for i, result in enumerate(results):
        context_chunks.append(f"[{i+1}] {result['text']}")
        sources.append({
            "chunk_id": i + 1,
            "source": result.get("metadata", {}).get("source", "unknown"),
            "score": result.get("score", 0.0),
        })

    context = "\n\n".join(context_chunks)

    # Step 3: Generate answer
    prompt = rag_prompt(question, context)
    answer = call_llm(prompt)

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieved_context": context,  # Added for evaluation
        "chunks_used": len(results),
    }
