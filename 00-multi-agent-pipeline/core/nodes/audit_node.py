import sys
import os

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../02-rag-evaluator"))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from core.metrics import score_faithfulness, score_relevancy
from app.state import AgentState

# Clean up path to prevent namespace collisions
if sys.path[0] == project_path:
    sys.path.pop(0)

def audit_node(state: AgentState):
    """
    Agent 3: Internal Auditor Agent.
    Audits the generated policy answer against faithfulness and relevancy standards.
    """
    print("--- AGENT 3: AUDITING POLICY RESPONSE ---")
    
    answer = state.get("policy_verdict", "")
    context = state.get("policy_context", "")
    question = state.get("raw_input", "")
    
    faithfulness = score_faithfulness(answer, context)
    relevancy = score_relevancy(answer, question)
    
    avg_score = (faithfulness + relevancy) / 2
    passed = avg_score >= 0.75
    
    feedback = ""
    if not passed:
        feedback = f"Faithfulness score ({faithfulness}) or Relevancy score ({relevancy}) is below target threshold of 0.75. Please ground your response better in the context and answer the prompt directly."
        
    return {
        "audit_scores": {"faithfulness": faithfulness, "relevancy": relevancy},
        "audit_passed": passed,
        "audit_feedback": feedback if not passed else None,
        "revision_count": state.get("revision_count", 0) + (1 if not passed else 0),
        "status": "audited"
    }
