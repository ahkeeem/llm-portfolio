import json
import os
from datetime import datetime

import requests

from core.metrics import score_faithfulness, score_relevancy, score_correctness


def run_evaluation(
    qa_path: str = "data/qa_pairs/qa_pairs.json",
    rag_endpoint: str = "http://localhost:8000/query",
    flag_threshold: float = 0.6,
) -> dict:
    """
    Run evaluation on all QA pairs against the RAG system.

    Args:
        qa_path: Path to the QA pairs JSON file.
        rag_endpoint: URL of the RAG system's query endpoint.
        flag_threshold: Score below which a result is flagged for review.

    Returns:
        Dict with per-question results and aggregate metrics.
    """
    # Load QA pairs
    with open(qa_path, "r") as f:
        qa_pairs = json.load(f)

    results = []
    flagged = []

    for i, qa in enumerate(qa_pairs):
        question = qa["question"]
        ground_truth = qa["answer"]

        # Query the RAG system
        try:
            response = requests.post(
                rag_endpoint,
                json={"question": question},
                timeout=30,
            )
            response.raise_for_status()
            rag_result = response.json()
            answer = rag_result.get("answer", "")
            context = rag_result.get("retrieved_context", "")
        except Exception as e:
            answer = f"ERROR: {str(e)}"
            context = ""

        # Score the answer
        faithfulness = score_faithfulness(answer, context)
        relevancy = score_relevancy(answer, question)
        correctness = score_correctness(answer, ground_truth)
        avg_score = (faithfulness + relevancy + correctness) / 3

        result = {
            "id": i,
            "question": question,
            "ground_truth": ground_truth,
            "rag_answer": answer,
            "scores": {
                "faithfulness": faithfulness,
                "relevancy": relevancy,
                "correctness": correctness,
                "average": round(avg_score, 3),
            },
            "flagged": avg_score < flag_threshold,
        }

        results.append(result)
        if avg_score < flag_threshold:
            flagged.append(result)

    # Aggregate metrics
    aggregate = {
        "total_questions": len(qa_pairs),
        "avg_faithfulness": round(
            sum(r["scores"]["faithfulness"] for r in results) / len(results), 3
        ),
        "avg_relevancy": round(
            sum(r["scores"]["relevancy"] for r in results) / len(results), 3
        ),
        "avg_correctness": round(
            sum(r["scores"]["correctness"] for r in results) / len(results), 3
        ),
        "flagged_count": len(flagged),
        "flag_rate": round(len(flagged) / len(results), 3) if results else 0,
    }

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "config": {"qa_path": qa_path, "flag_threshold": flag_threshold},
        "aggregate": aggregate,
        "results": results,
        "flagged": flagged,
    }

    os.makedirs("data/results", exist_ok=True)
    result_path = f"data/results/eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_path, "w") as f:
        json.dump(output, f, indent=2)

    return output
