from typing import List, Dict, Any
from core.tool_registry.registry import ToolRegistry

@ToolRegistry.register("policy_search", "Search the vector database for compliance and policy documents.")
def policy_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search tool wrapper that interacts with the vector index (ChromaDB/Pinecone).
    In a real production environment, this imports from core.retrieval.
    """
    # Mocking response for Phase 1 architecture verification
    return [
        {"text": "The company guarantees a 30-day refund window for all enterprise products.", "score": 0.95},
        {"text": "PII data (SSN, credit cards) must be redacted before sending to third-party LLMs.", "score": 0.88}
    ]

@ToolRegistry.register("sec_filing_lookup", "Look up SEC filings and financial KPIs for a given ticker.")
def sec_filing_lookup(ticker: str, year: int) -> Dict[str, Any]:
    """Mock tool for the financial workflow."""
    return {"revenue": "$10M", "ebitda_margin": "20%"}

@ToolRegistry.register("sql_executor", "Execute a read-only SQL query against the BI data warehouse.")
def sql_executor(query: str) -> List[Dict[str, Any]]:
    """Mock tool for the analytics workflow."""
    return [{"revenue": 10000000}]
