"""
Tool implementations registered with the ToolRegistry.

Each tool queries the lightweight dataset samples in data/samples/
instead of returning hardcoded mock data. This demonstrates
load-balanced dataset coupling at the portfolio level.
"""
import os
import pathlib
import pandas as pd
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
import chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 as onnx_module

from core.tool_registry.registry import ToolRegistry

# Resolve paths relative to the project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_SAMPLES_DIR = os.path.join(_PROJECT_ROOT, "data", "samples")

# Configure ONNX download path to point to workspace's cache
workspace_cache = pathlib.Path(_PROJECT_ROOT) / ".chroma_cache" / "onnx_models" / "all-MiniLM-L6-v2"
onnx_module.ONNXMiniLM_L6_V2.DOWNLOAD_PATH = workspace_cache

_embed_fn = embedding_functions.DefaultEmbeddingFunction()

# Persistent ChromaDB client
_chroma_client = chromadb.PersistentClient(path=os.path.join(_PROJECT_ROOT, "data", "chromadb"))
_collection = _chroma_client.get_or_create_collection(
    name="policy_documents",
    metadata={"hnsw:space": "cosine"},
)


def _load_sample(filename: str, nrows: int = None) -> pd.DataFrame:
    """Load a sample CSV from data/samples/ with optional row limit."""
    path = os.path.join(_SAMPLES_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Sample file not found: {path}")
    return pd.read_csv(path, nrows=nrows)


@ToolRegistry.register(
    "policy_search",
    "Search the vector database for compliance and policy documents."
)
def policy_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search the persistent ChromaDB collection for documents matching the query.
    Falls back to pandas CSV search and then mock data on failure.
    """
    try:
        query_embedding = _embed_fn([query])[0]
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        output = []
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                dist = results["distances"][0][i] if results["distances"] else 0.0
                score = round(1.0 - dist, 2)
                output.append({
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i].get("source", "ChromaDB") if results["metadatas"] else "ChromaDB",
                    "score": score,
                })
            return output

        raise ValueError("Chroma collection returned no results")
    except Exception:
        # Graceful fallback to pandas search on emails_sample.csv
        try:
            df = _load_sample("emails_sample.csv", nrows=200)
            query_lower = query.lower()
            mask = df["message"].str.lower().str.contains(query_lower, na=False)
            matches = df[mask].head(top_k)

            if matches.empty:
                matches = df.head(top_k)

            return [
                {
                    "text": row["message"][:500],
                    "source": row.get("file", "email_corpus"),
                    "score": round(0.95 - i * 0.03, 2),
                }
                for i, (_, row) in enumerate(matches.iterrows())
            ]
        except FileNotFoundError:
            # Final fallback to hardcoded mock text
            return [
                {"text": "30-day refund window for all enterprise products.", "score": 0.95},
                {"text": "PII data must be redacted before sending to third-party LLMs.", "score": 0.88},
            ]


@ToolRegistry.register(
    "sec_filing_lookup",
    "Look up SEC filings and financial KPIs for a given ticker."
)
def sec_filing_lookup(ticker: str, year: int = None) -> Dict[str, Any]:
    """
    Queries the financial_sample.csv for SEC filing records
    matching the given ticker symbol.
    """
    try:
        df = _load_sample("financial_sample.csv")
        # Filter by symbol if column exists
        if "symbol" in df.columns:
            matches = df[df["symbol"].str.upper() == ticker.upper()]
            if year and "filed_date" in df.columns:
                matches = matches[
                    matches["filed_date"].str.contains(str(year), na=False)
                ]
            if not matches.empty:
                row = matches.iloc[0]
                return {
                    "ticker": ticker.upper(),
                    "form": row.get("form", "N/A"),
                    "filed_date": str(row.get("filed_date", "N/A")),
                    "report_url": row.get("report_url", ""),
                    "access_number": row.get("access_number", ""),
                    "source": "data/samples/financial_sample.csv",
                }

        # Fallback: return aggregate stats from the sample
        return {
            "ticker": ticker.upper(),
            "total_filings_in_sample": len(df),
            "form_types": df["form"].value_counts().head(5).to_dict() if "form" in df.columns else {},
            "source": "data/samples/financial_sample.csv",
            "note": f"No exact match for {ticker}; returning sample summary.",
        }
    except FileNotFoundError:
        return {"ticker": ticker, "revenue": "$10M", "ebitda_margin": "20%", "source": "mock"}


@ToolRegistry.register(
    "sql_executor",
    "Execute a read-only SQL query against the BI data warehouse."
)
def sql_executor(query: str) -> List[Dict[str, Any]]:
    """
    Simulates SQL execution by querying the creditcard_sample.csv.
    Supports basic aggregate queries by returning summary statistics.
    """
    try:
        df = _load_sample("creditcard_sample.csv")
        query_lower = query.lower()

        # Route to appropriate aggregate based on query intent
        if "fraud" in query_lower or "class" in query_lower:
            fraud_count = int(df["Class"].sum()) if "Class" in df.columns else 0
            total = len(df)
            return [{
                "total_transactions": total,
                "fraud_count": fraud_count,
                "fraud_rate": round(fraud_count / total, 4) if total > 0 else 0,
                "source": "data/samples/creditcard_sample.csv",
            }]
        elif "amount" in query_lower or "revenue" in query_lower:
            return [{
                "total_amount": round(float(df["Amount"].sum()), 2) if "Amount" in df.columns else 0,
                "avg_amount": round(float(df["Amount"].mean()), 2) if "Amount" in df.columns else 0,
                "max_amount": round(float(df["Amount"].max()), 2) if "Amount" in df.columns else 0,
                "record_count": len(df),
                "source": "data/samples/creditcard_sample.csv",
            }]
        else:
            # Default: return sample summary
            return [{
                "columns": df.columns.tolist(),
                "record_count": len(df),
                "sample_amounts": df["Amount"].head(5).tolist() if "Amount" in df.columns else [],
                "source": "data/samples/creditcard_sample.csv",
            }]
    except FileNotFoundError:
        return [{"revenue": 10000000, "source": "mock"}]
