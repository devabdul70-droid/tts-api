from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central app configuration, overridable via environment variables / .env file."""

    APP_NAME: str = "TTS API"
    API_V1_PREFIX: str = "/api/v1"

    # TTS defaults
    DEFAULT_VOICE: str = "en-US-AvaNeural"
    DEFAULT_RATE: str = "-10%"
    DEFAULT_PITCH: str = "+0Hz"
    DEFAULT_VOLUME: str = "+0%"

    # Limits
    MAX_TEXT_LENGTH: int = 5000
    REQUEST_TIMEOUT_SECONDS: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
