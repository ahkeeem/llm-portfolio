FROM python:3.11-slim

WORKDIR /app

# System dependencies for OCR (Tesseract) and basic building
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY 04-email-triage-agent/requirements.txt ./
# Also we need to make sure we install celery, redis, fastapi, uvicorn
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install celery redis fastapi uvicorn langgraph pydantic chromadb

# Copy the entire enterprise directory structure
COPY apps/ ./apps/
COPY core/ ./core/
COPY services/ ./services/
COPY datasets/ ./datasets/

# Use an entrypoint script to decide between Control Plane and Compute Plane
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Environment variables
ENV PYTHONPATH=/app

ENTRYPOINT ["./entrypoint.sh"]
