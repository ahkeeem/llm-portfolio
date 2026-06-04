import re
from typing import List
from core.runtime.base_agent import BaseWorkflow
from core.schemas.state import AgentState
from core.runtime.llm import call_llm
from core.observability.metrics import metrics
from langgraph.graph import END

# Enterprise Context: Usually fetched from a database/CRM
COMPANY_INFO = """
Company: TechFlow Solutions
Support Hours: 9am - 6pm EST
Refund Policy: 30-day money back guarantee
Contact: support@techflow.io | 1-800-TECH-FLOW
"""

PII_PATTERNS = [
    (r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL_REDACTED]'),
    (r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE_REDACTED]'),
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
    (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[CARD_REDACTED]'),
    (r'\b(?:0[1-9]|[12]\d|3[01])[-/](?:0[1-9]|1[012])[-/](?:19|20)\d{2}\b', '[DOB_REDACTED]'),
    (r'\b[A-Z]{2}\d{6}[A-Z]?\b', '[PASSPORT_REDACTED]'),
]

def _redact_pii(text: str) -> tuple[str, List[str]]:
    found_types = []
    redacted = text
    if not text:
        return redacted, found_types
    for pattern, label in PII_PATTERNS:
        matches = re.findall(pattern, redacted)
        if matches:
            found_types.append(label.strip("[]"))
            redacted = re.sub(pattern, label, redacted)
    return redacted, list(set(found_types))

def scan_node(state: AgentState) -> AgentState:
    """Redact PII before LLM sees it."""
    email_text = state["context"].get("email_text", "")
    redacted, pii_types = _redact_pii(email_text)

    if pii_types:
        metrics.record_pii(pii_types)

    state["extracted_data"]["redacted_text"] = redacted
    state["extracted_data"]["pii_types"] = pii_types
    state["extracted_data"]["pii_found"] = len(pii_types) > 0

    state["context"]["contextual_text"] = f"COMPANY CONTEXT:\n{COMPANY_INFO}\n\nEMAIL TO PROCESS:\n{redacted}"

    state["messages"].append({"role": "system", "content": f"PII scan complete. Types found: {pii_types}"})
    return state

from core.tool_registry.registry import ToolRegistry
# Ensure tools are imported so decorators run

from pydantic import BaseModel

class ClassificationResponse(BaseModel):
    priority: str = "normal"
    type: str = "info"

def classify_node(state: AgentState) -> AgentState:
    contextual_text = state["context"]["contextual_text"]

    # Dynamically invoke policy search from the centralized registry
    policy_results = ToolRegistry.invoke("policy_search", query=contextual_text)
    state["active_tools"].append("policy_search")

    # Inject retrieved policy into prompt
    policy_context = "\n".join([f"- {r['text']}" for r in policy_results])

    prompt = f"""Classify the email. You must output a JSON object containing exactly the keys "priority" and "type".
- "priority" must be one of: urgent, normal, low
- "type" must be one of: complaint, request, info

Consider these company policies when classifying:
{policy_context}

Email:
{contextual_text}"""

    from core.runtime.llm import call_llm_structured
    classification_obj = call_llm_structured(prompt, ClassificationResponse, project="email-triage")

    classification_str = f"Priority: {classification_obj.priority.upper()} | Type: {classification_obj.type.upper()}"
    state["extracted_data"]["classification"] = classification_str
    state["messages"].append({"role": "system", "content": f"Email classified. Referenced {len(policy_results)} policies."})
    return state

def draft_node(state: AgentState) -> AgentState:
    classification = state["extracted_data"]["classification"]
    contextual_text = state["context"]["contextual_text"]

    prompt = f"""You are a professional assistant.

Email Context:
{contextual_text}

Classification:
{classification}

Write a concise, professional reply."""

    response = call_llm(prompt, project="email-triage")
    state["extracted_data"]["draft_response"] = response
    state["requires_approval"] = True
    state["messages"].append({"role": "system", "content": "Draft generated, pending approval."})
    return state

def rag_node(state: AgentState) -> AgentState:
    """Standard RAG node for answering policy questions."""
    question = state["context"].get("question", "")

    # Search policies
    policy_results = ToolRegistry.invoke("policy_search", query=question)
    state["active_tools"].append("policy_search")

    # Store sources for the frontend
    state["extracted_data"]["sources"] = [
        {"content": r["text"], "metadata": {"source": "Corporate Policy v1.2", "section": "Compliance"}}
        for r in policy_results
    ]

    context = "\n".join([r["text"] for r in policy_results])
    prompt = f"Answer this question using only the following context:\n\nCONTEXT:\n{context}\n\nQUESTION: {question}"

    response = call_llm(prompt, project="rag-advisor")
    state["extracted_data"]["draft_response"] = response
    state["messages"].append({"role": "system", "content": f"Answered question using {len(policy_results)} sources."})
    return state

def route_entry(state: AgentState) -> str:
    """Route to scan (email) or rag (question)."""
    if "question" in state["context"]:
        return "rag"
    return "scan"

class ComplianceWorkflow(BaseWorkflow):
    """
    Workflow for Compliance & Triage: Email routing, PII redaction, and policy validation.
    """
    def _build_graph(self):
        self.graph.add_node("scan", scan_node)
        self.graph.add_node("classify", classify_node)
        self.graph.add_node("draft", draft_node)
        self.graph.add_node("rag", rag_node)

        # Branching logic for the entry point
        self.graph.set_conditional_entry_point(
            route_entry,
            {
                "scan": "scan",
                "rag": "rag"
            }
        )

        self.graph.add_edge("scan", "classify")
        self.graph.add_edge("classify", "draft")
        self.graph.add_edge("draft", END)
        self.graph.add_edge("rag", END)
