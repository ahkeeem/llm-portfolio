from typing import Dict, Any
from core.runtime.base_agent import BaseWorkflow
from core.schemas.state import AgentState
from core.runtime.llm import call_llm_structured
from pydantic import BaseModel
from langgraph.graph import END

class ContractReview(BaseModel):
    risk_level: str
    missing_clauses: list[str]
    flagged_terms: list[str]

def extract_clauses_node(state: AgentState) -> AgentState:
    """Mock node for clause extraction."""
    contract_text = state["context"].get("contract_text", "STANDARD VENDOR AGREEMENT...")
    state["extracted_data"]["contract_length"] = len(contract_text)
    state["messages"].append({"role": "system", "content": "Extracted clauses from contract document."})
    return state

def classify_risk_node(state: AgentState) -> AgentState:
    """Uses LLM to review contract clauses against standard templates."""
    prompt = """You are an expert legal AI.
Review this vendor agreement snippet and identify the risk level (High/Medium/Low),
any missing clauses (like indemnification), and flag risky terms.

Contract:
Standard Vendor Agreement without a limitation of liability clause."""

    review = call_llm_structured(prompt, ContractReview)
    
    state["extracted_data"]["risk_level"] = review.risk_level
    state["extracted_data"]["missing_clauses"] = review.missing_clauses
    state["extracted_data"]["flagged_terms"] = review.flagged_terms
    
    state["requires_approval"] = True if review.risk_level.lower() == "high" else False
    state["messages"].append({"role": "system", "content": f"Contract reviewed. Risk: {review.risk_level}"})
    return state

class LegalWorkflow(BaseWorkflow):
    """
    Workflow for Legal Contract Analysis: Contract risk and clause analysis.
    """
    def _build_graph(self):
        self.graph.add_node("extract", extract_clauses_node)
        self.graph.add_node("classify", classify_risk_node)
        
        self.graph.set_entry_point("extract")
        self.graph.add_edge("extract", "classify")
        self.graph.add_edge("classify", END)
