"""
RAG Evaluation Pipeline — runs in-process against the live RAG system.

Metrics computed per QA pair:
  - Faithfulness (LLM-as-judge)
  - Relevancy (LLM-as-judge)
  - Correctness (LLM-as-judge)
  - Context Recall (LLM-as-judge)
  - ROUGE-L (lexical)
  - Latency (ms)
  - Token cost estimate (USD)
"""

import json
import os
import time
from datetime import datetime

from core.metrics import (
    score_faithfulness,
    score_relevancy,
    score_correctness,
    score_context_recall,
    score_rouge_l,
)
from core.rag import query_rag
from core.monitoring import metrics as telemetry


def run_evaluation(
    qa_path: str = "data/qa_pairs/qa_pairs.json",
    flag_threshold: float = 0.6,
) -> dict:
    """
    Run evaluation on all QA pairs against the RAG system directly.

    Args:
        qa_path: Path to the QA pairs JSON file.
        flag_threshold: Average score below which a result is flagged for human review.

    Returns:
        Dict with per-question results, aggregate metrics, and operational stats.
    """
    if not os.path.exists(qa_path):
        return {"error": f"QA pairs not found at {qa_path}"}

    with open(qa_path, "r") as f:
        qa_pairs = json.load(f)

    results = []
    flagged = []
    total_latency_ms = 0

    for i, qa in enumerate(qa_pairs):
        question = qa["question"]
        ground_truth = qa["answer"]

        # Query the RAG system directly (in-memory, no HTTP)
        start_time = time.time()
        try:
            rag_result = query_rag(question)
            answer = rag_result.get("answer", "")
            context = rag_result.get("retrieved_context", "")
            chunks_used = rag_result.get("chunks_used", 0)
        except Exception as e:
            answer = f"ERROR: {str(e)}"
            context = ""
            chunks_used = 0

        latency_ms = round((time.time() - start_time) * 1000, 1)
        total_latency_ms += latency_ms

        # Score the answer across all metrics
        faithfulness = score_faithfulness(answer, context)
        relevancy = score_relevancy(answer, question)
        correctness = score_correctness(answer, ground_truth)
        ctx_recall = score_context_recall(context, ground_truth)
        rouge_l = score_rouge_l(answer, ground_truth)

        avg_score = round(
            (faithfulness + relevancy + correctness + ctx_recall) / 4, 3
        )

        result = {
            "id": i,
            "question": question,
            "ground_truth": ground_truth,
            "rag_answer": answer,
            "chunks_used": chunks_used,
            "latency_ms": latency_ms,
            "scores": {
                "faithfulness": round(faithfulness, 3),
                "relevancy": round(relevancy, 3),
                "correctness": round(correctness, 3),
                "context_recall": round(ctx_recall, 3),
                "rouge_l": round(rouge_l, 3),
                "average": avg_score,
            },
            "flagged": avg_score < flag_threshold,
        }

        results.append(result)
        if avg_score < flag_threshold:
            flagged.append(result)

    n = len(results) or 1

    # Aggregate metrics
    aggregate = {
        "total_questions": len(qa_pairs),
        "avg_faithfulness": round(sum(r["scores"]["faithfulness"] for r in results) / n, 3),
        "avg_relevancy": round(sum(r["scores"]["relevancy"] for r in results) / n, 3),
        "avg_correctness": round(sum(r["scores"]["correctness"] for r in results) / n, 3),
        "avg_context_recall": round(sum(r["scores"]["context_recall"] for r in results) / n, 3),
        "avg_rouge_l": round(sum(r["scores"]["rouge_l"] for r in results) / n, 3),
        "avg_latency_ms": round(total_latency_ms / n, 1),
        "flagged_count": len(flagged),
        "flag_rate": round(len(flagged) / n, 3),
    }

    # Update telemetry
    telemetry.inc("evaluations_run")

    output = {
        "timestamp": datetime.now().isoformat(),
        "config": {"qa_path": qa_path, "flag_threshold": flag_threshold},
        "aggregate": aggregate,
        "results": results,
        "flagged": flagged,
    }

    # Persist results
    os.makedirs("data/results", exist_ok=True)
    result_path = f"data/results/eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_path, "w") as f:
        json.dump(output, f, indent=2)

    return output
