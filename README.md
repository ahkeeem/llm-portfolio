# 🧠 Senior LLM Engineer — Portfolio Projects

> **4 production-grade LLM systems** demonstrating end-to-end mastery of retrieval, evaluation, fine-tuning, and autonomous agents — each with human-in-the-loop controls.

---

## 📦 Projects

| # | Project | Domain | Core Skill | Dataset |
|---|---------|--------|------------|---------|
| 1 | [RAG Policy Advisor](./01-rag-policy-advisor/) | Regulatory / Research | Retrieval-Augmented Generation | UK Gov + arXiv |
| 2 | [RAG Evaluator](./02-rag-evaluator/) | Quality Assurance | LLM Evaluation Pipelines | Custom QA (from P1) |
| 3 | [Receipt Fine-tuner](./03-receipt-finetuner/) | Document AI | Supervised Fine-tuning | SROIE (HuggingFace) |
| 4 | [Email Triage Agent](./04-email-triage-agent/) | Enterprise Ops | Autonomous Agents | Enron Email (Kaggle) |

---

## 🏗️ Consistent Repo Structure

Every project follows the same layout for client confidence and maintainability:

```
project_name/
├── app/                # FastAPI / agent / UI entry points
├── core/               # Business logic (rag, agent, eval, etc.)
├── data/               # Raw + processed datasets
├── scripts/            # Ingestion, training, migration scripts
├── tests/              # Unit + integration tests
├── Dockerfile          # Container-ready deployment
├── requirements.txt    # Pinned dependencies
└── README.md           # Project-specific docs
```

---

## 🧑‍🔬 Human-in-the-Loop (Every Project)

Each system includes explicit human oversight:

| Project | Human Reviews | Action |
|---------|--------------|--------|
| RAG | Bad answers, missing sources | Improve chunking / prompts |
| Evaluation | Ground truth labels, low scores | Flag for re-annotation |
| Fine-tuning | Training data, incorrect labels | Clean before re-train |
| Agent | Draft replies before send | `requires_approval: true` gate |

---

## 💡 Positioning (Per Project)

Each project README clearly communicates:

1. **Problem** — Real-world pain point
2. **Solution** — LLM system architecture
3. **Control** — Human-in-the-loop safeguards
4. **Result** — Metrics, demo, or deployment evidence

---

## 🚀 Optional Upgrades

- **Observability**: Langfuse integration for tracing LLM calls
- **Dashboard**: Streamlit admin panels per project
- **CI/CD**: GitHub Actions for test + deploy

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| LLM | OpenAI GPT-4o-mini, HuggingFace Transformers |
| Framework | LangChain, FastAPI |
| Vector DB | ChromaDB / FAISS |
| Fine-tuning | HuggingFace PEFT / LoRA |
| Eval | RAGAS, custom metrics |
| Observability | Langfuse (optional) |
| Deployment | Docker, Uvicorn |

---

## 📄 Documentation

- [Technical Architecture](./ARCHITECTURE.md) — System design, data flows, integration patterns
- [Skills & Directions](./SKILLS.md) — Competency matrix and growth roadmap

---

*Built by a Senior LLM Engineer — production-first, human-in-the-loop, metrics-driven.*
