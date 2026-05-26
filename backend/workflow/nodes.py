"""
Agent Workflow Nodes.

Each node is a pure function: AgentState → partial AgentState.
The LangGraph runtime handles state merging and transitions.

Design principle: LLM does reasoning, program does control flow.
- Nodes use the LLM to decide WHAT to do.
- The graph edges decide the ORDER of execution.
- No infinite loops — max iterations enforced by the graph.
"""

import json
from backend.workflow.state import AgentState
from backend.schemas.chat import ChatMessage, Role
from backend.services.provider_registry import ProviderRegistry
from backend.tools.registry import ToolRegistry


def _add_status(state: AgentState, status: str) -> list[str]:
    """Append a status update."""
    return state.get("status_updates", []) + [status]


async def router_node(state: AgentState) -> dict:
    """
    Router: decides whether the query needs retrieval, a tool, or direct answer.

    Returns: {"route": "direct" | "retrieval" | "tool", "tool_name": ..., "tool_args": ...}
    """
    provider = ProviderRegistry.get_provider()
    status = _add_status(state, "🧠 Routing query...")

    # Get available tool descriptions
    tools = ToolRegistry.get_all_tools()
    tool_desc = "\n".join(
        f"- {t.name}: {t.description}" for t in tools
    )

    router_messages = [
        ChatMessage(
            role=Role.SYSTEM,
            content=(
                "You are a query router. Analyze the user's query and decide the best route.\n\n"
                "Available routes:\n"
                "- direct: Answer directly from your knowledge (simple questions, greetings, general chat)\n"
                "- retrieval: Search the knowledge base (questions about uploaded documents)\n"
                "- tool: Use a specific tool (calculations, web search, etc.)\n\n"
                f"Available tools:\n{tool_desc}\n\n"
                "Respond with ONLY a JSON object:\n"
                '{"route": "direct"} or\n'
                '{"route": "retrieval"} or\n'
                '{"route": "tool", "tool_name": "toolname", "tool_args": {"key": "value"}}'
            ),
        ),
        ChatMessage(role=Role.USER, content=state["query"]),
    ]

    response = await provider.chat(router_messages, temperature=0.1)

    # Parse the router decision
    try:
        # Extract JSON from response (handle markdown code blocks)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        decision = json.loads(cleaned)
    except json.JSONDecodeError:
        decision = {"route": "direct"}

    route = decision.get("route", "direct")

    return {
        "route": route,
        "tool_name": decision.get("tool_name", ""),
        "tool_args": decision.get("tool_args", {}),
        "iteration": state.get("iteration", 0),
        "status_updates": status,
    }


async def retrieval_node(state: AgentState) -> dict:
    """
    Retrieval: search the knowledge base using the retrieval tool.

    Returns: {"retrieval_results": [...]}
    """
    status = _add_status(state, "🔍 Searching knowledge base...")

    result = await ToolRegistry.execute("retrieval", query=state["query"])

    results = result.data.get("results", []) if result.success else []

    return {
        "retrieval_results": results,
        "status_updates": status,
    }


async def tool_node(state: AgentState) -> dict:
    """
    Tool execution: call the specified tool with its arguments.

    Returns: {"tool_result": {...}}
    """
    tool_name = state.get("tool_name", "")
    tool_args = state.get("tool_args", {})
    status = _add_status(state, f"🛠 Calling tool: {tool_name}...")

    result = await ToolRegistry.execute(tool_name, **tool_args)

    return {
        "tool_result": {
            "success": result.success,
            "data": result.data,
            "error": result.error,
        },
        "status_updates": status,
    }


