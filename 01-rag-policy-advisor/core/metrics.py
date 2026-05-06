"""
Evaluation metrics for RAG system quality.

Each metric returns a float between 0.0 and 1.0.

In production, these would use LLM-as-judge (RAGAS style).
This implementation provides a lightweight baseline using
text overlap heuristics, with clear extension points for LLM scoring.
"""

import re
from core.llm import call_llm


def _extract_score(text: str) -> float:
    """Extract the first floating point number between 0.0 and 1.0 from a string."""
    match = re.search(r'\b(0\.\d+|1\.0|0|1)\b', text)
    if match:
        return float(match.group(1))
    raise ValueError(f"Could not extract score from: {text}")


def score_faithfulness(answer: str, context: str) -> float:
    """Score how grounded the answer is in the retrieved context."""
    if not answer or not context:
        return 0.0

    prompt = f"""You are an expert evaluator. Rate the FAITHFULNESS of the answer based on the provided context.
An answer is faithful if every claim it makes is explicitly supported by the context.

Context:
{context[:3000]}

Answer:
{answer[:1500]}

Instructions:
1. Identify claims made in the answer.
2. Verify if they exist in the context.
3. Score from 0.0 (completely ungrounded/hallucinated) to 1.0 (perfectly grounded).
4. Return ONLY the numerical score.

Score (0.0 to 1.0):"""

    try:
        score_str = call_llm(prompt, temperature=0.0)
        score = _extract_score(score_str)
        return max(0.0, min(1.0, score))
    except (ValueError, TypeError):
        return 0.5


def score_relevancy(answer: str, question: str) -> float:
    """Score how relevant the answer is to the question."""
    if not answer or not question:
        return 0.0

    prompt = f"""You are an expert evaluator. Rate the RELEVANCY of the answer to the specific question asked.
The answer should directly address the question without excessive irrelevant info.

Question:
{question}

Answer:
{answer[:1500]}

Instructions:
1. Determine if the question was answered.
2. Penalize for irrelevant filler or failing to address the core query.
3. Score from 0.0 (not relevant) to 1.0 (perfectly relevant).
4. Return ONLY the numerical score.

Score (0.0 to 1.0):"""

    try:
        score_str = call_llm(prompt, temperature=0.0)
        score = _extract_score(score_str)
        return max(0.0, min(1.0, score))
    except (ValueError, TypeError):
        return 0.5


def score_correctness(answer: str, ground_truth: str) -> float:
    """Score how correct the answer is compared to ground truth."""
    if not answer or not ground_truth:
        return 0.0

    prompt = f"""You are an expert evaluator. Compare the generated answer to the human-verified ground truth for correctness.

Ground Truth:
{ground_truth}

Generated Answer:
{answer[:1500]}

Instructions:
1. Compare the semantic facts in both texts.
2. Score based on factual accuracy, not word-for-word matching.
3. Score from 0.0 (incorrect/contradictory) to 1.0 (factually perfect).
4. Return ONLY the numerical score.

Score (0.0 to 1.0):"""

    try:
        score_str = call_llm(prompt, temperature=0.0)
        score = _extract_score(score_str)
        return max(0.0, min(1.0, score))
    except (ValueError, TypeError):
        return 0.5
