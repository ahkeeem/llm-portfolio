from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.inference import extract_receipt_fields

app = FastAPI(
    title="Edge-AI Extraction Pipeline",
    description="Offline OCR and SLM data extraction for 100% data privacy and 0ms latency.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReceiptRequest(BaseModel):
    receipt_text: str


class ReviewRequest(BaseModel):
    receipt_text: str
    predicted: dict
    corrected: dict  # Human-corrected fields


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
def extract(req: ReceiptRequest):
    """
    Extract structured fields from receipt text.
    Returns company, date, address, total.
    """
    result = extract_receipt_fields(req.receipt_text)
    return result


@app.post("/review")
def review(req: ReviewRequest):
    """
    Human-in-the-loop: submit corrections for a prediction.
    In production, this would feed back into the training pipeline.
    """
    return {
        "status": "correction_logged",
        "predicted": req.predicted,
        "corrected": req.corrected,
    }
