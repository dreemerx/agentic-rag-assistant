"""
SiliconFlow Provider.

SiliconFlow offers an OpenAI-compatible API for Chinese LLMs at very low cost.
This makes it an ideal default provider for a zero-cost project.
"""

from typing import AsyncIterator
from openai import AsyncOpenAI
from backend.providers.base import LLMProvider
from backend.schemas.chat import ChatMessage
from backend.config import settings


class SiliconFlowProvider(LLMProvider):
    name = "siliconflow"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.siliconflow_api_key
        self.base_url = base_url or settings.siliconflow_base_url
        self.model = model or settings.siliconflow_model

        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY is required")

        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

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
