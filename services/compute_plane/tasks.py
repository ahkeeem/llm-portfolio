import time
from celery.utils.log import get_task_logger
from .celery_app import app

logger = get_task_logger(__name__)

@app.task(bind=True, name="compute_plane.async_ocr_extraction")
def async_ocr_extraction(self, document_path: str) -> dict:
    """
    Simulates a heavy OCR extraction task using local Edge AI / SLMs.
    In production, this would load a local Phi-3-mini or PyTesseract instance.
    """
    logger.info(f"Starting async OCR extraction for: {document_path}")

    # Simulate heavy CPU processing
    time.sleep(5)

    # Mock extracted text
    extracted_text = f"Mock extracted text from {document_path}. Policy ID: 12345."

    logger.info(f"Finished OCR extraction for: {document_path}")
    return {
        "status": "success",
        "document_path": document_path,
        "extracted_text": extracted_text,
        "confidence_score": 0.92
    }

@app.task(bind=True, name="compute_plane.vector_indexing")
def async_vector_indexing(self, documents: list) -> dict:
    """
    Simulates heavy chunking and embedding generation for ChromaDB/Pinecone.
    """
    logger.info(f"Starting vector indexing for {len(documents)} documents.")

    # Simulate heavy GPU/CPU processing
    time.sleep(3)

    logger.info(f"Finished vector indexing.")
    return {
        "status": "success",
        "indexed_chunks": len(documents) * 5,
        "db": "chroma"
    }
