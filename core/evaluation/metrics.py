"""
Evaluation metrics for RAG system quality.

Metrics implemented:
  - Faithfulness (LLM-as-judge): Is the answer grounded in the context?
  - Relevancy (LLM-as-judge): Does the answer address the question?
  - Correctness (LLM-as-judge): Does the answer match the ground truth?
  - Context Recall (LLM-as-judge): Does the context contain the ground truth?
  - ROUGE-L (lexical): Longest common subsequence overlap with ground truth.

Each metric returns a float between 0.0 and 1.0.
"""

import re
from core.llm import call_llm


def _extract_score(text: str) -> float:
    """Extract the first floating point number between 0.0 and 1.0 from a string."""
    match = re.search(r'\b(0\.\d+|1\.0|0|1)\b', text)
    if match:
        return float(match.group(1))
    raise ValueError(f"Could not extract score from: {text}")


def _lcs_length(x: list, y: list) -> int:
    """Compute length of the longest common subsequence."""
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def score_rouge_l(answer: str, ground_truth: str) -> float:
    """
    Compute ROUGE-L F1 score between the generated answer and the ground truth.
    Uses the longest common subsequence at the word level.
    """
    if not answer or not ground_truth:
        return 0.0

    answer_tokens = answer.lower().split()
    truth_tokens = ground_truth.lower().split()

    if not answer_tokens or not truth_tokens:
        return 0.0

    lcs = _lcs_length(answer_tokens, truth_tokens)
    precision = lcs / len(answer_tokens)
    recall = lcs / len(truth_tokens)

    if precision + recall == 0:
        return 0.0

    f1 = 2 * precision * recall / (precision + recall)
    return round(f1, 4)


def score_faithfulness(answer: str, context: str) -> float:
    """Score how grounded the answer is in the retrieved context (LLM-as-judge)."""
    if not answer or not context:
        return 0.0

    prompt = f"""You are an expert evaluator for Retrieval-Augmented Generation systems.
Rate the FAITHFULNESS of the answer based on the provided context.
An answer is faithful if every claim it makes is explicitly supported by the context.

Context:
{context[:3000]}

Answer:
{answer[:1500]}

Instructions:
1. List the key claims in the answer.
2. For each claim, check if it is directly supported by the context.
3. Penalise any hallucinated or unsupported claims.
4. Score from 0.0 (completely hallucinated) to 1.0 (perfectly grounded).
5. Return ONLY the numerical score, nothing else.

Score:"""

    try:
        score_str = call_llm(prompt, temperature=0.0)
        return max(0.0, min(1.0, _extract_score(score_str)))
    except (ValueError, TypeError):
        return 0.5


def score_relevancy(answer: str, question: str) -> float:
    """Score how relevant the answer is to the question (LLM-as-judge)."""
    if not answer or not question:
        return 0.0

    prompt = f"""You are an expert evaluator for Retrieval-Augmented Generation systems.
Rate the RELEVANCY of the answer to the specific question asked.
A relevant answer directly addresses the question without excessive filler.

Question:
{question}

Answer:
{answer[:1500]}

Instructions:
1. Does the answer address the core question?
2. Penalise irrelevant tangents, padding, or failure to answer.
3. Score from 0.0 (completely irrelevant) to 1.0 (perfectly relevant).
4. Return ONLY the numerical score, nothing else.

Score:"""

    try:
        score_str = call_llm(prompt, temperature=0.0)
        return max(0.0, min(1.0, _extract_score(score_str)))
    except (ValueError, TypeError):
        return 0.5


def score_correctness(answer: str, ground_truth: str) -> float:
    """Score factual correctness compared to the human-verified ground truth (LLM-as-judge)."""
    if not answer or not ground_truth:
        return 0.0

    prompt = f"""You are an expert evaluator. Compare the generated answer to the human-verified ground truth.

Ground Truth:
{ground_truth}

Generated Answer:
{answer[:1500]}

Instructions:
1. Compare the semantic facts in both texts.
2. Score based on factual accuracy, not word-for-word matching.
3. Penalise contradictions or missing key facts.
4. Score from 0.0 (incorrect/contradictory) to 1.0 (factually perfect).
5. Return ONLY the numerical score, nothing else.

Score:"""

    try:
        score_str = call_llm(prompt, temperature=0.0)
        return max(0.0, min(1.0, _extract_score(score_str)))
    except (ValueError, TypeError):
        return 0.5


def score_context_recall(context: str, ground_truth: str) -> float:
    """
    Score whether the retrieved context contains the information needed to
    produce the ground truth answer (LLM-as-judge).
    A high score means the retrieval pipeline is surfacing the right chunks.
    """
    if not context or not ground_truth:
        return 0.0

    prompt = f"""You are an expert evaluator for RAG retrieval quality.
Given the ground truth answer and the retrieved context, determine what
fraction of the ground truth information is present in the context.

Ground Truth Answer:
{ground_truth}

Retrieved Context:
{context[:3000]}

Instructions:
1. Break the ground truth into individual facts/claims.
2. Check how many of those facts appear in the context.
3. Score from 0.0 (none of the facts are present) to 1.0 (all facts are present).
4. Return ONLY the numerical score, nothing else.

Score:"""

    try:
        score_str = call_llm(prompt, temperature=0.0)
        return max(0.0, min(1.0, _extract_score(score_str)))
    except (ValueError, TypeError):
        return 0.5
