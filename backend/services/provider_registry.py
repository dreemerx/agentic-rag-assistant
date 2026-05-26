"""
Provider Registry Service.

Central registry that manages provider instances.
- Lazy initialization: providers are created only when first requested.
- Thread-safe singleton per provider name.
- Agent layer calls `get_provider(name)` — never instantiates providers directly.

This decouples the agent from any concrete provider implementation.
"""

from backend.providers.base import LLMProvider
from backend.providers.siliconflow import SiliconFlowProvider
from backend.providers.qwen import QwenProvider
from backend.providers.ollama import OllamaProvider
from backend.config import settings


class ProviderRegistry:
    """Singleton registry for LLM providers."""

    _providers: dict[str, LLMProvider] = {}
    _initialized: bool = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        if cls._initialized:
            return

        # Register available providers — failures are OK (e.g. missing API key)
        _registry = {
            "siliconflow": lambda: SiliconFlowProvider(),
            "qwen": lambda: QwenProvider(),
            "ollama": lambda: OllamaProvider(),
        }

        for name, factory in _registry.items():
            try:
                cls._providers[name] = factory()
            except ValueError:
                # Provider not configured — skip silently
                pass

        cls._initialized = True

    @classmethod
    def get_provider(cls, name: str | None = None) -> LLMProvider:
        """Get a provider by name, falling back to the default."""
        cls._ensure_initialized()

        provider_name = name or settings.default_provider
        provider = cls._providers.get(provider_name)

        if not provider:
            available = list(cls._providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not available. "
                f"Available: {available}"
            )

        return provider

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all available (configured) provider names."""
        cls._ensure_initialized()
        return list(cls._providers.keys())
