import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict
from langgraph.graph import StateGraph
from core.schemas.state import AgentState

logger = logging.getLogger("ear.workflow")

class BaseWorkflow(ABC):
    """
    Base abstraction for any domain workflow in the Enterprise Agent Runtime.
    Provides standard graph initialization, compilation, and invocation.
    """

    def __init__(self, name: str):
        self.name = name
        self.graph = StateGraph(AgentState)
        self._build_graph()
        # Compile without checkpointer by default, control plane will handle persistence
        self.compiled_graph = self.graph.compile()

    @abstractmethod
    def _build_graph(self):
        """Define nodes, edges, and routing logic here."""
        pass

    def invoke(self, state: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke the compiled graph with centralized telemetry/tracing hooks."""
        logger.info(f"Starting workflow trace: {self.name} | Session: {state.get('session_id')}")
        start_time = time.time()

        from core.observability.metrics import request_usage_context
        token = request_usage_context.set([])

        try:
            # Here we would initialize the Langfuse/OpenTelemetry span
            result = self.compiled_graph.invoke(state, config=config)

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"Workflow {self.name} completed successfully in {elapsed_ms:.2f}ms")

            # Record execution time and token usage in metadata
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["latency_ms"] = elapsed_ms

            # Aggregate request-specific token usage
            usage_list = request_usage_context.get() or []
            total_prompt = sum(u["prompt_tokens"] for u in usage_list)
            total_completion = sum(u["completion_tokens"] for u in usage_list)
            total_tokens = sum(u["total_tokens"] for u in usage_list)
            total_cost = sum(u["cost_usd"] for u in usage_list)

            result["metadata"]["tokens"] = {
                "prompt": total_prompt,
                "completion": total_completion,
                "total": total_tokens,
            }
            result["metadata"]["cost_usd"] = round(total_cost, 6)

            return result
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Workflow {self.name} failed after {elapsed_ms:.2f}ms: {str(e)}")
            # Fail span in telemetry here
            raise
        finally:
            request_usage_context.reset(token)
