"""
Memory Manager.

Design rationale:
- Memory is NOT a Tool — it's a runtime context provider.
- Two memory types:
  1. Short-term: sliding window of the last N conversation turns.
  2. Summary: LLM-generated summary of the conversation so far.
- The agent workflow calls `memory.build_context()` to get a system prompt
  injection that includes both the summary and recent history.
- Summary is regenerated periodically (every N turns) to stay concise.

Why not just pass all history to the LLM?
- Token cost grows linearly with conversation length.
- Old messages become less relevant over time.
- Summary compresses key facts while recent turns preserve detail.
"""

from backend.schemas.chat import ChatMessage, Role
from backend.providers.base import LLMProvider


class MemoryManager:
    """Manages short-term and summary memory for a conversation."""

    def __init__(
        self,
        max_short_term: int = 10,
        summarize_every: int = 8,
    ):
        self.max_short_term = max_short_term
        self.summarize_every = summarize_every
        self._history: list[ChatMessage] = []
        self._summary: str = ""
        self._turns_since_summary: int = 0

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to conversation history."""
        self._history.append(message)
        self._turns_since_summary += 1

    def get_short_term(self) -> list[ChatMessage]:
        """Get the last N messages (sliding window)."""
        return self._history[-self.max_short_term:]

    def get_summary(self) -> str:
        """Get the current conversation summary."""
        return self._summary

    def get_full_history(self) -> list[ChatMessage]:
        """Get all messages (used for summarization)."""
        return list(self._history)

    def build_context(self, system_prompt: str = "") -> list[ChatMessage]:
        """
        Build the context messages for the LLM.

        Combines:
        1. System prompt (if provided)
        2. Conversation summary (if exists)
        3. Recent short-term messages
        """
        messages: list[ChatMessage] = []

        # System prompt with summary injection
        context_parts = []
        if system_prompt:
            context_parts.append(system_prompt)
        if self._summary:
            context_parts.append(f"\n\n[Conversation Summary]\n{self._summary}")

        if context_parts:
            messages.append(ChatMessage(
                role=Role.SYSTEM,
                content="\n".join(context_parts),
            ))

        # Recent history
        messages.extend(self.get_short_term())
        return messages

    def should_summarize(self) -> bool:
        """Check if it's time to generate a new summary."""
        return self._turns_since_summary >= self.summarize_every

    async def summarize(self, provider: LLMProvider) -> str:
        """
        Generate a conversation summary using the LLM.

        This compresses the full history into a concise summary
        that captures key topics, decisions, and context.
        """
        if not self._history:
            return ""

        # Build summarization prompt
        history_text = "\n".join(
            f"{m.role.value}: {m.content}" for m in self._history
        )

        summarize_messages = [
            ChatMessage(
                role=Role.SYSTEM,
                content=(
                    "You are a conversation summarizer. Summarize the following conversation "
                    "in 2-3 concise sentences. Focus on: key topics discussed, decisions made, "
                    "and any important context. Output ONLY the summary, nothing else."
                ),
            ),
            ChatMessage(
                role=Role.USER,
                content=f"Conversation to summarize:\n\n{history_text}",
            ),
        ]

        self._summary = await provider.chat(summarize_messages, temperature=0.3)
        self._turns_since_summary = 0
        return self._summary

    def clear(self) -> None:
        """Clear all memory."""
        self._history.clear()
        self._summary = ""
        self._turns_since_summary = 0
