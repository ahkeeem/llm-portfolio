"""
Enterprise Agent Runtime (EAR) — Control Plane.
Central FastAPI service that routes all workflow requests, tracks metrics,
and exposes live telemetry. Deployed on Render.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from core.workflows.registry import WorkflowRegistry
from core.observability.metrics import metrics, track_endpoint
from core.runtime.llm import PROVIDER, call_llm  # for error messages
from core.bi.sql_engine import execute_query, infer_chart_config, get_schema, get_preview
import core.tool_registry.tools  # noqa: F401 — import triggers @ToolRegistry.register() decorators
from apps.compliance_workflow.workflow import ComplianceWorkflow
from apps.financial_workflow.workflow import FinancialWorkflow
from apps.legal_workflow.workflow import LegalWorkflow
from apps.analytics_workflow.workflow import AnalyticsWorkflow
from apps.extraction_workflow.workflow import ExtractionWorkflow
from apps.evaluation_workflow.workflow import EvaluationWorkflow

# ── Register all workflows ────────────────────────────────────────────
WorkflowRegistry.register("compliance-workflow", ComplianceWorkflow("compliance-workflow"))
WorkflowRegistry.register("financial-workflow", FinancialWorkflow("financial-workflow"))
WorkflowRegistry.register("legal-workflow", LegalWorkflow("legal-workflow"))
WorkflowRegistry.register("analytics-workflow", AnalyticsWorkflow("analytics-workflow"))
WorkflowRegistry.register("extraction-workflow", ExtractionWorkflow("extraction-workflow"))
WorkflowRegistry.register("evaluation-workflow", EvaluationWorkflow("evaluation-workflow"))

# ── App ───────────────────────────────────────────────────────────────
app = FastAPI(title="Enterprise Agent Runtime (EAR) Control Plane", version="2.0.0")


# CORS: allow_credentials must be False when allow_origins is ["*"] per the
# CORS spec; browsers block credentialed cross-origin requests with wildcards.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────
class InvokeRequest(BaseModel):
    workflow_id: str
    session_id: str
    inputs: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


class ApproveRequest(BaseModel):
    email_text: Optional[str] = None
    approved: bool


class BIChatRequest(BaseModel):
    question: str
    session_id: str = "bi-demo"
    history: Optional[List[Dict[str, str]]] = None


# ── Endpoints ─────────────────────────────────────────────────────────
@app.post("/api/v1/workflows/invoke")
@track_endpoint("invoke")
async def invoke_workflow(req: InvokeRequest):
    """
    Invoke a specific workflow by ID.
    Initialises the standard AgentState and routes to the correct LangGraph instance.
    """
    try:
        workflow = WorkflowRegistry.get(req.workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    initial_state = {
        "workflow_id": req.workflow_id,
        "session_id": req.session_id,
        "messages": req.inputs.get("messages", []),
        "context": req.inputs.get("context", {}),
        "extracted_data": {},
        "active_tools": [],
        "requires_approval": req.config.get("requires_approval", False) if req.config else False,
        "approval_status": None,
        "error": None,
        "metadata": {},
    }

    try:
        result = workflow.invoke(initial_state, config=req.config)

        # ── Format response per workflow for the frontend ──
        frontend_response = result

        if req.workflow_id == "compliance-workflow":
            if "question" in req.inputs.get("context", {}):
                # RAG Advisor path
                frontend_response = {
                    "answer": result["extracted_data"].get("draft_response", "No answer found."),
                    "sources": result["extracted_data"].get("sources", []),
                    "status": "success",
                }
            else:
                # Email Triage path
                frontend_response = {
                    "classification": result["extracted_data"].get("classification", ""),
                    "response": result["extracted_data"].get("draft_response", ""),
                    "privacy_scan": "FLAGGED" if result["extracted_data"].get("pii_found") else "PASSED",
                    "pii_redacted": result["extracted_data"].get("pii_found", False),
                    "requires_approval": result.get("requires_approval", False),
                }

        elif req.workflow_id == "extraction-workflow":
            frontend_response = {
                "fields": result["extracted_data"].get("fields", {}),
                "status": "success",
            }

        elif req.workflow_id == "evaluation-workflow":
            frontend_response = {
                "aggregate": result["extracted_data"].get("aggregate", {}),
                "flagged": result["extracted_data"].get("flagged", []),
                "status": "success",
            }

        return {
            "status": "success",
            "session_id": req.session_id,
            "state": frontend_response,
            "metadata": result.get("metadata", {}),
        }
    except Exception as e:
        # Unwrap RetryError to show the real cause
        error_msg = str(e)
        cause = e
        if hasattr(e, 'last_attempt'):
            exc = e.last_attempt.exception()
            if exc:
                cause = exc
                error_msg = str(exc)
        # Provide user-friendly messages for common API errors
        cause_type = type(cause).__name__
        if 'PermissionDenied' in cause_type or 'AuthenticationError' in cause_type:
            error_msg = f"LLM API key is invalid or expired ({PROVIDER}). Please update your API key in .env"
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {error_msg}")


@app.get("/api/v1/workflows")
async def list_workflows():
    """List all registered EAR workflows."""
    return {"workflows": WorkflowRegistry.list_workflows()}


@app.post("/api/v1/workflows/approve")
async def approve_workflow(req: ApproveRequest):
    """Handle HITL approval for workflows."""
    if req.approved:
        metrics.inc("emails_approved")
    else:
        metrics.inc("emails_rejected")
    return {"status": "success", "approved": req.approved, "message": "Approval recorded successfully"}


@app.get("/health")
async def health_check():
    """Control Plane health check with live telemetry."""
    from core.runtime.llm import PROVIDER, DEFAULT_MODEL
    return {
        "status": "online",
        "service": "control-plane",
        "version": "2.0.0",
        "llm_provider": PROVIDER,
        "llm_model": DEFAULT_MODEL,
        "metrics": metrics.snapshot(),
    }


# ── BI Chat Endpoints ─────────────────────────────────────────────────

@app.get("/api/v1/bi-schema")
async def bi_schema():
    """
    Return the database schema (table names + columns) and a data preview
    for the BI Chat dataset viewer.
    """
    schema = get_schema()
    previews = {}
    for table_name in schema:
        cols, rows = get_preview(table_name, n_rows=8)
        previews[table_name] = {"columns": cols, "rows": rows}
    return {
        "status": "ok",
        "schema": schema,
        "previews": previews,
    }


@app.post("/api/v1/bi-chat")
async def bi_chat(req: BIChatRequest):
    """
    Conversational BI endpoint.
    1. Sends the question + schema context to the LLM to get SQL.
    2. Executes the SQL against in-memory SQLite loaded from project CSVs.
    3. Returns: generated_sql, columns, rows, chart_config, natural_language_summary.
    """
    schema = get_schema()

    # Build a schema description for the LLM prompt
    schema_desc = "\n".join(
        f"  Table '{t}': columns = {', '.join(cols)}"
        for t, cols in schema.items()
    )

    # Build conversation history context
    history_ctx = ""
    if req.history:
        history_ctx = "\nPrevious conversation turns:\n" + "\n".join(
            f"  [{h['role']}]: {h['content']}" for h in req.history[-4:]
        )

    prompt = f"""You are an enterprise BI SQL assistant. You write SQLite-compatible SELECT queries.

