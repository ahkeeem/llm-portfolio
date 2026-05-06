import sys
import os

# Add relevant paths so we can import from original projects
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../03-edge-ai-extraction")))

from core.inference import extract_receipt_fields
from app.state import AgentState

def extract_node(state: AgentState):
    """
    Agent 1: Extraction Agent.
    Wraps the fine-tuned/fallback extraction logic.
    """
    print("--- AGENT 1: EXTRACTING DATA ---")
    raw_input = state["raw_input"]
    
    # Call original Project 3 logic
    result = extract_receipt_fields(raw_input)
    
    # Update state
    return {
        "extracted_data": result.get("fields", {}),
        "extraction_confidence": 0.95 if result.get("model") == "fine-tuned-local" else 0.8,
        "status": "extracted"
    }
