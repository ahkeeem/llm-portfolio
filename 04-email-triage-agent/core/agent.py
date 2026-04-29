from core.prompts import classify_prompt, response_prompt
from core.llm import call_llm


def process_email(email_text: str) -> dict:
    """
    Two-step agent pipeline:
    1. Classify the email (priority + type)
    2. Generate a draft response based on classification

    Returns dict with classification, response, and approval flag.
    """
    classification = call_llm(classify_prompt(email_text))
    response = call_llm(response_prompt(email_text, classification))

    return {
        "classification": classification,
        "response": response,
        "requires_approval": True,  # Human-in-the-loop gate
    }
