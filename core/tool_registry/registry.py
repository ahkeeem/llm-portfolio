from typing import Callable, Dict, Any, Awaitable, Union
import inspect
import logging

logger = logging.getLogger("ear.tool_registry")

ToolCallable = Union[Callable[..., Any], Callable[..., Awaitable[Any]]]

class ToolRegistry:
    """
    Centralized tool registry for all EAR workflows.
    Prevents direct hardcoded tool invocation and centralizes observability,
    failure handling, and potential MCP/dynamic selection.
    """
    _tools: Dict[str, ToolCallable] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, description: str = ""):
        """Decorator to register a tool."""
        def decorator(func: ToolCallable):
            cls._tools[name] = func
            cls._metadata[name] = {"description": description or func.__doc__}
            return func
        return decorator

    @classmethod
    async def invoke_async(cls, name: str, *args, **kwargs) -> Any:
        """Invoke a tool asynchronously with observability hooks."""
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' not found in registry.")

        tool = cls._tools[name]
        logger.info(f"Invoking tool: {name}")
        try:
            if inspect.iscoroutinefunction(tool):
                result = await tool(*args, **kwargs)
            else:
                result = tool(*args, **kwargs)
            logger.info(f"Tool '{name}' completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            raise

    @classmethod
    def invoke(cls, name: str, *args, **kwargs) -> Any:
        """Synchronous tool invocation."""
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' not found in registry.")

        tool = cls._tools[name]
        logger.info(f"Invoking tool (sync): {name}")
        try:
            result = tool(*args, **kwargs)
            logger.info(f"Tool '{name}' completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            raise

    @classmethod
    def list_tools(cls) -> list[str]:
        """Return list of registered tool names."""
        return list(cls._tools.keys())

    @classmethod
    def get_metadata(cls, name: str) -> Dict[str, Any]:
        """Get metadata for a specific tool."""
        return cls._metadata.get(name, {})
