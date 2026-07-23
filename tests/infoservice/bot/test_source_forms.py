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


@pytest.mark.parametrize("source_type", ("reddit", "twitter"))
def test_edit_rejects_non_stable_source_types(source_type):
    with pytest.raises(ValueError, match="unsupported stable source type"):
        SourceDraft.edit("source-id", source_type, {}, enabled=True)


@pytest.mark.parametrize("source_type", ("reddit", "twitter"))
def test_validated_config_rejects_non_stable_source_types(source_type):
    draft = SourceDraft(report_id="report-id", source_type=source_type)

    with pytest.raises(ValueError, match="unsupported stable source type"):
        validated_config(draft, settings())


def test_apply_field_returns_new_draft_and_normalizes_optional_category():
    draft = SourceDraft.new("report-id", "telegram").with_values(channel="python_news")
    updated = apply_field(draft, "category", "-")
    assert updated is not draft
    assert updated.values["category"] is None


def test_draft_values_are_immutable_and_storage_round_trip_is_defensive():
    draft = SourceDraft.new("report-id", "telegram").with_values(
        channel="python_news",
        filters={"authors": ["alice"]},
    )

    with pytest.raises(TypeError):
        draft.values["fetch_limit"] = 50
    with pytest.raises(AttributeError):
        draft.values["filters"]["authors"].append("bob")

    stored = draft.to_storage()
    assert stored["values"] == {
        "enabled": True,
        "fetch_limit": 20,
        "channel": "python_news",
        "filters": {"authors": ["alice"]},
    }
    restored = SourceDraft.from_storage(stored)
    stored["values"]["filters"]["authors"].append("bob")

    assert restored == draft
    assert restored.values["filters"]["authors"] == ("alice",)


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
