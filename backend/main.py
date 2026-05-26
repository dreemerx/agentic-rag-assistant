"""
Agentic RAG Assistant — Entry point.

Phase 1: FastAPI + Provider Abstraction + Streaming Chat
Phase 2: RAG pipeline (upload → chunk → embed → retrieve)
Phase 3: LangGraph Agent Workflow + Tools + Memory
Phase 4: WebSocket + Frontend integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.chat import router as chat_router
from backend.api.health import router as health_router
from backend.api.rag import router as rag_router
from backend.api.agent import router as agent_router
from backend.api.websocket import router as ws_router
from backend.config import settings

app = FastAPI(
    title="Agentic RAG Assistant",
    description="An industrial-grade AI Agent with RAG, Tool Calling, and Memory",
    version="0.1.0",
)

# CORS — allow frontend to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(chat_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "name": "Agentic RAG Assistant",
        "version": "0.1.0",
        "docs": "/docs",
    }
