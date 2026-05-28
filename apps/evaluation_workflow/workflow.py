"""
Evaluation Workflow: LLM-as-a-Judge RAG quality evaluation.
Uses the centralized LLM runtime so all token usage is tracked in real metrics.
"""
from typing import Dict, Any, List
from core.runtime.base_agent import BaseWorkflow
from core.schemas.state import AgentState
from core.runtime.llm import call_llm_structured
from core.tool_registry.registry import ToolRegistry
import core.tool_registry.tools  # Ensure tools are registered
from pydantic import BaseModel
from langgraph.graph import END


class EvalScore(BaseModel):
    faithfulness: float = 0.5
    relevance: float = 0.5
    correctness: float = 0.5
    reasoning: str = ""


# A small built-in test set so the evaluator always has real questions to grade
EVAL_QA_PAIRS = [
    {
        "question": "What is the company refund policy?",
        "expected": "The company guarantees a 30-day refund window for all enterprise products.",
    },
    {
        "question": "How should PII data be handled when using LLMs?",
        "expected": "PII data such as SSN and credit cards must be redacted before sending to third-party LLMs.",
    },
    {
        "question": "What are the support hours?",
        "expected": "Support hours are 9am to 6pm EST.",
    },
]


def retrieve_and_answer_node(state: AgentState) -> AgentState:
    """For each QA pair, retrieve context and generate an answer, then store for judging."""
    qa_results = []

    for pair in EVAL_QA_PAIRS:
        # Retrieve context via the tool registry (same path as the live RAG demo)
        policy_results = ToolRegistry.invoke("policy_search", query=pair["question"])
        context = "\n".join([r["text"] for r in policy_results])

        from core.runtime.llm import call_llm
        answer = call_llm(
            f"Answer this question using only the following context:\n\nCONTEXT:\n{context}\n\nQUESTION: {pair['question']}",
            project="rag-evaluator",
        )

        qa_results.append({
            "question": pair["question"],
            "expected": pair["expected"],
            "context": context,
            "answer": answer,
        })

    state["extracted_data"]["qa_results"] = qa_results
    state["messages"].append({"role": "system", "content": f"Generated answers for {len(qa_results)} QA pairs."})
    return state


def judge_node(state: AgentState) -> AgentState:
    """Use LLM-as-a-judge to score each QA pair on faithfulness, relevance, and correctness."""
    qa_results = state["extracted_data"]["qa_results"]
    scored = []
    totals = {"faithfulness": 0.0, "relevance": 0.0, "correctness": 0.0}

    for pair in qa_results:
        prompt = f"""You are a strict evaluation judge. Score the following answer on three dimensions.
Each score must be between 0.0 and 1.0.

QUESTION: {pair['question']}
EXPECTED ANSWER: {pair['expected']}
ACTUAL ANSWER: {pair['answer']}
CONTEXT USED: {pair['context']}

Score:
- faithfulness: Is the answer grounded in the provided context? (1.0 = fully grounded)
- relevance: Does the answer address the question? (1.0 = perfectly relevant)
- correctness: Does the answer match the expected answer? (1.0 = exact match)

Also provide brief reasoning."""

        score = call_llm_structured(prompt, EvalScore, project="rag-evaluator")
        scored.append({
            **pair,
            "scores": score.model_dump(),
        })
        totals["faithfulness"] += score.faithfulness
        totals["relevance"] += score.relevance
        totals["correctness"] += score.correctness

    n = len(scored)
    aggregate = {
        "avg_faithfulness": round(totals["faithfulness"] / n, 3) if n else 0,
        "avg_relevance": round(totals["relevance"] / n, 3) if n else 0,
        "avg_correctness": round(totals["correctness"] / n, 3) if n else 0,
        "total_evaluated": n,
    }

    # Flag any pair where any score is below 0.7
    flagged = [s for s in scored if any(v < 0.7 for k, v in s["scores"].items() if k != "reasoning")]

    state["extracted_data"]["scores"] = scored
    state["extracted_data"]["aggregate"] = aggregate
    state["extracted_data"]["flagged"] = flagged
    state["messages"].append({"role": "system", "content": f"Evaluation complete. {len(flagged)} flagged items."})
    return state


class EvaluationWorkflow(BaseWorkflow):
    """
    Workflow for RAG Evaluation: End-to-end LLM-as-a-judge pipeline.
    Retrieves context, generates answers, then scores them on faithfulness,
    relevance, and correctness — all with real LLM calls and tracked metrics.
    """
    def _build_graph(self):
        self.graph.add_node("retrieve_answer", retrieve_and_answer_node)
        self.graph.add_node("judge", judge_node)

        self.graph.set_entry_point("retrieve_answer")
        self.graph.add_edge("retrieve_answer", "judge")
        self.graph.add_edge("judge", END)
