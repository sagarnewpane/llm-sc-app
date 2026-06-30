from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings for the API service."""

    app_name: str = "LLM SC API"
    api_version_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./llm_sc.db"
    supabase_url: str = ""
    supabase_key: str = ""
    secret_key: str = "testing"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    groq_api_key: str = ""

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
