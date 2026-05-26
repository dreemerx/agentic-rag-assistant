"""
Ollama Provider (local fallback).

Ollama runs locally and exposes an OpenAI-compatible endpoint.
No API key needed — ideal for offline development and testing.
"""

from typing import AsyncIterator
from openai import AsyncOpenAI
from backend.providers.base import LLMProvider
from backend.schemas.chat import ChatMessage
from backend.config import settings


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        # Ollama doesn't need an API key
        self.client = AsyncOpenAI(api_key="ollama", base_url=self.base_url)

    def _to_openai_messages(self, messages: list[ChatMessage]) -> list[dict]:
        return [{"role": m.role.value, "content": m.content} for m in messages]

    async def chat(self, messages: list[ChatMessage], temperature: float = 0.7) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self._to_openai_messages(messages),
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def stream_chat(
        self, messages: list[ChatMessage], temperature: float = 0.7
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self._to_openai_messages(messages),
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
