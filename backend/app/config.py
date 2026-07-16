"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    app_name: str = "Clinical Trial Management System"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./ctms.db"
    test_database_url: str = "sqlite+aiosqlite:///./ctms_test.db"
    secret_key: str = "change-me-in-production"
    webhook_secret: str = "ctms-webhook-secret"
    redis_url: str = "redis://localhost:6379/0"
    api_v1_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
