from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.rag import query_rag

app = FastAPI(
    title="RAG Policy Advisor",
    description="Query UK policy documents and arXiv papers with source-cited answers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class FlagRequest(BaseModel):
    question: str
    answer: str
    reason: str  # "bad_answer" | "missing_source" | "other"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query(req: QueryRequest):
    """
    Query the RAG system with a natural language question.
    Returns an answer grounded in retrieved document chunks with source citations.
    """
    result = query_rag(req.question, top_k=req.top_k)
    return result


@app.post("/flag")
def flag(req: FlagRequest):
    """
    Human-in-the-loop: flag a bad answer for review.
    In production, this would log to a review queue.
    """
    # TODO: Persist to a review database / Langfuse
    return {
        "status": "flagged",
        "question": req.question,
        "reason": req.reason,
    }
