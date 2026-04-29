# 🤖 Project 4 — Email Triage Agent

> Autonomous email classification, prioritization, and response drafting with human approval gate.

---

## 🎯 Problem

Enterprise teams waste hours manually triaging inbound emails — classifying urgency, categorizing type, and drafting responses. This is repetitive, error-prone, and doesn't scale.

## 💡 Solution

A 2-step LLM agent that:
1. **Classifies** emails by priority (urgent/normal/low) and type (complaint/request/info)
2. **Drafts** a professional response based on the classification

All responses require **human approval** before sending — no black-box automation.

## 🧑‍🔬 Control (Human-in-the-Loop)

| Gate | Description |
|------|-------------|
| `requires_approval: true` | Every draft response is flagged for human review |
| `/approve` endpoint | Explicit approval/rejection before any action |
| Logging | All classifications and responses are traceable |

## 📊 Result

| Metric | Value |
|--------|-------|
| Token cost per email | ~1,250 tokens (~$0.0002) |
| Batch 1000 emails | ~$0.19 |
| Classification accuracy | Evaluated via human spot-checks |
| Response quality | Human-reviewed before send |

---

## 📁 Structure

```
04-email-triage-agent/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI endpoints
├── core/
│   ├── __init__.py
│   ├── agent.py              # 2-step pipeline orchestration
│   ├── llm.py                # OpenAI wrapper
│   └── prompts.py            # Prompt templates
├── data/
│   ├── raw/                  # Enron email CSV (not committed)
│   └── processed/            # Clean JSONL
├── scripts/
│   └── ingest_emails.py      # Dataset preparation
├── tests/
│   ├── test_agent.py         # Pipeline tests (mocked LLM)
│   └── test_prompts.py       # Prompt template tests
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
cd 04-email-triage-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your OPENAI_API_KEY
```

### 2. Prepare Data
```bash
# Download Enron dataset from Kaggle and place at data/raw/emails.csv
python scripts/ingest_emails.py
```

### 3. Run
```bash
uvicorn app.main:app --reload
```

### 4. Test
```bash
# Process an email
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"email_text": "I have been waiting 3 weeks for my refund. This is unacceptable!"}'

# Approve a response
curl -X POST http://localhost:8000/approve \
  -H "Content-Type: application/json" \
  -d '{"email_text": "...", "approved": true}'
```

### 5. Run Tests
```bash
pytest tests/ -v
```

### 6. Docker
```bash
docker build -t email-triage-agent .
docker run -p 8000:8000 --env-file .env email-triage-agent
```

---

## 🏗️ Architecture

```
Email Text
    │
    ├──▶ LLM Call 1: classify_prompt()
    │         │
    │         ▼
    │    { "priority": "urgent", "type": "complaint" }
    │
    └──▶ LLM Call 2: response_prompt(email, classification)
              │
              ▼
         "Dear customer, we apologize for..."
              │
              ▼
         requires_approval: true  ◄── HUMAN GATE
```

---

## 📦 Dataset

**Enron Email Dataset** (Kaggle)
- ~500K real corporate emails
- Public domain (released during Enron investigation)
- Rich variety: complaints, requests, FYIs, scheduling

---

## 🔧 Tech Stack

| Component | Tool |
|-----------|------|
| LLM | OpenAI GPT-4o-mini |
| API | FastAPI + Pydantic |
| Deployment | Docker + Uvicorn |
| Testing | Pytest + unittest.mock |
| Observability | Langfuse (optional) |
