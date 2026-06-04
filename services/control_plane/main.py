"""
Enterprise Agent Runtime (EAR) — Control Plane.
Central FastAPI service that routes all workflow requests, tracks metrics,
and exposes live telemetry. Deployed on Render.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.workflows.registry import WorkflowRegistry
from core.observability.metrics import metrics, track_endpoint
from core.runtime.llm import PROVIDER  # for error messages
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    return {
        "status": "online",
        "service": "control-plane",
        "version": "2.0.0",
        "metrics": metrics.snapshot(),
    }
