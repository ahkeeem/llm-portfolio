from typing import Dict
from core.runtime.base_agent import BaseWorkflow

class WorkflowRegistry:
    """
    Centralized registry for all EAR domain workflows.
    Allows the Control Plane to dynamically route requests based on workflow_id.
    """
    _workflows: Dict[str, BaseWorkflow] = {}

    @classmethod
    def register(cls, name: str, workflow_instance: BaseWorkflow):
        cls._workflows[name] = workflow_instance

    @classmethod
    def get(cls, name: str) -> BaseWorkflow:
        if name not in cls._workflows:
            raise ValueError(f"Workflow '{name}' not found in registry.")
        return cls._workflows[name]

    @classmethod
    def list_workflows(cls) -> list[str]:
        return list(cls._workflows.keys())
