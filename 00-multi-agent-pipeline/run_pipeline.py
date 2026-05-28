import sys
import os

# Ensure the root of the pipeline is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.graph import create_pipeline
from app.state import AgentState

def run_demo():
    print("==================================================")
    print("🚀 Running Autonomous Compliance Desk Demo Pipeline")
    print("==================================================")

    # 1. Initialize State
    initial_state = {
        "raw_input": "Dear Whole Foods support, I purchased Organic Apples and Almond Milk on 05/15/2026 for $11.48 at store #10402 in SF. I need a refund as the item was bad.",
        "claim_id": "claim-1001",
        "extracted_data": {},
        "extraction_confidence": 0.0,
        "policy_verdict": "",
        "policy_citations": [],
        "policy_context": "",
        "audit_scores": {},
        "audit_feedback": None,
        "audit_passed": False,
        "final_email_draft": "",
        "requires_approval": True,
        "human_feedback": None,
        "trace_id": "trace-555-abc",
        "revision_count": 0,
        "status": "starting"
    }

    # 2. Compile Pipeline
    app_graph = create_pipeline()

    # 3. Execute
    print(f"Initial State Inquiry:\n\"{initial_state['raw_input']}\"\n")

    final_state = app_graph.invoke(initial_state)

    print("\n==================================================")
    print("🏁 Pipeline Run Complete. Final State Outputs:")
    print("==================================================")
    print(f"• Claim ID: {final_state.get('claim_id')}")
    print(f"• Extracted Fields (Agent 1): {final_state.get('extracted_data')}")
    print(f"• Extracted Confidence: {final_state.get('extraction_confidence')}")
    print(f"• Policy Verdict (Agent 2): {final_state.get('policy_verdict')}")
    print(f"• Policy Citations: {final_state.get('policy_citations')}")
    print(f"• Audit Score (Agent 3): {final_state.get('audit_scores')}")
    print(f"• Audit Passed: {final_state.get('audit_passed')}")
    print(f"• Email Draft (Agent 4):\n\n{final_state.get('final_email_draft')}\n")
    print(f"• Human Approval Required: {final_state.get('requires_approval')}")
    print("==================================================")

if __name__ == "__main__":
    run_demo()
