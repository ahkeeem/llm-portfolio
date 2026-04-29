import re
from typing import TypedDict
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

def _scan_pii(text: str) -> bool:
    """Simulate a PII scan for sensitive information (Emails, SSNs, etc)."""
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\d{3}-\d{3}-\d{4}'
    return bool(re.search(email_pattern, text) or re.search(phone_pattern, text))

class AgentState(TypedDict):
    email_text: str
    contextual_text: str
    pii_found: bool
    classification: str
    response: str
    feedback: str
    revision_count: int

def scan_node(state: AgentState):
    pii_found = _scan_pii(state["email_text"])
    contextual_text = f"COMPANY CONTEXT:\n{COMPANY_INFO}\n\nEMAIL TO PROCESS:\n{state['email_text']}"
    return {"pii_found": pii_found, "contextual_text": contextual_text}

def classify_node(state: AgentState):
    classification = call_llm(classify_prompt(state["contextual_text"]))
    return {"classification": classification}

def draft_node(state: AgentState):
    if state.get("feedback"):
        # Cyclic routing: Revise draft based on human feedback
        prompt = f"REVISE THIS DRAFT based on human feedback: {state['feedback']}\n\nORIGINAL DRAFT: {state['response']}\n\nORIGINAL EMAIL: {state['email_text']}"
        response = call_llm(prompt)
        return {"response": response, "revision_count": state.get("revision_count", 0) + 1}
    else:
        # First pass
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
    Executes the LangGraph pipeline for the initial run.
    """
    initial_state = {
        "email_text": email_text,
        "contextual_text": "",
        "pii_found": False,
        "classification": "",
        "response": "",
        "feedback": "",
        "revision_count": 0
    }
    
    result = app_graph.invoke(initial_state)
    
    return {
        "classification": result["classification"],
        "response": result["response"],
        "privacy_scan": "PASSED" if not result["pii_found"] else "FLAGGED (Contains PII)",
        "requires_approval": True,
    }
