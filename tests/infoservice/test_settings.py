import pytest
from pydantic import ValidationError

from src.infoservice.settings import Settings


@pytest.fixture
def valid_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/infoservice")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("APP_ENCRYPTION_KEY", "encryption-key")


def test_settings_require_secrets(monkeypatch):
    for name in ("DATABASE_URL", "TELEGRAM_BOT_TOKEN", "APP_ENCRYPTION_KEY"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError):
        Settings()


def test_settings_parse_capabilities(monkeypatch, valid_env):
    monkeypatch.setenv("ENABLE_TWITTER", "true")
    settings = Settings()
    assert settings.enable_twitter is True
    assert settings.max_reports_per_user == 5
    assert settings.run_retention_days == 30
