from core.runtime.base_agent import BaseWorkflow
from core.schemas.state import AgentState
from core.tool_registry.registry import ToolRegistry
from core.runtime.llm import call_llm_structured
from pydantic import BaseModel
from langgraph.graph import END

class SqlGeneration(BaseModel):
    sql_query: str
    explanation: str

def generate_sql_node(state: AgentState) -> AgentState:
    """Uses LLM to convert natural language to SQL."""
    question = state["context"].get("question", "What was the total revenue?")

    prompt = f"""You are an Enterprise BI Copilot.
Convert the following natural language question into a PostgreSQL query.
Assume a table named 'sales' with columns: 'id', 'date', 'revenue', 'region'.

Question: {question}"""

    sql_res = call_llm_structured(prompt, SqlGeneration, project="analytics-workflow")
    state["extracted_data"]["generated_sql"] = sql_res.sql_query
    state["extracted_data"]["sql_explanation"] = sql_res.explanation

    state["messages"].append({"role": "system", "content": f"Generated SQL: {sql_res.sql_query}"})
    return state

def execute_sql_node(state: AgentState) -> AgentState:
    """Executes the generated SQL via the tool registry."""
    query = state["extracted_data"]["generated_sql"]

    results = ToolRegistry.invoke("sql_executor", query=query)
    state["active_tools"].append("sql_executor")

    state["extracted_data"]["query_results"] = results
    state["messages"].append({"role": "system", "content": "SQL executed against data warehouse."})
    return state

class AnalyticsWorkflow(BaseWorkflow):
    """
    Workflow for Enterprise BI Copilot: Natural language analytics agent.
    """
    def _build_graph(self):
        self.graph.add_node("generate", generate_sql_node)
        self.graph.add_node("execute", execute_sql_node)

        self.graph.set_entry_point("generate")
        self.graph.add_edge("generate", "execute")
        self.graph.add_edge("execute", END)
