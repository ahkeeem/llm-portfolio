"""
Document ingestion script for RAG Policy Advisor.

Parses PDFs and text files from data/raw/, chunks them, and loads into ChromaDB.

Usage:
    python scripts/ingest_documents.py
"""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_text_files(raw_dir: str = "data/raw") -> list[dict]:
    """Load all text/PDF files from the raw directory."""
    documents = []

    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir, exist_ok=True)
        print(f"📁 Created {raw_dir}/ — place your documents there and re-run.")
        return documents

    for filename in os.listdir(raw_dir):
        filepath = os.path.join(raw_dir, filename)
        if filename.endswith(".txt"):
            with open(filepath, "r") as f:
                text = f.read()
            documents.append({"text": text, "source": filename})
        elif filename.endswith(".pdf"):
            try:
                import pdfplumber

                with pdfplumber.open(filepath) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                documents.append({"text": text, "source": filename})
            except ImportError:
                print("⚠️ Install pdfplumber for PDF support: pip install pdfplumber")

    print(f"✅ Loaded {len(documents)} documents from {raw_dir}/")
    return documents


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 20:  # Skip very short chunks
            chunks.append(chunk)
        start = end - overlap

    return chunks


def ingest(raw_dir: str = "data/raw"):
    """Main ingestion pipeline: load → chunk → embed → store."""
    from core.vectorstore import add_documents

    documents = load_text_files(raw_dir)
    if not documents:
        print("❌ No documents to ingest.")
        return

    all_chunks = []
    for doc in documents:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{doc['source']}_chunk_{i}",
                "text": chunk,
                "metadata": {"source": doc["source"], "chunk_index": i},
            })

    print(f"📦 Chunked into {len(all_chunks)} chunks")

    count = add_documents(all_chunks)
    print(f"✅ Ingested {count} chunks into ChromaDB")

    # Save manifest
    manifest_path = "data/processed/ingest_manifest.json"
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(
            {"total_documents": len(documents), "total_chunks": len(all_chunks)},
            f,
            indent=2,
        )
    print(f"📋 Manifest saved to {manifest_path}")


if __name__ == "__main__":
    ingest()
