from types import SimpleNamespace

import httpx
import pytest

from src.infoservice.bot.source_forms import (
    STABLE_SOURCE_TYPES,
    SourceDraft,
    SourceFieldError,
    apply_field,
    format_source_card,
    parse_primary,
    resolve_rss_name,
    validated_config,
)
from src.infoservice.sources.catalog import SourceCatalog


def settings():
    return SimpleNamespace(enable_twitter=False, enable_openbb=False)


def test_catalog_exposes_exactly_four_stable_capabilities():
    assert [item.type for item in SourceCatalog.stable()] == list(STABLE_SOURCE_TYPES)


@pytest.mark.parametrize(
    ("raw", "channel"),
    [
        ("@python_news", "python_news"),
        ("https://t.me/python_news", "python_news"),
        ("python_news", "python_news"),
    ],
)
def test_parse_telegram_target(raw, channel):
    assert parse_primary("telegram", raw) == {"channel": channel}


def test_parse_rss_derives_safe_default_name():
    assert parse_primary("rss", "https://blog.example.com/feed.xml") == {
        "url": "https://blog.example.com/feed.xml",
        "name": "blog.example.com",
    }


def test_parse_github_repo_and_user_targets():
    assert parse_primary("github", "https://github.com/pallets/flask", "repo_releases") == {
        "type": "repo_releases",
        "owner": "pallets",
        "repo": "flask",
    }
    assert parse_primary("github", "https://github.com/octocat", "user_events") == {
        "type": "user_events",
        "username": "octocat",
    }


def test_hackernews_defaults_validate_through_source_catalog():
    draft = SourceDraft.new("report-id", "hackernews")
    assert validated_config(draft, settings())["fetch_top_stories"] == 30
    assert validated_config(draft, settings())["min_score"] == 100


def test_apply_field_returns_new_draft_and_normalizes_optional_category():
    draft = SourceDraft.new("report-id", "telegram").with_values(channel="python_news")
    updated = apply_field(draft, "category", "-")
    assert updated is not draft
    assert updated.values["category"] is None


def test_invalid_target_has_field_reason_and_example():
    with pytest.raises(SourceFieldError) as error:
        parse_primary("telegram", "https://t.me/+private")
    assert error.value.field == "channel"
    assert "@durov" in error.value.example


def test_human_card_contains_no_json_or_internal_field_names():
    text = format_source_card(
        "telegram",
        {"channel": "python_news", "fetch_limit": 20, "category": "Python"},
    )
    assert "@python_news" in text
    assert "20" in text
    assert "fetch_limit" not in text
    assert "{" not in text


@pytest.mark.asyncio
async def test_rss_name_uses_feed_title(monkeypatch):
    async def safe_request(*_args, **_kwargs):
        return SimpleNamespace(
            content=b"<rss><channel><title>Python Weekly</title></channel></rss>",
            raise_for_status=lambda: None,
        )

    monkeypatch.setattr("src.infoservice.bot.source_forms.safe_request", safe_request)
    assert (
        await resolve_rss_name("https://example.com/feed.xml", SimpleNamespace())
        == "Python Weekly"
    )


@pytest.mark.asyncio
async def test_rss_name_falls_back_to_hostname_on_fetch_failure(monkeypatch):
    async def safe_request(*_args, **_kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr("src.infoservice.bot.source_forms.safe_request", safe_request)
    assert (
        await resolve_rss_name("https://blog.example.com/feed.xml", SimpleNamespace())
        == "blog.example.com"
    )
