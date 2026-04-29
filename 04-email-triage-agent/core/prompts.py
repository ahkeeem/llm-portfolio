def classify_prompt(email: str) -> str:
    """Build the classification prompt for email triage."""
    return f"""You are an email classification system.

Classify the email into:
- urgent
- normal
- low

Also label type:
- complaint
- request
- info

Return JSON only, no explanation:
{{
  "priority": "",
  "type": ""
}}

Email:
{email}"""


def response_prompt(email: str, classification: str) -> str:
    """Build the response generation prompt using email + classification context."""
    return f"""You are a professional assistant.

Email:
{email}

Classification:
{classification}

Write a concise, professional reply."""
