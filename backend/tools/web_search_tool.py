"""
Web Search Tool — internet search via DuckDuckGo.

Uses the duckduckgo-search library (free, no API key required).
This gives the agent access to real-time information beyond its training data.
"""

from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import ToolRegistry


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Search the internet for current information. "
        "Use this when the user asks about recent events, facts not in the knowledge base, "
        "or anything requiring up-to-date information."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def run(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                    })

            return ToolResult(
                success=True,
                data={"results": results, "total": len(results)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Auto-register
ToolRegistry.register(WebSearchTool())
