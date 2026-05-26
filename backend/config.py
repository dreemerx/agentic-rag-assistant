"""
Centralized configuration management using pydantic-settings.

All env vars are loaded once at startup and validated.
Provider-specific configs are nested under their own section.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # --- Default Provider ---
    default_provider: str = "siliconflow"

    # --- SiliconFlow ---
    siliconflow_api_key: Optional[str] = None
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_model: str = "Qwen/Qwen2.5-7B-Instruct"

    # --- Qwen (DashScope) ---
    qwen_api_key: Optional[str] = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen2.5:7b"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
