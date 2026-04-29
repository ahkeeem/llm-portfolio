# 🏛️ Technical Architecture

> System design, data flows, and integration patterns across all 4 LLM portfolio projects.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT / API LAYER                     │
│              FastAPI + Pydantic Request Models               │
└─────────────┬──────────┬──────────┬──────────┬──────────────┘
              │          │          │          │
         ┌────▼───┐ ┌───▼────┐ ┌──▼───┐ ┌───▼─────┐
         │  RAG   │ │  EVAL  │ │ FINE │ │  AGENT  │
         │ Engine │ │ Engine │ │ TUNE │ │ Engine  │
         └────┬───┘ └───┬────┘ └──┬───┘ └───┬─────┘
              │          │         │          │
         ┌────▼───┐ ┌───▼────┐ ┌──▼───┐ ┌───▼─────┐
         │Vector  │ │Metrics │ │HF    │ │LLM      │
         │Store   │ │Store   │ │PEFT  │ │Pipeline │
         └────┬───┘ └───┬────┘ └──┬───┘ └───┬─────┘
              │          │         │          │
         ┌────▼──────────▼─────────▼──────────▼─────┐
         │           LLM PROVIDER (OpenAI)           │
         │         + Observability (Langfuse)         │
         └───────────────────────────────────────────┘
```

---

## Project 1 — RAG Policy Advisor

### Data Flow

```
UK Gov PDFs / arXiv Papers
        │
        ▼
┌──────────────┐
│  Ingestion   │ ── scripts/ingest.py
│  (chunking)  │
└──────┬───────┘
       │  text chunks + metadata
       ▼
┌──────────────┐
│  Embeddings  │ ── OpenAI text-embedding-3-small
└──────┬───────┘
       │  vectors
       ▼
┌──────────────┐
│  ChromaDB    │ ── persistent vector store
└──────┬───────┘
       │  similarity search
       ▼
┌──────────────┐     ┌────────────┐
│  RAG Chain   │────▶│  Response   │
│  (retrieve   │     │  + Sources  │
│   + generate)│     └─────┬──────┘
└──────────────┘           │
                           ▼
                  ┌────────────────┐
                  │ Human Review   │
                  │ (bad answers?) │
                  └────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Chunk size: 512 tokens, overlap: 64 | Balances context retention vs retrieval precision |
| Embedding: `text-embedding-3-small` | Cost-effective, strong performance on policy text |
| Vector DB: ChromaDB | Zero-infra local dev, easy to swap for Pinecone/Weaviate |
| Reranking: optional cross-encoder | Improves top-k relevance at inference cost |

### Token Budget Strategy

- **Ingestion**: One-time embedding cost (~$0.02/1M tokens)
- **Query**: ~800 tokens context + ~200 tokens query = ~1000 tokens/request
- **Response**: ~500 tokens average → **~1500 tokens total per query**

---

## Project 2 — RAG Evaluator

### Data Flow

```
Project 1 RAG System
        │
        ▼
┌──────────────────┐
│  QA Pair Builder  │ ── scripts/generate_qa.py
│  (LLM + manual)  │
└──────┬───────────┘
       │  30-50 QA pairs (JSON)
       ▼
┌──────────────────┐
│  Evaluation Run   │ ── core/evaluator.py
│  (per-question)   │
└──────┬───────────┘
       │  metrics per pair
       ▼
┌──────────────────┐
│  Metric Aggregation│
│  faithfulness,     │
│  relevancy,        │
│  answer_correctness│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Report / Dashboard│
└──────────────────┘
```

### Metrics

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Faithfulness | Is the answer grounded in retrieved context? | > 0.85 |
| Answer Relevancy | Does the answer address the question? | > 0.80 |
| Context Precision | Are the top-k retrieved chunks relevant? | > 0.75 |
| Answer Correctness | Does it match ground truth? | > 0.70 |

### Token Budget Strategy

- **QA Generation**: ~2000 tokens × 50 pairs = ~100K tokens (one-time)
- **Evaluation Run**: ~1500 tokens × 50 pairs = ~75K tokens per run
- **Total per eval cycle**: ~175K tokens ≈ **$0.03 with gpt-4o-mini**

