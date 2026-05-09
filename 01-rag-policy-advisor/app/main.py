import json
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.rag import query_rag
from core.evaluator import run_evaluation
from core.monitoring import metrics, track_endpoint

app = FastAPI(
    title="RAG Policy Advisor",
    description="Query UK policy documents and arXiv papers with source-cited answers. "
                "Includes built-in evaluation pipeline and telemetry.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response Models ---

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class FlagRequest(BaseModel):
    question: str
    answer: str
    reason: str  # "bad_answer" | "missing_source" | "other"


class EvalConfig(BaseModel):
    qa_path: str = "data/qa_pairs/qa_pairs.json"
    flag_threshold: float = 0.6


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/query")
@track_endpoint("/query")
def query(req: QueryRequest):
    """
    Query the RAG system with a natural language question.
    Returns an answer grounded in retrieved document chunks with source citations.
    """
    result = query_rag(req.question, top_k=req.top_k)
    return result


@app.post("/flag")
@track_endpoint("/flag")
def flag(req: FlagRequest):
    """
    Human-in-the-loop: flag a bad answer for review.
    Persists to a local JSON review log (production would use a database).
    """
    metrics.inc("flags_submitted")

    flag_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": req.question,
        "answer": req.answer,
        "reason": req.reason,
    }

    # Persist to a review log file
    os.makedirs("data/flags", exist_ok=True)
    flags_path = "data/flags/flagged_answers.jsonl"
    with open(flags_path, "a") as f:
        f.write(json.dumps(flag_entry) + "\n")

    return {
        "status": "flagged",
        "question": req.question,
        "reason": req.reason,
        "persisted_to": flags_path,
    }


@app.post("/evaluate")
@track_endpoint("/evaluate")
def evaluate(config: EvalConfig = EvalConfig()):
    """
    Run a full evaluation against the RAG system.
    Computes Faithfulness, Relevancy, Correctness, Context Recall,
    and ROUGE-L using LLM-as-judge methodology.
    """
    results = run_evaluation(
        qa_path=config.qa_path,
        flag_threshold=config.flag_threshold,
    )
    return results


@app.get("/metrics")
def get_metrics():
    """
    Live telemetry: request counts, latencies, token usage, and cost estimates.
    """
    return metrics.snapshot()
