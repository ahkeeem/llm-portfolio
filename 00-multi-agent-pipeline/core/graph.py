from app.state import AgentState


def should_retry_policy(state: AgentState):
    """
    Conditional logic: If Auditor (Agent 3) fails the draft, 
    route back to Analyst (Agent 2) for re-reasoning.
    Max 3 revision attempts before escalating to human.
    """
    if not state.get("audit_passed", True) and state.get("revision_count", 0) < 3:
        return "re-reason"
    return "finalize"


def create_pipeline():
    """
    Build and compile the 4-agent LangGraph pipeline.
    
    Imports are deferred to runtime so the module can be imported
    for unit testing even when langgraph or project dependencies
    are not installed.
    """
    from langgraph.graph import StateGraph, END

    # Deferred imports: each adapter touches a different project's core/
    from core.nodes.extract_node import extract_node
    from core.nodes.policy_node import policy_node
    from core.nodes.audit_node import audit_node
    from core.nodes.triage_node import triage_node

    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("extract", extract_node)
    workflow.add_node("policy_analyze", policy_node)
    workflow.add_node("audit", audit_node)
    workflow.add_node("triage", triage_node)

    # 2. Define Edges & Transitions
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "policy_analyze")
    workflow.add_edge("policy_analyze", "audit")

    # 3. Add Conditional Routing (The Auditor's Power)
    workflow.add_conditional_edges(
        "audit",
        should_retry_policy,
        {
            "re-reason": "policy_analyze",
            "finalize": "triage"
        }
    )

    workflow.add_edge("triage", END)
    
    return workflow.compile()
