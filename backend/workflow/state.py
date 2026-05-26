"""
Agent Workflow State.

Defines the state that flows through the LangGraph graph.
Each node reads from and writes to this state.

Why TypedDict: LangGraph requires a typed state schema for
its internal bookkeeping and checkpointing.
"""

from typing import TypedDict, Annotated, Any
from langgraph.graph import add_messages
from backend.schemas.chat import ChatMessage


class AgentState(TypedDict):
    """State that flows through the agent workflow."""

    # Original user query
    query: str

    # Messages for the LLM (includes system prompt + history + current query)
    messages: list[ChatMessage]

    # Router decision: "direct", "retrieval", "tool"
    route: str

    # Retrieval results (if route == "retrieval")
    retrieval_results: list[dict]

    # Tool call info (if route == "tool")
    tool_name: str
    tool_args: dict
    tool_result: dict

    # Planned response strategy
    plan: str

    # Generated response
    response: str

    # Reflection verdict: "pass", "revise", "fail"
    reflection: str

    # Iteration counter (prevents infinite loops)
    iteration: int

    # Status updates for the frontend (streamed via WebSocket)
    status_updates: list[str]
