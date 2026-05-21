from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # --- Input Data ---
    raw_input: str              # Original email text or image path
    claim_id: str               # Unique identifier for the transaction
    
    # --- Agent 1: Extraction Outputs ---
    extracted_data: Dict[str, Any]  # JSON from SLM (e.g., total, vendor, date)
    extraction_confidence: float
    
    # --- Agent 2: Policy Analyst Outputs ---
    policy_verdict: str         # The RAG-generated answer
    policy_citations: List[str]  # Sources from the Vector DB
    policy_context: str         # The raw retrieved context chunks
    
    # --- Agent 3: Internal Auditor Outputs ---
    audit_scores: Dict[str, float] # {faithfulness: 0.9, relevancy: 0.8}
    audit_feedback: Optional[str]   # Feedback if scores are low
    audit_passed: bool
    
    # --- Agent 4: Triage/Email Outputs ---
    final_email_draft: str
    requires_approval: bool     # Human gate flag
    human_feedback: Optional[str] # Input from the human reviewer
    
    # --- Metadata ---
    trace_id: str
    revision_count: int         # Track internal retries
    status: str                 # e.g., "extracting", "auditing", "ready_for_human"
