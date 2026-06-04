"""
Extraction Workflow: Edge-AI Document Extraction via backend LLM.
Routes receipt/document text through the server-side Groq API
so no API key is ever exposed in the browser.
"""
from core.runtime.base_agent import BaseWorkflow
from core.schemas.state import AgentState
from core.runtime.llm import call_llm_structured
from pydantic import BaseModel
from langgraph.graph import END


class ReceiptExtraction(BaseModel):
    company: str = "Unknown"
    date: str = "Unknown"
    address: str = "Unknown"
    total: str = "Unknown"


def extract_node(state: AgentState) -> AgentState:
    """Extract structured fields from raw receipt/document text using LLM."""
    receipt_text = state["context"].get("receipt_text", "")

    prompt = f"""Extract the following fields from this receipt text.
Return ONLY valid JSON matching this schema exactly:
{{"company": "", "date": "", "address": "", "total": ""}}

Receipt:
{receipt_text}"""

    extraction = call_llm_structured(prompt, ReceiptExtraction, project="edge-ai-extraction")

    state["extracted_data"]["fields"] = extraction.model_dump()
    state["messages"].append({"role": "system", "content": "Receipt fields extracted via backend LLM."})
    return state


class ExtractionWorkflow(BaseWorkflow):
    """
    Workflow for Edge-AI Extraction: Structured field extraction from documents.
    In production this would use a local SLM (Phi-3); for the live demo it routes
    through the server-side Groq API to keep keys secure.
    """
    def _build_graph(self):
        self.graph.add_node("extract", extract_node)
        self.graph.set_entry_point("extract")
        self.graph.add_edge("extract", END)
