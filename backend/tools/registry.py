"""
Tool Registry.

Central registry for all agent tools.
- Tools are registered at import time via `register()`.
- The agent calls `ToolRegistry.get_all_tools()` for tool-calling prompts,
  or `ToolRegistry.execute(name, **kwargs)` to run a tool.
- No if/elif dispatch — the registry handles routing.
"""

from backend.tools.base import BaseTool, ToolResult


class ToolRegistry:
    """Singleton registry for agent tools."""

    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """Register a tool instance."""
        cls._tools[tool.name] = tool

    @classmethod
    def get_tool(cls, name: str) -> BaseTool:
        """Get a tool by name."""
        if name not in cls._tools:
            available = list(cls._tools.keys())
            raise ValueError(f"Tool '{name}' not found. Available: {available}")
        return cls._tools[name]

    @classmethod
    def get_all_tools(cls) -> list[BaseTool]:
        """Get all registered tools."""
        return list(cls._tools.values())

    @classmethod
    def get_openai_tools(cls) -> list[dict]:
        """Get all tools in OpenAI function-calling format."""
        return [tool.to_openai_tool() for tool in cls._tools.values()]

    @classmethod
    async def execute(cls, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = cls.get_tool(name)
        return await tool.run(**kwargs)
