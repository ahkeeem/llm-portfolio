from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.agent import process_email
from core.monitoring import metrics, track_endpoint

app = FastAPI(
    title="Email Triage Agent",
    description="Classify, prioritize, and draft responses to emails with PII redaction "
                "and human-in-the-loop approval.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EmailRequest(BaseModel):
    email_text: str


class ApprovalRequest(BaseModel):
    email_text: str
    approved: bool


@app.get("/")
def root():
    return {
        "message": "Email Triage Agent API is running",
        "version": "2.0.0",
        "documentation": "/docs",
        "endpoints": ["/process", "/approve", "/health", "/metrics"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/process")
@track_endpoint("/process")
def process(req: EmailRequest):
    """
    Process an email: scan PII, classify, prioritize, and draft a response.
    PII is redacted before any LLM call.
    Returns classification + draft with requires_approval flag.
    """
    metrics.inc("emails_processed")
    result = process_email(req.email_text)
    return result


@app.post("/approve")
@track_endpoint("/approve")
def approve(req: ApprovalRequest):
    """
    Human-in-the-loop approval gate.
    In production, this would trigger the actual send or archive action.
    """
    if req.approved:
        metrics.inc("emails_approved")
        return {"status": "approved", "action": "email_sent"}
    else:
        metrics.inc("emails_rejected")
        return {"status": "rejected", "action": "archived_for_review"}


@app.get("/metrics")
def get_metrics():
    """
    Live telemetry: request counts, latencies, token usage,
    PII redaction breakdown, and cost estimates.
    """
    return metrics.snapshot()
