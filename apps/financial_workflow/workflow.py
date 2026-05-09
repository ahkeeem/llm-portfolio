from typing import Dict, Any
from core.runtime.base_agent import BaseWorkflow
from core.schemas.state import AgentState
from core.tool_registry.registry import ToolRegistry
from core.runtime.llm import call_llm_structured
from pydantic import BaseModel
from langgraph.graph import END

class FinancialAnalysis(BaseModel):
    summary: str
    key_risks: list[str]
    growth_outlook: str

def ingest_filing_node(state: AgentState) -> AgentState:
    """Simulates ingesting an SEC filing."""
    ticker = state["context"].get("ticker", "AAPL")
    year = state["context"].get("year", 2026)
    
    # Use tool registry to get mock SEC data
    filing_data = ToolRegistry.invoke("sec_filing_lookup", ticker=ticker, year=year)
    state["active_tools"].append("sec_filing_lookup")
    
    state["extracted_data"]["raw_filing"] = filing_data
    state["messages"].append({"role": "system", "content": f"Ingested {year} SEC filing for {ticker}."})
    return state

def analyze_kpi_node(state: AgentState) -> AgentState:
    """Uses LLM to analyze the ingested KPI data."""
    ticker = state["context"].get("ticker", "AAPL")
    filing_data = state["extracted_data"]["raw_filing"]
    
    prompt = f"""You are an expert equity research analyst.
Analyze the following KPIs for {ticker}:
Revenue: {filing_data.get('revenue')}
EBITDA Margin: {filing_data.get('ebitda_margin')}

Provide a brief summary, key risks, and growth outlook."""

    analysis = call_llm_structured(prompt, FinancialAnalysis)
    
    state["extracted_data"]["analysis_summary"] = analysis.summary
    state["extracted_data"]["key_risks"] = analysis.key_risks
    state["extracted_data"]["growth_outlook"] = analysis.growth_outlook
    
    state["messages"].append({"role": "system", "content": "Completed KPI analysis."})
    return state

class FinancialWorkflow(BaseWorkflow):
    """
    Workflow for Financial Research: AI equity research assistant.
    """
    def _build_graph(self):
        self.graph.add_node("ingest", ingest_filing_node)
        self.graph.add_node("analyze", analyze_kpi_node)
        
        self.graph.set_entry_point("ingest")
        self.graph.add_edge("ingest", "analyze")
        self.graph.add_edge("analyze", END)
