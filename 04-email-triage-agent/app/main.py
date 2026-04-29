from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.agent import process_email

app = FastAPI(
    title="Email Triage Agent",
    description="Classify, prioritize, and draft responses to emails with human-in-the-loop approval.",
    version="1.0.0",
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
        "documentation": "/docs",
        "endpoints": ["/process", "/approve", "/health"]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process")
def process(req: EmailRequest):
    """
    Process an email: classify, prioritize, and generate a draft response.
    Returns classification + draft with requires_approval flag.
    """
    result = process_email(req.email_text)
    return result


@app.post("/approve")
def approve(req: ApprovalRequest):
    """
    Human-in-the-loop approval gate.
    In production, this would trigger the actual send or archive action.
    """
    if req.approved:
        return {"status": "approved", "action": "email_sent"}
    else:
        return {"status": "rejected", "action": "archived_for_review"}
