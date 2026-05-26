"""
LangGraph Agent Workflow.

This defines the graph that controls the agent's reasoning and execution flow.

Graph structure:
    START → router
    router → retrieve (if retrieval needed)
    router → tool (if tool needed)
    router → generate (if direct answer)
    retrieve → plan
    tool → plan
    plan → generate
    generate → reflect
    reflect → generate (if revision needed, max 1x)
    reflect → END (if passed)

Key design decisions:
- No infinite loops: max 2 iterations enforced by reflect_node.
- LLM decides WHAT to do (router), program decides WHEN (graph edges).
- Each node is async — the graph runs on asyncio.
- State is a TypedDict — LangGraph handles merging.
"""

from langgraph.graph import StateGraph, END
from backend.workflow.state import AgentState
from backend.workflow.nodes import (
    router_node,
    retrieval_node,
    tool_node,
    plan_node,
    generate_node,
    reflect_node,
)


def _route_after_router(state: AgentState) -> str:
    """Conditional edge: decide which node to run after the router."""
    route = state.get("route", "direct")
    if route == "retrieval":
        return "retrieve"
    elif route == "tool":
        return "tool"
    else:
        return "generate"


def _route_after_reflect(state: AgentState) -> str:
    """Conditional edge: revise or finish."""
    if state.get("reflection") == "revise":
        return "generate"
    return END


def build_agent_graph() -> StateGraph:
    """Build and compile the agent workflow graph."""

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("retrieve", retrieval_node)
    graph.add_node("tool", tool_node)
    graph.add_node("planner", plan_node)
    graph.add_node("generate", generate_node)
    graph.add_node("reflect", reflect_node)

    # Entry point
    graph.set_entry_point("router")

    # Conditional edges from router
    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "retrieve": "retrieve",
            "tool": "tool",
            "generate": "generate",
        },
    )

    # Linear edges
    graph.add_edge("retrieve", "planner")
    graph.add_edge("tool", "planner")
    graph.add_edge("planner", "generate")
    graph.add_edge("generate", "reflect")

    # Conditional edge from reflect (loop or end)
    graph.add_conditional_edges(
        "reflect",
        _route_after_reflect,
        {
            "generate": "generate",
            END: END,
        },
    )

    return graph.compile()


# Singleton compiled graph
agent_graph = build_agent_graph()
