import os
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    """
    Central configuration for the Voice Assistant application.
    Loaded from environment variables or defaults.
    """
    llm_routing_mode: str = Field(default_factory=lambda: os.getenv("LLM_ROUTING_MODE", "local_first"))
    stt_provider: str = Field(default_factory=lambda: os.getenv("STT_PROVIDER", "whisper"))
    max_steps: int = Field(default_factory=lambda: int(os.getenv("MAX_STEPS", "10")))
    timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("TIMEOUT_SECONDS", "120")))
    wake_word: str = Field(default_factory=lambda: os.getenv("WAKE_WORD", "Asistente"))
    locale: str = Field(default_factory=lambda: os.getenv("LOCALE", "es-ES"))

# Singleton instance to be used across the app
config = AppConfig()
