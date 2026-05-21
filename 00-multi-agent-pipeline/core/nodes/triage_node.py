import sys
import os

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../04-email-triage-agent"))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from core.llm import call_llm
from app.state import AgentState

# Clean up path to prevent namespace collisions
if sys.path[0] == project_path:
    sys.path.pop(0)

def triage_node(state: AgentState):
    """
    Agent 4: Triage/Email Agent.
    Drafts the final response incorporating the audited policy verdict.
    """
    print("--- AGENT 4: TRIAGING & DRAFTING EMAIL ---")
    
    raw_email = state["raw_input"]
    verdict = state.get("policy_verdict", "No specific policy details found.")
    extracted = state.get("extracted_data", {})
    
    prompt = f"""You are a professional customer support representative.
Write a professional, polite, and clear email response to the customer.

Original Customer Inquiry:
{raw_email}

Extracted Transaction Data:
{extracted}

Audited Compliance Policy Verdict:
{verdict}

Instructions:
1. Reference the customer's specific concern.
2. Provide a clear decision based strictly on the Audited Compliance Policy Verdict.
3. Be professional and empathetic.
4. Keep the draft ready for human approval.

Final Email Draft:"""

    response = call_llm(prompt)
    
    return {
        "final_email_draft": response,
        "requires_approval": True,
        "status": "ready_for_human"
    }
