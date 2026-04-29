# 📊 Project 2 — RAG Evaluator

> Custom evaluation pipeline for measuring RAG system quality using RAGAS metrics and human-verified QA pairs.

---

## 🎯 Problem

RAG systems can hallucinate, miss relevant sources, or give vague answers. Without systematic evaluation, you can't improve what you can't measure — and clients demand evidence of quality.

## 💡 Solution

An evaluation pipeline that:
1. **Generates** 30-50 QA pairs from Project 1's document corpus (LLM + manual verification)
2. **Runs** each question through the RAG system
3. **Scores** answers using an "LLM-as-a-Judge" layer measuring faithfulness, relevancy, context precision, and correctness
4. **Reports** aggregate metrics with per-question drill-down

### The "Evaluation-First" Loop
Automated metrics are useless if they don't correlate with human judgment. We validate the reliability of the **LLM-as-a-Judge** by:
1. Creating a gold-standard baseline of human-labeled QA pairs.
2. Running the RAGAS evaluator against this dataset.
3. Measuring the alignment between the automated scores and human labels. If the LLM judge hallucinates high scores for bad answers, the evaluation prompt is iterated and version-controlled until it aligns with human intuition.

## 🧑‍🔬 Control (Human-in-the-Loop)

| Gate | Description |
|------|-------------|
| Ground truth labeling | Humans write/verify reference answers |
| Low score review | Any answer scoring < 0.6 is flagged for manual inspection |
| QA pair curation | LLM-generated QA pairs are manually verified before use |

## 📊 Result

| Metric | Target | Description |
|--------|--------|-------------|
| Faithfulness | > 0.85 | Is the answer grounded in retrieved context? |
| Answer Relevancy | > 0.80 | Does the answer address the question? |
| Context Precision | > 0.75 | Are retrieved chunks relevant? |
| Answer Correctness | > 0.70 | Does it match ground truth? |

---

## 📁 Structure

```
02-rag-evaluator/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI endpoints for eval runs
├── core/
│   ├── __init__.py
│   ├── evaluator.py          # Evaluation engine
│   ├── metrics.py            # Individual metric calculators
│   ├── qa_generator.py       # Synthetic QA pair generation
│   └── llm.py                # LLM wrapper
├── data/
│   ├── qa_pairs/             # Ground truth QA pairs (JSON)
│   └── results/              # Evaluation run results
├── scripts/
│   └── generate_qa.py        # QA generation script
├── tests/
│   └── test_evaluator.py
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
cd 02-rag-evaluator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Generate QA Pairs
```bash
python scripts/generate_qa.py
# Then manually review data/qa_pairs/qa_pairs.json
```

### 3. Run Evaluation
```bash
uvicorn app.main:app --reload
curl -X POST http://localhost:8000/evaluate
```

---

## 🏗️ Architecture

```
QA Pairs (ground truth)
        │
        ▼
┌──────────────────┐
│  For each QA pair │
│    ├── Query RAG  │ ── calls Project 1's /query endpoint
│    ├── Get answer │
│    └── Score it   │ ── faithfulness, relevancy, etc.
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Aggregate Metrics │
│  + Per-Question    │
│    Breakdown       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Report / Flag    │
│  Low Scores       │
└──────────────────┘
```

---

## 🔧 Tech Stack

| Component | Tool |
|-----------|------|
| LLM | OpenAI GPT-4o-mini |
| Metrics | RAGAS (or custom implementation) |
| API | FastAPI |
| Data | JSON QA pairs |
| Deployment | Docker + Uvicorn |
