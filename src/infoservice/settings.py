from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    telegram_bot_token: SecretStr
    app_encryption_key: SecretStr
    worker_concurrency: int = Field(default=2, ge=1, le=16)
    stale_run_minutes: int = Field(default=30, ge=5)
    scheduler_poll_seconds: int = Field(default=30, ge=5)
    run_retention_days: int = Field(default=30, ge=1)
    max_reports_per_user: int = 5
    max_sources_per_report: int = 30
    deepseek_default_model: str = "deepseek-v4-flash"
    enable_twitter: bool = False
    enable_openbb: bool = False
    apify_token: SecretStr | None = None
