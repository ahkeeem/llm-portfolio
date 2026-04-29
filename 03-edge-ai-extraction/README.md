# 🛡️ Project 3 — Edge-AI Extraction Pipeline

> Local OCR and Small Language Model (SLM) extraction pipeline running entirely on edge hardware for 100% data privacy and 0ms network latency.

---

## 🎯 Problem

Enterprise data often contains highly sensitive PII or proprietary financial information (like receipts, invoices, and KYC documents). Sending this data to cloud APIs (like OpenAI) violates data sovereignty requirements and introduces unpredictable network latency.

## 💡 Solution

A secure, edge-deployed pipeline that:
1. **Digitizes** documents offline using local OCR
2. **Extracts** structured JSON using a Small Language Model (SLM like Phi-3-mini) fine-tuned with LoRA/PEFT
3. **Serves** predictions via a local FastAPI endpoint running directly on the client's hardware

### Why Edge-AI instead of Cloud APIs?
For high-volume structured data extraction, standard cloud APIs are a liability. By deploying an OCR + SLM pipeline on the edge, we achieve:
- **100% Data Privacy:** No sensitive data ever leaves the local network. Perfect for healthcare (HIPAA) or finance (SOC2).
- **0ms Network Latency:** Eliminates the network round-trip time associated with cloud APIs.
- **Zero API Costs:** Processing 10,000 documents a day with a local, 4-bit quantized SLM eliminates per-token API costs entirely.

## 🧑‍🔬 Control (Human-in-the-Loop)

| Gate | Description |
|------|-------------|
| Data cleaning | Human reviews and corrects training labels before fine-tuning |
| Prediction review | Low-confidence extractions are flagged for manual verification |
| Model comparison | Human evaluates fine-tuned vs base model outputs |

## 📊 Result

| Metric | Target | Description |
|--------|--------|-------------|
| Field-level F1 | > 0.90 | Per-field extraction accuracy |
| Exact Match | > 0.75 | All fields correct in one prediction |
| Inference cost | ~400 tokens | Per-receipt extraction |

---

## 📁 Structure

```
03-edge-ai-extraction/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI inference endpoint
├── core/
│   ├── __init__.py
│   ├── trainer.py            # LoRA fine-tuning logic
│   ├── inference.py          # Model loading + prediction
│   ├── data_prep.py          # SROIE → training format
│   └── metrics.py            # F1, exact match evaluation
├── data/
│   ├── raw/                  # SROIE dataset
│   └── processed/            # train.jsonl / val.jsonl
├── scripts/
│   ├── prepare_data.py       # Data preparation script
│   └── train.py              # Training script
├── tests/
│   └── test_data_prep.py
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Setup
```bash
cd 03-edge-ai-extraction
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Prepare Data
```bash
python scripts/prepare_data.py  # Downloads SROIE + converts to JSONL
```

### 3. Train
```bash
python scripts/train.py  # LoRA fine-tuning (requires GPU)
```

### 4. Serve
```bash
uvicorn app.main:app --reload
```

### 5. Extract
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"receipt_text": "WALMART\n123 Main St\n04/15/2024\nMilk $3.99\nBread $2.49\nTOTAL $6.48"}'
```

---

## 🏗️ Architecture

```
SROIE Dataset
    │
    ▼
┌─────────────────┐
│  Data Prep       │ ── scripts/prepare_data.py
│  (SROIE → JSONL) │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  LoRA Training   │ ── scripts/train.py
│  (Phi-3-mini +   │
│   PEFT adapter)  │
└──────┬──────────┘
       │  adapter weights
       ▼
┌─────────────────┐
│  Inference API   │ ── app/main.py
│  (receipt → JSON)│
└─────────────────┘
```

---

## 📦 Dataset

**SROIE** (Scanned Receipts OCR and Information Extraction)
- Source: HuggingFace `darentang/sroie`
- Task: Extract company, date, address, total from receipt text
- Size: ~626 training samples

---

## 🔧 Tech Stack

| Component | Tool |
|-----------|------|
| Base Model | Phi-3-mini (or Mistral-7B) |
| Fine-tuning | HuggingFace PEFT / LoRA |
| Quantization | bitsandbytes (4-bit) |
| API | FastAPI + Pydantic |
| Deployment | Docker + Uvicorn |
