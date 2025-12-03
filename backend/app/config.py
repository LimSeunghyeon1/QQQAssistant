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

    # Pricing
    exchange_rate: float = 185.2
    default_margin: float = 15.0
    vat_rate: float = 10.0
    default_delivery: float = 3500.0

    # Content helpers
    return_policy_image_url: str | None = None


settings = Settings()
