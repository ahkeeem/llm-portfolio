# 🧾 Project 3 — Receipt Fine-tuner

> Parameter-efficient fine-tuning (LoRA) for structured data extraction from receipt images/text.

---

## 🎯 Problem

Extracting structured data (merchant, date, total, items) from receipts is tedious and error-prone when done manually. Generic LLMs lack the domain precision needed for consistent field extraction.

## 💡 Solution

A fine-tuned model that:
1. **Trains** on the SROIE receipt extraction dataset using LoRA/PEFT
2. **Extracts** structured JSON from receipt text (merchant, date, address, total)
3. **Serves** predictions via a FastAPI endpoint

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
03-receipt-finetuner/
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
cd 03-receipt-finetuner
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
