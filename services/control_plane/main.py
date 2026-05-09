from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.workflows.registry import WorkflowRegistry
from apps.compliance_workflow.workflow import ComplianceWorkflow
from apps.financial_workflow.workflow import FinancialWorkflow
from apps.legal_workflow.workflow import LegalWorkflow
from apps.analytics_workflow.workflow import AnalyticsWorkflow

# Register workflows
WorkflowRegistry.register("compliance-workflow", ComplianceWorkflow("compliance-workflow"))
WorkflowRegistry.register("financial-workflow", FinancialWorkflow("financial-workflow"))
WorkflowRegistry.register("legal-workflow", LegalWorkflow("legal-workflow"))
WorkflowRegistry.register("analytics-workflow", AnalyticsWorkflow("analytics-workflow"))

app = FastAPI(title="Enterprise Agent Runtime (EAR) Control Plane")

class InvokeRequest(BaseModel):
    workflow_id: str
    session_id: str
    inputs: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None

@app.post("/api/v1/workflows/invoke")
async def invoke_workflow(req: InvokeRequest):
    """
    Invoke a specific workflow by ID.
    Handles initialization of the standard AgentState and routing to the right LangGraph instance.
    """
    try:
        workflow = WorkflowRegistry.get(req.workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Initialize the standardized AgentState
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
        "metadata": {}
    }
    
    try:
        # In production, heavy tasks would be dispatched to the Compute Plane here via Redis/Celery.
        # For Phase 1 we invoke directly.
        result = workflow.invoke(initial_state, config=req.config)
        
        # Format response for the legacy frontend
        frontend_response = result
        if req.workflow_id == "compliance-workflow":
            frontend_response = {
                "classification": result["extracted_data"].get("classification", ""),
                "response": result["extracted_data"].get("draft_response", ""),
                "privacy_scan": "FLAGGED" if result["extracted_data"].get("pii_found") else "PASSED",
                "pii_redacted": result["extracted_data"].get("pii_found", False),
                "requires_approval": result.get("requires_approval", False)
            }
            
        return {"status": "success", "session_id": req.session_id, "state": frontend_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@app.get("/api/v1/workflows")
async def list_workflows():
    """List all registered EAR workflows."""
    return {"workflows": WorkflowRegistry.list_workflows()}

@app.get("/health")
async def health_check():
    """Control Plane health check."""
    return {"status": "online", "service": "control-plane", "version": "1.0.0"}
