from __future__ import annotations

import pytest

from src.infoservice.settings import Settings
from src.infoservice.sources.catalog import SourceCatalog, SourceValidationError


@pytest.fixture
def settings(monkeypatch) -> Settings:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://user:password@localhost/infoservice"
    )
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv(
        "APP_ENCRYPTION_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    )
    return Settings()


def test_optional_sources_follow_capabilities(settings):
    names = {item.type for item in SourceCatalog.available(settings)}
    assert {"rss", "telegram", "hackernews", "github"} <= names
    assert "twitter" not in names
    assert "openbb" not in names


def test_telegram_accepts_only_public_username(settings):
    parsed = SourceCatalog.validate("telegram", {"channel": "@example"}, settings)
    assert parsed.channel == "example"

    with pytest.raises(SourceValidationError):
        SourceCatalog.validate("telegram", {"channel": "https://t.me/+private"}, settings)


def test_catalog_rejects_unknown_input_fields(settings):
    with pytest.raises(SourceValidationError):
        SourceCatalog.validate(
            "rss",
            {"name": "Example", "url": "https://example.com/feed", "unexpected": True},
            settings,
        )
