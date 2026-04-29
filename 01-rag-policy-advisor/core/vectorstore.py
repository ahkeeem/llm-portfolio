import chromadb
from core.embeddings import get_embedding

# Persistent ChromaDB client
_client = chromadb.PersistentClient(path="data/chromadb")
_collection = _client.get_or_create_collection(
    name="policy_documents",
    metadata={"hnsw:space": "cosine"},
)


def add_documents(documents: list[dict]) -> int:
    """
    Add documents to the vector store.

    Args:
        documents: List of dicts with 'text', 'metadata', and optional 'id' keys.

    Returns:
        Number of documents added.
    """
    ids = []
    embeddings = []
    texts = []
    metadatas = []

    for i, doc in enumerate(documents):
        doc_id = doc.get("id", f"doc_{i}")
        ids.append(doc_id)
        embeddings.append(get_embedding(doc["text"]))
        texts.append(doc["text"])
        metadatas.append(doc.get("metadata", {}))

    _collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return len(ids)


def search_similar(query: str, top_k: int = 5) -> list[dict]:
    """
    Search the vector store for chunks similar to the query.

    Args:
        query: Natural language query string.
        top_k: Number of results to return.

    Returns:
        List of dicts with 'text', 'metadata', and 'score' keys.
    """
    query_embedding = get_embedding(query)

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    output = []
    for i in range(len(results["documents"][0])):
        output.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "score": results["distances"][0][i] if results["distances"] else 0.0,
        })

    return output
