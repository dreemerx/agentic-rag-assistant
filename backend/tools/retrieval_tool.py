"""
Retrieval Tool — RAG knowledge base search.

This is the core tool that lets the agent search the user's uploaded documents.
It wraps the Retriever and returns formatted results with source citations.
"""

from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import ToolRegistry
from backend.rag.retriever import retriever


class RetrievalTool(BaseTool):
    name = "retrieval"
    description = (
        "Search the knowledge base for relevant information from uploaded documents. "
        "Returns ranked results with source citations. "
        "Use this when the user asks about topics that might be covered in their documents."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant documents",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default: 3)",
                "default": 3,
            },
        },
        "required": ["query"],
    }

    async def run(self, query: str, top_k: int = 3, **kwargs) -> ToolResult:
        try:
            results = await retriever.search(query=query, top_k=top_k)

            if not results["results"]:
                return ToolResult(
                    success=True,
                    data={"message": "No relevant documents found.", "results": []},
                )

            # Format results with citations
            formatted = []
            for i, r in enumerate(results["results"], 1):
                source = r["metadata"].get("source", "unknown")
                page = r["metadata"].get("page")
                citation = f"[{source}]"
                if page:
                    citation = f"[{source}, p.{page}]"

                formatted.append({
                    "rank": i,
                    "content": r["content"],
                    "citation": citation,
                    "score": round(r.get("rerank_score", r.get("score", 0)), 3),
                })

            return ToolResult(
                success=True,
                data={"results": formatted, "total": len(formatted)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Auto-register
ToolRegistry.register(RetrievalTool())
