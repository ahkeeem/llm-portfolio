from fastapi import FastAPI
from pydantic import BaseModel
from core.evaluator import run_evaluation

app = FastAPI(
    title="RAG Evaluator",
    description="Evaluate RAG system quality using RAGAS-style metrics on custom QA pairs.",
    version="1.0.0",
)


class EvalConfig(BaseModel):
    qa_path: str = "data/qa_pairs/qa_pairs.json"
    rag_endpoint: str = "http://localhost:8000/query"  # Project 1's endpoint
    flag_threshold: float = 0.6


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/evaluate")
def evaluate(config: EvalConfig = EvalConfig()):
    """
    Run a full evaluation against the RAG system.
    Returns per-question scores and aggregate metrics.
    """
    results = run_evaluation(
        qa_path=config.qa_path,
        rag_endpoint=config.rag_endpoint,
        flag_threshold=config.flag_threshold,
    )
    return results