---

## Project 3 — Receipt Fine-tuner

### Data Flow

```
SROIE Dataset (HuggingFace)
        │
        ▼
┌──────────────────┐
│  Data Cleaning    │ ── scripts/prepare_data.py
│  (format → JSONL) │
└──────┬───────────┘
       │  train.jsonl / val.jsonl
       ▼
┌──────────────────┐
│  Base Model       │ ── e.g., Mistral-7B / Phi-3
│  + LoRA Adapter   │
└──────┬───────────┘
       │  PEFT fine-tuning
       ▼
┌──────────────────┐
│  Evaluation       │ ── F1, exact match on fields
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Inference API    │ ── FastAPI endpoint
│  (receipt → JSON) │
└──────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| LoRA rank: 16 | Good balance of parameter efficiency vs quality |
| Base model: Phi-3-mini | Small enough for local training, strong instruction following |
| Training: 3 epochs | Prevents overfitting on small dataset |
| Quantization: 4-bit | Enables training on consumer GPU (16GB VRAM) |

### Token Budget Strategy

- **Fine-tuning**: Local compute (no API token cost)
- **Inference**: ~300 tokens input + ~100 tokens output = **~400 tokens/request**
- **Validation**: 200 samples × 400 tokens = ~80K tokens if using API eval

---

## Project 4 — Email Triage Agent

### Data Flow

```
Enron Email Dataset (Kaggle)
        │
        ▼
┌──────────────────┐
│  Email Input      │ ── app/main.py (FastAPI)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Classification   │ ── Step 1: classify + prioritize
│  (LLM call #1)   │
└──────┬───────────┘
       │  { priority, type }
       ▼
┌──────────────────┐
│  Response Draft   │ ── Step 2: generate reply
│  (LLM call #2)   │
└──────┬───────────┘
       │  draft response
       ▼
┌──────────────────┐
│  Human Approval   │ ── requires_approval: true
│  Gate             │
└──────┬───────────┘
       │  approved / rejected
       ▼
┌──────────────────┐
│  Send / Archive   │
└──────────────────┘
```

### Agent Pipeline (2-Step)

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

### Token Budget Strategy

- **Classification**: ~400 tokens prompt + ~50 tokens response = ~450 tokens
- **Response Draft**: ~600 tokens prompt + ~200 tokens response = ~800 tokens
- **Total per email**: **~1250 tokens ≈ $0.0002 with gpt-4o-mini**
- **Batch 1000 emails**: ~1.25M tokens ≈ **$0.19**

---

## Cross-Cutting Concerns

### Observability (Langfuse)

```
All LLM Calls
     │
     ▼
┌──────────────┐
│   Langfuse   │
│   Tracing    │
└──────┬───────┘
       │
       ├── Latency per call
       ├── Token usage per call
       ├── Cost tracking
       ├── Error rates
       └── Prompt versioning
```

### Deployment Pattern

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Dockerfile  │────▶│  Docker Image │────▶│  Container   │
│  per project │     │  (slim Python)│     │  (uvicorn)   │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| API | Pydantic validation + HTTP error codes |
| LLM | Retry with exponential backoff (max 3) |
| Vector DB | Graceful fallback if no results |
| Agent | Approval gate blocks on failure |

### Security

| Concern | Mitigation |
|---------|------------|
| API Keys | `.env` files, never committed |
| Prompt Injection | Input sanitization + output validation |
| Data Privacy | Enron dataset is public; no PII in production |
| Rate Limiting | FastAPI middleware throttle |

---

## Token Usage Summary (All Projects)

| Project | Per Request | Batch (100) | Monthly Est. |
|---------|-------------|-------------|-------------|
| RAG | ~1,500 tokens | 150K | ~$2.25 |
| Eval | ~1,500 tokens | 75K (per run) | ~$0.50 |
| Fine-tune | ~400 tokens | 40K | ~$0.60 |
| Agent | ~1,250 tokens | 125K | ~$1.88 |
| **Total** | | | **~$5.23/mo** |

*All estimates use gpt-4o-mini pricing ($0.15/1M input, $0.60/1M output).*
