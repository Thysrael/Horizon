from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .security.credentials import validate_fernet_key


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

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

    @field_validator("app_encryption_key")
    @classmethod
    def validate_app_encryption_key(cls, value: SecretStr) -> SecretStr:
        validate_fernet_key(value.get_secret_value())
        return value
