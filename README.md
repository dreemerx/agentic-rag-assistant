# Agentic RAG Assistant

An industrial-grade AI Agent system with RAG knowledge base, tool calling, memory, and streaming output. Built with FastAPI, LangGraph, and Next.js.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Chat UI  │  │ Status   │  │ Provider │  │  WebSocket   │   │
│  │          │  │ Display  │  │ Selector │  │  Client      │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────┬───────┘   │
└────────────────────────────────────────────────────┼───────────┘
                                                     │
                    WebSocket / SSE                  │
                                                     │
┌────────────────────────────────────────────────────┼───────────┐
│                    Backend (FastAPI)                │           │
│                                                    ▼           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Layer                              │  │
│  │   /chat/stream  /rag/upload  /agent/chat  /ws/chat       │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              LangGraph Agent Workflow                     │  │
│  │                                                          │  │
│  │   START → Router → ┬─ Retrieval ──→ Planner → Generate   │  │
│  │                    ├─ Tool ───────→ Planner → Generate    │  │
│  │                    └─ Direct ──────────────→ Generate     │  │
│  │                                              │           │  │
│  │                                         Reflect ──→ END   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                  │
│  ┌──────────┐  ┌───────────┴──┐  ┌──────────┐  ┌──────────┐  │
│  │ Memory   │  │    Tools     │  │   RAG    │  │Providers │  │
│  │ Manager  │  │  ┌─────────┐ │  │ Pipeline │  │          │  │
│  │          │  │  │Retrieval│ │  │          │  │Silicon   │  │
│  │ Short-   │  │  │WebSearch│ │  │ Loader   │  │Flow      │  │
│  │ term     │  │  │Calc     │ │  │ Splitter │  │          │  │
│  │ Summary  │  │  └─────────┘ │  │ Embed    │  │Qwen      │  │
│  └──────────┘  └──────────────┘  │ Rerank   │  │          │  │
│                                  │ ChromaDB │  │Ollama    │  │
│                                  └──────────┘  └──────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Features

- **RAG Pipeline** — Upload PDF, DOCX, TXT, Markdown → chunk → embed → retrieve with citations
- **Agent Workflow** — LangGraph state machine: Router → Retrieval/Tool → Planner → Generate → Reflect
- **Tool Calling** — Retrieval, Web Search (DuckDuckGo), Calculator (safe AST eval)
- **Memory** — Short-term (sliding window) + Summary (LLM-compressed)
- **Streaming** — Token-by-token output via WebSocket and SSE
- **Multi-Provider** — SiliconFlow, Qwen, Ollama with unified interface
- **Provider Abstraction** — Agent layer never knows which model it talks to

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, asyncio, WebSocket |
| Agent | LangGraph (StateGraph) |
| RAG | ChromaDB, bge-small-zh-v1.5, ms-marco-MiniLM-L-6-v2 |
| LLM | OpenAI-compatible (SiliconFlow, Qwen, Ollama) |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Deploy | Docker, Docker Compose |

## Project Structure

