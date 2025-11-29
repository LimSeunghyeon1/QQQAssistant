from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "sqlite:///./qqq_assistant.db"

    # External integrations
    translation_api_key: str | None = None
    translation_provider: str = "gcloud"
    google_application_credentials: str | None = None

    # Generated file locations
    sales_channel_export_dir: str = "./exports"


settings = Settings()
