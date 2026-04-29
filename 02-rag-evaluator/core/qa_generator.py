"""
Generate synthetic QA pairs from document chunks for evaluation.
"""

import json
import os

from core.llm import call_llm


def generate_qa_from_text(text: str, num_pairs: int = 3) -> list[dict]:
    """
    Use LLM to generate QA pairs from a document chunk.

    Args:
        text: Source text to generate questions from.
        num_pairs: Number of QA pairs to generate.

    Returns:
        List of dicts with 'question' and 'answer' keys.
    """
    prompt = f"""Generate {num_pairs} question-answer pairs from the following text.
Return valid JSON array only, no other text.

Text:
{text[:2000]}

Format:
[
  {{"question": "...", "answer": "..."}},
  ...
]"""

    try:
        response = call_llm(prompt, temperature=0.7)
        # Try to parse JSON from response
        pairs = json.loads(response)
        return pairs if isinstance(pairs, list) else []
    except (json.JSONDecodeError, Exception):
        return []


def generate_qa_dataset(
    chunks_path: str = "../01-rag-policy-advisor/data/processed/",
    output_path: str = "data/qa_pairs/qa_pairs.json",
    target_pairs: int = 50,
):
    """
    Generate a QA evaluation dataset from document chunks.

    Args:
        chunks_path: Path to chunked documents.
        output_path: Where to save the generated QA pairs.
        target_pairs: Target number of QA pairs to generate.
    """
    all_pairs = []

    # Try loading chunks from the RAG project's processed data
    if os.path.exists(chunks_path):
        for filename in os.listdir(chunks_path):
            if filename.endswith(".json") or filename.endswith(".jsonl"):
                filepath = os.path.join(chunks_path, filename)
                with open(filepath, "r") as f:
                    if filename.endswith(".jsonl"):
                        chunks = [json.loads(line) for line in f]
                    else:
                        chunks = json.load(f)

                for chunk in chunks[:20]:  # Limit to avoid excessive API calls
                    text = chunk.get("text", chunk.get("content", ""))
                    if len(text) > 100:
                        pairs = generate_qa_from_text(text, num_pairs=3)
                        all_pairs.extend(pairs)

                    if len(all_pairs) >= target_pairs:
                        break

            if len(all_pairs) >= target_pairs:
                break

    all_pairs = all_pairs[:target_pairs]

    # Add verification flag
    for pair in all_pairs:
        pair["verified"] = False  # Human must verify before use

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_pairs, f, indent=2)

    print(f"✅ Generated {len(all_pairs)} QA pairs → {output_path}")
    print("⚠️  Remember to manually verify each pair (set 'verified': true)")

    return all_pairs
