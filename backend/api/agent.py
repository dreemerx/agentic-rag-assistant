"""
Agent API endpoint.

This is the main entry point for agent conversations.
It orchestrates: memory → workflow → streaming response.

Unlike the simple /chat endpoint, this runs the full agent workflow:
router → retrieval/tool → plan → generate → reflect.
"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.schemas.chat import ChatMessage, Role
from backend.memory.manager import MemoryManager
from backend.workflow.graph import agent_graph
from backend.services.provider_registry import ProviderRegistry

# Ensure tools are imported and registered
import backend.tools.retrieval_tool  # noqa: F401
import backend.tools.web_search_tool  # noqa: F401
import backend.tools.calculator_tool  # noqa: F401

router = APIRouter(prefix="/agent", tags=["agent"])

# In-memory session store (replace with Redis in production)
_sessions: dict[str, MemoryManager] = {}


class AgentRequest(BaseModel):
    message: str
    session_id: str = "default"


def _get_session(session_id: str) -> MemoryManager:
    """Get or create a memory session."""
    if session_id not in _sessions:
        _sessions[session_id] = MemoryManager(max_short_term=10, summarize_every=8)
    return _sessions[session_id]


@router.post("/chat")
async def agent_chat(request: AgentRequest):
    """
    Agent chat endpoint with full workflow and streaming.

    Returns Server-Sent Events:
    - status: {type, message} — agent status updates
    - token: {type, content} — streaming response tokens
    - done: {type, content, provider} — final message
    """
    memory = _get_session(request.session_id)

    # Add user message to memory
    memory.add_message(ChatMessage(role=Role.USER, content=request.message))

    # Build context for the workflow
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    context_messages = memory.build_context(
        system_prompt=(
            f"You are a helpful AI assistant with access to a knowledge base and tools. "
            f"Today's date is {today}. When the user asks about 'today' or recent events, "
            f"use this date to understand what they mean."
        )
    )

    async def event_stream():
        try:
            # Run the agent workflow
            initial_state = {
                "query": request.message,
                "messages": context_messages,
                "route": "",
                "retrieval_results": [],
                "tool_name": "",
                "tool_args": {},
                "tool_result": {},
                "plan": "",
                "response": "",
                "reflection": "",
                "iteration": 0,
                "status_updates": [],
            }

            final_state = None
            last_update_count = 0

            # Stream workflow execution
            async for event in agent_graph.astream(initial_state, stream_mode="updates"):
                for node_name, node_output in event.items():
                    # Stream any new status updates
                    updates = node_output.get("status_updates", [])
                    for update in updates[last_update_count:]:
                        yield f"data: {json.dumps({'type': 'status', 'message': update}, ensure_ascii=False)}\n\n"
                    last_update_count = len(updates)

                    # Track final state
                    if node_name == "generate" or node_name == "reflect":
                        if final_state is None:
                            final_state = {}
                        final_state.update(node_output)

            # Get the final response
            response = final_state.get("response", "") if final_state else ""

            # Stream the response token by token (simulate streaming)
            if response:
                # Stream in chunks for responsive UI
                chunk_size = 4
                for i in range(0, len(response), chunk_size):
                    chunk = response[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"

            # Add assistant response to memory
            if response:
                memory.add_message(ChatMessage(role=Role.ASSISTANT, content=response))

            # Check if we should summarize
            if memory.should_summarize():
                provider = ProviderRegistry.get_provider()
                yield f"data: {json.dumps({'type': 'status', 'message': '📝 Summarizing conversation...'}, ensure_ascii=False)}\n\n"
                await memory.summarize(provider)

            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'content': response, 'provider': ProviderRegistry.get_provider().name}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/reset")
async def reset_session(session_id: str = "default"):
    """Clear a conversation session."""
    if session_id in _sessions:
        _sessions[session_id].clear()
        del _sessions[session_id]
    return {"message": f"Session '{session_id}' reset"}


@router.get("/sessions")
async def list_sessions():
    """List active sessions."""
    return {"sessions": list(_sessions.keys())}
