import pytest
from pydantic import ValidationError

from src.infoservice.settings import Settings


@pytest.fixture
def valid_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/infoservice")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("APP_ENCRYPTION_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=")


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


def test_settings_reject_invalid_app_encryption_key_at_startup(monkeypatch, valid_env):
    invalid_key = "not-a-fernet-key"
    monkeypatch.setenv("APP_ENCRYPTION_KEY", invalid_key)

    with pytest.raises(ValidationError) as exc:
        Settings()

    assert "APP_ENCRYPTION_KEY must be a valid Fernet key" in str(exc.value)
    assert invalid_key not in str(exc.value)
