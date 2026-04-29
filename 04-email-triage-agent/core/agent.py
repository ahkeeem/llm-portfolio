import re
from core.prompts import classify_prompt, response_prompt
from core.llm import call_llm

# Enterprise Context: Usually fetched from a database/CRM
COMPANY_INFO = """
Company: TechFlow Solutions
Support Hours: 9am - 6pm EST
Refund Policy: 30-day money back guarantee
Contact: support@techflow.io | 1-800-TECH-FLOW
"""

def _scan_pii(text: str) -> bool:
    """Simulate a PII scan for sensitive information (Emails, SSNs, etc)."""
    # Simple regex for demonstration
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\d{3}-\d{3}-\d{4}'
    return bool(re.search(email_pattern, text) or re.search(phone_pattern, text))

def process_email(email_text: str) -> dict:
    """
    Two-step agent pipeline with Privacy Scan and Company Context.
    """
    # 1. Privacy Scan
    pii_found = _scan_pii(email_text)
    
    # 2. Inject Company Context into the prompt
    contextual_text = f"COMPANY CONTEXT:\n{COMPANY_INFO}\n\nEMAIL TO PROCESS:\n{email_text}"

    # 3. Pipeline
    classification = call_llm(classify_prompt(contextual_text))
    response = call_llm(response_prompt(contextual_text, classification))

    return {
        "classification": classification,
        "response": response,
        "privacy_scan": "PASSED" if not pii_found else "FLAGGED (Contains PII)",
        "requires_approval": True,
    }
