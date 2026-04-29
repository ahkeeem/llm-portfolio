import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import base64
from PIL import Image
from core.vision import processor_engine

app = FastAPI(
    title="Automated Compliance Gateway",
    description="Edge-AI Local-First Pipeline for OCR Extraction, Redaction, and Human-in-the-Loop clearance.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    """
    Accepts a raw document image (FUNSD format), runs local LayoutLMv3 spatial extraction,
    applies pixel-level redaction over PII (answers), and returns a sanitized JSON.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
        
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    
    # Run the Local-First Pipeline (Modules A, B, C)
    sanitized_json, redacted_img, requires_review = processor_engine.process_document(image)
    
    # Convert redacted image to base64 for easy API consumption
    buffered = io.BytesIO()
    redacted_img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # The JSON Schema Generator
    return JSONResponse({
        "status": "success",
        "human_review_required": requires_review,
        "structured_data": sanitized_json,
        "redacted_image_base64": img_str
    })
