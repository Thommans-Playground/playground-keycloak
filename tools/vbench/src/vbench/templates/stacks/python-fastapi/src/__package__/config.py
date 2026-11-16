"""Configuration: every environment-specific value is read from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    app_name: str = "{{NAME}}"
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/app"


@lru_cache
def get_settings() -> Settings:
    return Settings()