```
backend/
 ├── main.py                      # FastAPI entry point
 ├── config.py                    # pydantic-settings config
 ├── api/
 │   ├── chat.py                  # Direct chat endpoints
 │   ├── rag.py                   # File upload + RAG query
 │   ├── agent.py                 # Agent workflow endpoint
 │   ├── websocket.py             # WebSocket real-time chat
 │   └── health.py                # Health check
 ├── providers/
 │   ├── base.py                  # LLMProvider ABC
 │   ├── siliconflow.py           # SiliconFlow provider
 │   ├── qwen.py                  # Qwen (DashScope) provider
 │   └── ollama.py                # Ollama local provider
 ├── rag/
 │   ├── loaders.py               # BaseLoader + PDF/TXT/DOCX/MD
 │   ├── splitter.py              # RecursiveCharacterTextSplitter
 │   ├── embedding.py             # bge-small-zh-v1.5 embedding service
 │   ├── vectorstore.py           # ChromaDB wrapper
 │   ├── reranker.py              # ms-marco-MiniLM cross-encoder
 │   └── retriever.py             # Search + rerank orchestrator
 ├── tools/
 │   ├── base.py                  # BaseTool ABC
 │   ├── registry.py              # ToolRegistry
 │   ├── retrieval_tool.py        # RAG knowledge base search
 │   ├── web_search_tool.py       # DuckDuckGo search (ddgs)
 │   └── calculator_tool.py       # Safe math evaluation
 ├── memory/
 │   └── manager.py               # MemoryManager (short-term + summary)
 ├── workflow/
 │   ├── state.py                 # AgentState TypedDict
 │   ├── nodes.py                 # 6 workflow nodes
 │   └── graph.py                 # LangGraph StateGraph
 ├── schemas/
 │   └── chat.py                  # Pydantic models
 └── services/
     └── provider_registry.py     # Provider singleton registry

frontend/
 ├── src/
 │   ├── app/
 │   │   ├── page.tsx             # Main page
 │   │   ├── layout.tsx           # Root layout
 │   │   └── globals.css          # Tailwind + animations
 │   ├── components/
 │   │   ├── Chat.tsx             # Chat orchestrator
 │   │   ├── ChatMessage.tsx      # Message bubble
 │   │   ├── ChatInput.tsx        # Input form
 │   │   ├── AgentStatus.tsx      # Status indicators
 │   │   └── ProviderSelector.tsx # Provider dropdown
 │   ├── hooks/
 │   │   └── useWebSocket.ts      # WebSocket hook
 │   └── lib/
 │       └── api.ts               # API endpoints
 └── next.config.ts
```

## Quick Start

### Prerequisites

- Python 3.11 (required — 3.13 has compatibility issues with sentence-transformers)
- Node.js 18+
- At least one LLM API key (SiliconFlow recommended — free tier available)

### 1. Clone and configure

```bash
git clone https://github.com/dreemerx/agentic-rag-assistant.git
cd agentic-rag-assistant
cp .env.example .env
# Edit .env — add your API key
```

### 2. Start backend

```bash
python -m venv .venv
source .venv/Scripts/activate  # Linux: source .venv/bin/activate
pip install -r requirements.txt

# Set Hugging Face mirror (for China users)
export HF_ENDPOINT=https://hf-mirror.com

# Start server
PYTHONPATH=. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Docker (one command)

```bash
cp .env.example .env
# Edit .env with your API keys
docker compose up --build
```

## API Reference

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat/stream` | Streaming chat (SSE) |
| `POST` | `/api/v1/chat/completions` | Non-streaming chat |
| `GET` | `/api/v1/chat/providers` | List available providers |

### RAG

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/rag/upload` | Upload document (admin) |
| `POST` | `/api/v1/rag/query` | Search knowledge base |
| `GET` | `/api/v1/rag/files` | List indexed files |
| `DELETE` | `/api/v1/rag/files/{id}` | Delete file |

### Agent

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/agent/chat` | Full agent workflow (SSE) |
| `POST` | `/api/v1/agent/reset` | Reset session |
| `WS` | `/ws/chat` | WebSocket real-time chat |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEFAULT_PROVIDER` | No | `siliconflow` | Default LLM provider |
| `SILICONFLOW_API_KEY` | Yes* | — | SiliconFlow API key |
| `SILICONFLOW_MODEL` | No | `Qwen/Qwen2.5-7B-Instruct` | Model name |
| `QWEN_API_KEY` | No | — | Qwen (DashScope) API key |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434/v1` | Ollama endpoint |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |
| `HF_ENDPOINT` | No | — | Hugging Face mirror (e.g. `https://hf-mirror.com`) |

*At least one provider API key is required.

## Notes

- **Python 3.11 required** — Python 3.13 causes segfault with sentence-transformers
- **Hugging Face mirror** — Set `HF_ENDPOINT=https://hf-mirror.com` if you're in China
- **Memory usage** — Embedding model (~90MB) loads on first request; allow a few seconds
- **RAG upload** — Admin-only operation via API, not exposed in frontend chat UI

## Deployment

### Backend (Railway / Render)

1. Push to GitHub
2. Connect repo to Railway or Render
3. Set environment variables from `.env`
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)

1. Push to GitHub
2. Import project in Vercel
3. Set root directory to `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL=https://your-backend-url`
5. Deploy

### Docker

```bash
# Build and run
docker compose up --build -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

## License

MIT
