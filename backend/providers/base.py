"""
LLM Provider Abstraction Layer.

Design rationale:
- All providers implement the same async interface → Agent layer never knows which backend it talks to.
- Uses OpenAI-compatible chat format so we can swap providers without changing message schemas.
- `stream_chat` yields tokens incrementally for real-time streaming to the frontend.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator
from backend.schemas.chat import ChatMessage


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    name: str = "base"

    @abstractmethod
    async def chat(self, messages: list[ChatMessage], temperature: float = 0.7) -> str:
        """Send a chat request and return the full response."""
        ...

    @abstractmethod
    async def stream_chat(
        self, messages: list[ChatMessage], temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """Send a chat request and yield tokens as they arrive."""
        ...
