"""
Chat-related Pydantic schemas.

Why separate from API schemas: these are shared between the API layer,
the provider layer, and later the agent/workflow layer.
"""

from pydantic import BaseModel, Field
from enum import Enum


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    """Incoming chat request from the frontend."""

    messages: list[ChatMessage]
    provider: str | None = None  # override default provider
    model: str | None = None  # override default model
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = True


class ChatResponse(BaseModel):
    """Non-streaming response."""

    content: str
    provider: str
    model: str


class StreamChunk(BaseModel):
    """A single chunk in a streaming response."""

    delta: str
    done: bool = False
