"""
Tool Abstraction Layer.

Design rationale:
- BaseTool defines a uniform interface: name, description, parameters schema, run().
- The agent never imports a concrete tool — it calls ToolRegistry.get_tool(name).
- Each tool declares its parameter schema as a JSON Schema dict, which the LLM
  can use for structured tool calling.
- Tools are async by default since most real tools involve I/O.
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any


class ToolResult(BaseModel):
    """Standardized tool output."""

    success: bool
    data: Any = None
    error: str | None = None


class BaseTool(ABC):
    """Base class for all agent tools."""

    name: str = "base"
    description: str = ""
    parameters: dict = {}  # JSON Schema for the tool's input

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        ...

    def to_openai_tool(self) -> dict:
        """Convert to OpenAI function-calling tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
