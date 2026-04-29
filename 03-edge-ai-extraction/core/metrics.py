"""
Evaluation metrics for receipt field extraction.
"""

import json


def field_f1(predicted: dict, ground_truth: dict) -> dict:
    """
    Calculate per-field F1 scores for receipt extraction.

    Args:
        predicted: Predicted fields dict.
        ground_truth: Ground truth fields dict.

    Returns:
        Dict with per-field scores and macro F1.
    """
    fields = ["company", "date", "address", "total"]
    scores = {}

    for field in fields:
        pred = str(predicted.get(field, "")).strip().lower()
        truth = str(ground_truth.get(field, "")).strip().lower()

        if not truth:
            scores[field] = 1.0 if not pred else 0.0
        elif pred == truth:
            scores[field] = 1.0
        elif pred in truth or truth in pred:
            scores[field] = 0.5  # Partial match
        else:
            scores[field] = 0.0

    scores["macro_f1"] = sum(scores.values()) / len(fields)
    return scores


def exact_match(predicted: dict, ground_truth: dict) -> bool:
    """
    Check if all fields match exactly.

    Args:
        predicted: Predicted fields dict.
        ground_truth: Ground truth fields dict.

    Returns:
        True if all fields match.
    """
    fields = ["company", "date", "address", "total"]
    return all(
        str(predicted.get(f, "")).strip().lower() == str(ground_truth.get(f, "")).strip().lower()
        for f in fields
    )
