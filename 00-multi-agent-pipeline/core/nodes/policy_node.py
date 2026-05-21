import sys
import os

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../01-rag-policy-advisor"))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from core.rag import query_rag
from app.state import AgentState

# Clean up path to prevent namespace collisions
if sys.path[0] == project_path:
    sys.path.pop(0)

def policy_node(state: AgentState):
    """
    Agent 2: Policy Analyst Agent.
    Retrieves policy evidence and generates a verdict.
    """
    print("--- AGENT 2: ANALYZING POLICY ---")
    
    extracted = state.get("extracted_data", {})
    # Build query based on extracted claim
    company = extracted.get("company", "TechFlow Solutions")
    total = extracted.get("total", "unknown amount")
    item = extracted.get("item", "purchase")
    
    query = f"What is the refund policy for {item} from {company} with total {total}?"
    
    result = query_rag(query)
    
    return {
        "policy_verdict": result.get("answer", ""),
        "policy_citations": [src["metadata"].get("source", "Policy document") for src in result.get("sources", [])],
        "policy_context": result.get("retrieved_context", ""),
        "status": "policy_analyzed"
    }
