# 🧠 Senior LLM Engineer — Portfolio Projects

> **"I specialize in moving LLM prototypes from 'Unpredictable Chatbots' to 'Observable Enterprise Systems' with a focus on ROI and Data Sovereignty."**

Welcome to my portfolio. I build **observable AI**, not just wrappers. These 4 production-grade systems demonstrate end-to-end mastery of retrieval, evaluation, fine-tuning, and stateful autonomous agents. I mitigate hallucinations, handle failure modes (prompt injection, rate limits), and ensure you never experience vendor lock-in by designing systems easily portable between OpenAI and Open Source models (Llama 3, Mistral).

### 📉 Token Stewardship & Cost Optimization
**Optimizing for cost through semantic caching and prompt compression.** 
Across these 4 projects, the total estimated cloud inference cost is **~$6/month** at moderate volume. Efficient token usage is a first-class feature of my architecture.

## 📦 Projects

| # | Project | Domain | Core Skill | Dataset | Live API |
|---|---------|--------|------------|---------|----------|
| 1 | [RAG Policy Advisor](./01-rag-policy-advisor/) | Regulatory / Research | Retrieval-Augmented Generation | UK Gov + arXiv | [▶️ Loom Demo](#) \| [Swagger UI](https://rag-gdzc.onrender.com/docs) |
| 2 | [RAG Evaluator](./02-rag-evaluator/) | Quality Assurance | LLM-as-a-Judge Eval Pipelines | Custom QA (from P1) | [▶️ Loom Demo](#) \| Local / Docker |
| 3 | [Edge-AI Extraction Pipeline](./03-edge-ai-extraction/) | Edge AI / OCR | Local OCR + SLM Fine-tuning | SROIE Dataset | [▶️ Loom Demo](#) \| Local / Edge |
| 4 | [Email Triage Agent](./04-email-triage-agent/) | Enterprise Ops | Stateful Agents (LangGraph) | Enron Email (Kaggle) | [▶️ Loom Demo](#) \| [Swagger UI](https://email-x1cn.onrender.com/docs) |

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

## 🚀 Production Observability & Upgrades

- **Observability (Langfuse/LangSmith)**: Real-time tracing of LLM chains. *[See example trace below demonstrating a bottleneck resolution during RAG generation](#)*
- **Dashboard**: Streamlit admin panels per project
- **CI/CD**: GitHub Actions for test + deploy
- **Caching**: Redis/GPTCache layer for semantic caching to drastically reduce repetitive API calls.

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
