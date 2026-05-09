from typing import TypedDict, Annotated, Any, Dict, List, Optional
import operator

class AgentState(TypedDict):
    """
    Shared state schema for all Enterprise Agent Runtime workflows.
    LangGraph StateGraph relies on this schema.
    """
    workflow_id: str
    session_id: str
    
    # Annotated with operator.add so messages are appended rather than overwritten
    messages: Annotated[list[Any], operator.add]
    
    # Domain specific context and data
    context: Dict[str, Any]
    extracted_data: Dict[str, Any]
    
    # Centralized tool tracking
    active_tools: List[str]
    
    # HITL (Human In The Loop) capabilities
    requires_approval: bool
    approval_status: Optional[str]  # "approved", "rejected", "pending"
    
    # Error state and routing flags
    error: Optional[str]
    
    # Universal tracking metadata (tokens, costs, latency)
    metadata: Dict[str, Any]
