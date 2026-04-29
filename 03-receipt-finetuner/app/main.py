from fastapi import FastAPI
from pydantic import BaseModel
from core.inference import extract_receipt_fields

app = FastAPI(
    title="Receipt Fine-tuner",
    description="Extract structured data from receipt text using a fine-tuned model.",
    version="1.0.0",
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