Available tables and their columns:
{schema_desc}

IMPORTANT rules:
- Always use SQLite syntax (no PostgreSQL-specific functions).
- Only write SELECT queries — no INSERT, UPDATE, DELETE, DROP.
- Use double quotes around table and column names if they contain spaces or special characters.
- For date operations use SQLite's strftime or substr.
- For numeric aggregations cast TEXT columns: CAST(col AS REAL).
- Limit results to at most 50 rows unless asked for more.
- Respond with ONLY the raw SQL query — no markdown, no explanation, no backticks.
{history_ctx}

User question: {req.question}

SQL query:"""

    # Generate SQL
    try:
        generated_sql = call_llm(prompt, temperature=0.0, project="bi-chat").strip()
        # Strip any accidental markdown fencing
        if generated_sql.startswith("```"):
            import re
            generated_sql = re.sub(r"```(?:sql)?\n?|```", "", generated_sql).strip()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM error: {exc}")

    # Execute SQL
    columns, rows, error = execute_query(generated_sql)

    if error:
        # Return graceful error with the attempted SQL so the user can inspect it
        return {
            "status": "error",
            "generated_sql": generated_sql,
            "error": error,
            "columns": [],
            "rows": [],
            "chart_config": {},
            "summary": f"The query could not be executed: {error}",
        }

    # Build chart config heuristically
    chart_config = infer_chart_config(req.question, columns, rows)

    # Generate a natural-language summary (short LLM call)
    row_count = len(rows)
    summary_prompt = f"""Summarise in one concise sentence (max 30 words) what these query results show.
Question: {req.question}
SQL: {generated_sql}
Result: {row_count} row(s), columns: {columns}.
First few rows: {rows[:3]}"""

    try:
        summary = call_llm(summary_prompt, temperature=0.3, project="bi-chat").strip()
    except Exception:
        summary = f"Query returned {row_count} result(s)."

    return {
        "status": "success",
        "generated_sql": generated_sql,
        "columns": columns,
        "rows": rows[:100],   # cap frontend payload at 100 rows
        "row_count": row_count,
        "chart_config": chart_config,
        "summary": summary,
    }
