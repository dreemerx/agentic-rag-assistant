"""
WebSocket endpoint for real-time agent communication.

Design rationale:
- WebSocket provides full-duplex communication — the server can push
  status updates and tokens as they arrive, without the client polling.
- Each connection gets its own MemoryManager session.
- Messages are JSON-encoded for easy frontend parsing.
- The agent workflow streams status updates and tokens through the socket.

Protocol:
  Client sends: {"type": "chat", "message": "...", "session_id": "..."}
  Server sends: {"type": "status", "message": "..."}
  Server sends: {"type": "token", "content": "..."}
  Server sends: {"type": "done", "content": "...", "provider": "..."}
  Server sends: {"type": "error", "message": "..."}
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.schemas.chat import ChatMessage, Role
from backend.memory.manager import MemoryManager
from backend.workflow.graph import agent_graph
from backend.services.provider_registry import ProviderRegistry

router = APIRouter(tags=["websocket"])

# Session store
_sessions: dict[str, MemoryManager] = {}


def _get_session(session_id: str) -> MemoryManager:
    if session_id not in _sessions:
        _sessions[session_id] = MemoryManager(max_short_term=10, summarize_every=8)
    return _sessions[session_id]


async def _send(ws: WebSocket, data: dict) -> None:
    """Send a JSON message through the WebSocket."""
    await ws.send_text(json.dumps(data, ensure_ascii=False))


@router.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    """
    Main WebSocket endpoint for agent chat.

    Handles the full lifecycle:
    1. Accept connection
    2. Receive messages
    3. Run agent workflow with streaming
    4. Send status updates and tokens
    5. Handle disconnection
    """
    await ws.accept()

    try:
        while True:
            # Receive message from client
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "chat":
                await _handle_chat(ws, data)
            elif msg_type == "reset":
                session_id = data.get("session_id", "default")
                if session_id in _sessions:
                    _sessions[session_id].clear()
                    del _sessions[session_id]
                await _send(ws, {"type": "status", "message": "Session reset"})
            elif msg_type == "ping":
                await _send(ws, {"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await _send(ws, {"type": "error", "message": str(e)})
        except Exception:
            pass


async def _handle_chat(ws: WebSocket, data: dict) -> None:
    """Process a chat message through the agent workflow."""
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not message:
        await _send(ws, {"type": "error", "message": "Empty message"})
        return

    memory = _get_session(session_id)
    memory.add_message(ChatMessage(role=Role.USER, content=message))

    # Build context
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    context_messages = memory.build_context(
        system_prompt=(
            f"You are a helpful AI assistant with access to a knowledge base and tools. "
            f"Today's date is {today}. When the user asks about 'today' or recent events, "
            f"use this date to understand what they mean."
        )
    )

    try:
        # Run the agent workflow
        initial_state = {
            "query": message,
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
                # Send new status updates
                updates = node_output.get("status_updates", [])
                for update in updates[last_update_count:]:
                    await _send(ws, {"type": "status", "message": update})
                last_update_count = len(updates)

                if node_name in ("generate", "reflect"):
                    if final_state is None:
                        final_state = {}
                    final_state.update(node_output)

        # Get final response
        response = final_state.get("response", "") if final_state else ""

        # Stream the response in chunks
        if response:
            chunk_size = 4
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                await _send(ws, {"type": "token", "content": chunk})

        # Save to memory
        if response:
            memory.add_message(ChatMessage(role=Role.ASSISTANT, content=response))

        # Summarize if needed
        if memory.should_summarize():
            provider = ProviderRegistry.get_provider()
            await _send(ws, {"type": "status", "message": "Summarizing conversation..."})
            await memory.summarize(provider)

        # Send completion
        await _send(ws, {
            "type": "done",
            "content": response,
            "provider": ProviderRegistry.get_provider().name,
        })

    except Exception as e:
        await _send(ws, {"type": "error", "message": str(e)})