async def plan_node(state: AgentState) -> dict:
    """
    Planner: synthesize retrieved information into a response plan.

    Only called after retrieval or tool use — not for direct answers.
    """
    provider = ProviderRegistry.get_provider()
    status = _add_status(state, "📋 Planning response...")

    # Build context from retrieval results or tool results
    context = ""
    if state.get("retrieval_results"):
        context = "Retrieved documents:\n"
        for i, r in enumerate(state["retrieval_results"], 1):
            context += f"[{i}] {r.get('citation', '')}: {r['content']}\n\n"
    elif state.get("tool_result"):
        context = f"Tool result: {json.dumps(state['tool_result'], ensure_ascii=False)}"

    plan_messages = [
        ChatMessage(
            role=Role.SYSTEM,
            content=(
                "You are a response planner. Given the user's query and retrieved context, "
                "create a brief plan for how to structure the response. "
                "Focus on: what information to include, how to cite sources, "
                "and what tone to use. Output ONLY the plan, 2-3 sentences max."
            ),
        ),
        ChatMessage(
            role=Role.USER,
            content=f"Query: {state['query']}\n\nContext:\n{context}",
        ),
    ]

    plan = await provider.chat(plan_messages, temperature=0.3)

    return {
        "plan": plan,
        "status_updates": status,
    }


async def generate_node(state: AgentState) -> dict:
    """
    Generator: produce the final response.

    Uses the full context: query, retrieval results, tool results, plan.
    """
    provider = ProviderRegistry.get_provider()
    status = _add_status(state, "✍️ Generating response...")

    # Build the generation prompt based on available context
    context_parts = []

    if state.get("retrieval_results"):
        context_parts.append("Reference documents:")
        for i, r in enumerate(state["retrieval_results"], 1):
            context_parts.append(f"[{i}] {r.get('citation', '')}: {r['content']}")

    if state.get("tool_result"):
        context_parts.append(f"\nTool output: {json.dumps(state['tool_result'], ensure_ascii=False)}")

    if state.get("plan"):
        context_parts.append(f"\nResponse plan: {state['plan']}")

    context_str = "\n".join(context_parts) if context_parts else ""

    system_prompt = (
        "You are a helpful AI assistant. Answer the user's question based on the provided context. "
        "If context includes documents, cite them using [source] notation. "
        "Be concise, accurate, and helpful. Answer in the same language as the user's query."
    )

    messages = [
        ChatMessage(role=Role.SYSTEM, content=system_prompt),
        ChatMessage(role=Role.USER, content=f"{context_str}\n\nUser question: {state['query']}"),
    ]

    response = await provider.chat(messages, temperature=0.7)

    return {
        "response": response,
        "iteration": state.get("iteration", 0) + 1,
        "status_updates": status,
    }


async def reflect_node(state: AgentState) -> dict:
    """
    Reflector: evaluate the quality of the generated response.

    Returns: {"reflection": "pass" | "revise"}
    - pass: response is good, send to user
    - revise: response needs improvement (max 1 revision)

    Only allows one revision to prevent infinite loops.
    """
    provider = ProviderRegistry.get_provider()
    iteration = state.get("iteration", 0)
    status = _add_status(state, "🔍 Checking response quality...")

    # Max 2 iterations (1 original + 1 revision)
    if iteration >= 2:
        return {
            "reflection": "pass",
            "status_updates": status,
        }

    reflect_messages = [
        ChatMessage(
            role=Role.SYSTEM,
            content=(
                "You are a response quality checker. Evaluate if the response adequately "
                "answers the user's question. Check:\n"
                "- Is the response relevant to the query?\n"
                "- Are sources properly cited (if documents were used)?\n"
                "- Is the response clear and well-structured?\n\n"
                "Respond with ONLY: 'pass' (if good) or 'revise' (if needs improvement)."
            ),
        ),
        ChatMessage(
            role=Role.USER,
            content=(
                f"User query: {state['query']}\n\n"
                f"Generated response: {state.get('response', '')}"
            ),
        ),
    ]

    verdict = await provider.chat(reflect_messages, temperature=0.1)
    verdict = verdict.strip().lower()

    if "revise" in verdict:
        return {
            "reflection": "revise",
            "status_updates": status,
        }

    return {
        "reflection": "pass",
        "status_updates": status,
    }
