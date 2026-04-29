# 🧠 Project 1 — RAG Policy Advisor

> Retrieval-Augmented Generation system over UK Government policy documents and arXiv research papers.

---

## 🎯 Problem

Policy analysts and researchers spend hours searching through dense regulatory documents and academic papers. Finding relevant passages across hundreds of documents is slow, error-prone, and doesn't scale.

## 💡 Solution

A RAG system that:
1. **Ingests** UK Gov policy PDFs and arXiv papers into a vector store
2. **Retrieves** the most relevant passages for any natural language query
3. **Generates** grounded, source-cited answers using GPT-4o-mini

## 🧑‍🔬 Control (Human-in-the-Loop)

| Gate | Description |
|------|-------------|
| Source citations | Every answer includes retrieved document references |
| Bad answer flagging | Users can flag low-quality responses for prompt/chunking improvement |
| Missing source review | Analysts verify coverage gaps in the document corpus |

## 📊 Result

| Metric | Value |
|--------|-------|
| Token cost per query | ~1,500 tokens (~$0.0002) |
| Chunk retrieval (top-k) | 5 chunks × 512 tokens |
| Context relevancy | Evaluated via Project 2 |
| Faithfulness | Evaluated via Project 2 |

---

## 📁 Structure

```
01-rag-policy-advisor/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI query endpoint
├── core/
│   ├── __init__.py
│   ├── rag.py                # RAG chain (retrieve + generate)
│   ├── embeddings.py         # Embedding wrapper
│   ├── vectorstore.py        # ChromaDB interface
│   └── prompts.py            # RAG prompt templates
├── data/
│   ├── raw/                  # Original PDFs / papers
│   └── processed/            # Chunked text (JSONL)
├── scripts/
│   ├── ingest_documents.py   # PDF parsing + chunking
│   └── download_arxiv.py     # arXiv dataset download
├── tests/
│   ├── test_rag.py
│   └── test_embeddings.py
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
cd 01-rag-policy-advisor
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your OPENAI_API_KEY
```

### 2. Prepare Data
```bash
# Download UK Gov documents into data/raw/
python scripts/download_arxiv.py       # Download arXiv subset
python scripts/ingest_documents.py     # Parse, chunk, embed → ChromaDB
```

### 3. Run
```bash
uvicorn app.main:app --reload
```

### 4. Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the UK regulations on AI transparency?"}'
```

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│  Embed Query     │ ── text-embedding-3-small
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  ChromaDB Search │ ── top-k=5 similarity
└──────┬──────────┘
       │  relevant chunks + metadata
       ▼
┌─────────────────┐
│  RAG Prompt      │ ── context + question → LLM
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Answer + Sources│
└─────────────────┘
```

---

## 📦 Datasets

| Source | Type | Access |
|--------|------|--------|
| UK Government | Policy & consultation docs | https://www.gov.uk/search/policy-papers-and-consultations |
| arXiv | Research papers (AI/ML subset) | HuggingFace `arxiv_dataset` |

---

## 🔧 Tech Stack

| Component | Tool |
|-----------|------|
| LLM | OpenAI GPT-4o-mini |
| Embeddings | text-embedding-3-small |
| Vector DB | ChromaDB |
| API | FastAPI + Pydantic |
| PDF Parsing | PyPDF2 / pdfplumber |
| Deployment | Docker + Uvicorn |
