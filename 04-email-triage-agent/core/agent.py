import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from core.prompts import classify_prompt, response_prompt
from core.llm import call_llm

# Enterprise Context: Usually fetched from a database/CRM
COMPANY_INFO = """
Company: TechFlow Solutions
Support Hours: 9am - 6pm EST
Refund Policy: 30-day money back guarantee
Contact: support@techflow.io | 1-800-TECH-FLOW
"""

# PII patterns with redaction labels
PII_PATTERNS = [
    (r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL_REDACTED]'),
    (r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE_REDACTED]'),
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
    (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[CARD_REDACTED]'),
    (r'\b(?:0[1-9]|[12]\d|3[01])[-/](?:0[1-9]|1[012])[-/](?:19|20)\d{2}\b', '[DOB_REDACTED]'),
    (r'\b[A-Z]{2}\d{6}[A-Z]?\b', '[PASSPORT_REDACTED]'),  # UK/EU passport pattern
]


def _redact_pii(text: str) -> tuple[str, List[str]]:
    """
    Scan for PII, redact it, and return the cleaned text + list of found PII types.
    The LLM never processes raw PII — only redacted placeholders.
    """
    found_types = []
    redacted = text
    for pattern, label in PII_PATTERNS:
        matches = re.findall(pattern, redacted)
        if matches:
            found_types.append(label.strip("[]"))
            redacted = re.sub(pattern, label, redacted)
    return redacted, found_types


class AgentState(TypedDict):
    email_text: str          # Original (kept server-side only, never logged)
    redacted_text: str       # PII-stripped version sent to LLM
    pii_types: List[str]     # List of detected PII types e.g. ["EMAIL_REDACTED"]
    pii_found: bool
    contextual_text: str
    classification: str
    response: str
    feedback: str
    revision_count: int


def scan_node(state: AgentState):
    """Redact PII before any LLM call. The LLM only ever sees redacted_text."""
    redacted, pii_types = _redact_pii(state["email_text"])
    pii_found = len(pii_types) > 0
    # LLM receives the redacted version only
    contextual_text = f"COMPANY CONTEXT:\n{COMPANY_INFO}\n\nEMAIL TO PROCESS:\n{redacted}"
    return {
        "redacted_text": redacted,
        "pii_types": pii_types,
        "pii_found": pii_found,
        "contextual_text": contextual_text,
    }


def classify_node(state: AgentState):
    classification = call_llm(classify_prompt(state["contextual_text"]))
    return {"classification": classification}


def draft_node(state: AgentState):
    if state.get("feedback"):
        prompt = f"REVISE THIS DRAFT based on human feedback: {state['feedback']}\n\nORIGINAL DRAFT: {state['response']}\n\nORIGINAL EMAIL (redacted): {state['redacted_text']}"
        response = call_llm(prompt)
        return {"response": response, "revision_count": state.get("revision_count", 0) + 1}
    else:
        response = call_llm(response_prompt(state["contextual_text"], state.get("classification", "")))
        return {"response": response, "revision_count": 0}


# Build the Cyclic StateGraph
workflow = StateGraph(AgentState)
workflow.add_node("scan", scan_node)
workflow.add_node("classify", classify_node)
workflow.add_node("draft", draft_node)

workflow.set_entry_point("scan")
workflow.add_edge("scan", "classify")
workflow.add_edge("classify", "draft")
workflow.add_edge("draft", END)

app_graph = workflow.compile()


def process_email(email_text: str) -> dict:
    """
    Executes the LangGraph pipeline. PII is redacted before the first LLM call.
    """
    initial_state = {
        "email_text": email_text,
        "redacted_text": "",
        "pii_types": [],
        "pii_found": False,
        "contextual_text": "",
        "classification": "",
        "response": "",
        "feedback": "",
        "revision_count": 0,
    }

    result = app_graph.invoke(initial_state)

    pii_detail = (
        f"FLAGGED — Detected: {', '.join(result['pii_types'])}"
        if result["pii_found"] else "PASSED"
    )

    return {
        "classification": result["classification"],
        "response": result["response"],
        "privacy_scan": pii_detail,
        "pii_redacted": result["pii_found"],
        "requires_approval": True,
    }
