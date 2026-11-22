from __future__ import annotations

from pathlib import Path

import pytest

from src.models import AIConfig, AIProvider, Config
from src.setup import wizard


class _StopWizard(Exception):
    """Raised by a stubbed load_presets() to short-circuit main() for tests."""


def _prepare_main(monkeypatch, load_presets_calls):
    """Wire main() up to run until the preset-loading step, then stop."""

    def fake_load_presets(**kwargs):
        load_presets_calls.append(kwargs)
        raise _StopWizard()

    monkeypatch.setattr(wizard, "configure_logging", lambda console, level=None: None)
    monkeypatch.setattr(wizard.console, "print", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        wizard,
        "configure_ai",
        lambda: AIConfig(provider=AIProvider.OLLAMA, model="llama3.1", api_key_env=""),
    )
    monkeypatch.setattr(wizard, "get_interests", lambda: "test interests")
    monkeypatch.setattr(wizard, "load_presets", fake_load_presets)


def test_configure_ai_allows_ollama_without_api_key(monkeypatch):
    answers = iter(
        [
            "ollama",
            "llama3.2",
            "http://nas.local:11434",
            "",
            "zh,en",
        ]
    )

    prompt_consoles = []

    def answer_prompt(*args, **kwargs):
        prompt_consoles.append(kwargs.get("console"))
        return next(answers)

    monkeypatch.setattr(wizard.Prompt, "ask", answer_prompt)
    monkeypatch.setattr(wizard.console, "print", lambda *args, **kwargs: None)

    config = wizard.configure_ai()

    assert config == AIConfig(
        provider=AIProvider.OLLAMA,
        model="llama3.2",
        base_url="http://nas.local:11434",
        api_key_env="",
        temperature=0.3,
        max_tokens=8192,
        languages=["zh", "en"],
    )
    assert prompt_consoles == [wizard.console] * 5


def test_ai_recommendations_available_for_ollama_without_api_key():
    config = AIConfig(
        provider=AIProvider.OLLAMA,
        model="llama3.1",
        api_key_env="",
    )

    assert wizard._ai_recommendations_available(config) is True


def test_ai_recommendations_require_api_key_for_cloud_provider(monkeypatch):
    config = AIConfig(
        provider=AIProvider.OPENAI,
        model="gpt-4",
        api_key_env="OPENAI_API_KEY",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert wizard._ai_recommendations_available(config) is False

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert wizard._ai_recommendations_available(config) is True


def test_build_config_hackernews_follows_selection_and_count():
    ai = AIConfig(provider=AIProvider.OLLAMA, model="llama3.1", api_key_env="")

    rss_config = wizard.build_config(
        ai,
        [{"type": "rss", "config": {"name": "News", "url": "https://example.com/feed"}}],
    )
    default_config = wizard.build_config(ai, [])

    assert rss_config.sources.hackernews.enabled is False
    assert wizard._count_sources(rss_config) == 1
    assert default_config.sources.hackernews.enabled is True
    assert wizard._count_sources(default_config) == 1
    assert default_config.processing.profile_settings["tech-news"].threshold == 7.0
    assert default_config.processing.profile_settings["tech-blog"].topic_dedup is False
    assert default_config.digest.profile_order == [
        "tech-news",
        "tech-blog",
        "finance-news",
    ]


def test_merge_configs_preserves_all_existing_configuration_and_deduplicates_lists():
    existing = Config.model_validate(
        {
            "ai": {"provider": "openai", "model": "old", "api_key_env": "OLD_KEY"},
            "collection": {"time_window_hours": 36},
            "digest": {"max_items": 9},
            "extractors": {"html": {"type": "trafilatura", "favor_precision": True}},
            "email": {
                "imap_server": "imap.example.com", "smtp_server": "smtp.example.com",
                "email_address": "alerts@example.com", "enabled": True,
            },
            "webhook": {"url_env": "WEBHOOK_URL", "enabled": True},
            "sources": {
                "github": [
                    {"type": "user_events", "username": "alice", "enabled": False, "category": "old"},
                    {"type": "repo_releases", "owner": "acme", "repo": "core", "enabled": True},
                ],
                "hackernews": {"enabled": False, "fetch_top_stories": 77, "min_score": 12},
                "rss": [{"name": "Old", "url": "https://example.com/feed", "enabled": False}],
                "reddit": {
                    "enabled": False, "fetch_comments": 42,
                    "subreddits": [{"subreddit": "python", "enabled": False, "min_score": 99}],
                    "users": [{"username": "spez", "enabled": False, "fetch_limit": 3}],
                },
                "telegram": {
                    "enabled": False,
                    "channels": [{"channel": "updates", "enabled": False, "fetch_limit": 7}],
                },
                "twitter": {"enabled": True, "users": ["openai"], "fetch_limit": 4},
                "openbb": {"enabled": True, "watchlists": [{"name": "tech", "symbols": ["NVDA"]}]},
                "ossinsight": {"enabled": True, "keywords": ["agent"], "max_items": 8},
                "gdelt": {"enabled": True, "query": "robotics", "max_records": 13},
                "google_news": {"enabled": True, "query": "semiconductors", "country": "GB"},
            },
        }
    )
    new = wizard.build_config(
        AIConfig(provider=AIProvider.OLLAMA, model="new", api_key_env=""),
        [
            {"type": "github_user", "config": {"username": "alice"}},
            {"type": "github_user", "config": {"username": "alice"}},
            {"type": "rss", "config": {"name": "New", "url": "https://example.com/feed"}},
            {"type": "reddit_subreddit", "config": {"subreddit": "python"}},
            {"type": "reddit_user", "config": {"username": "spez"}},
            {"type": "telegram", "config": {"channel": "updates"}},
        ],
    )

    merged = wizard.merge_configs(new, existing)

    assert merged.extractors == existing.extractors
    assert merged.email == existing.email
    assert merged.webhook == existing.webhook
    assert merged.ai == new.ai
    assert merged.collection == existing.collection
    assert merged.digest == existing.digest
    for name in ("hackernews", "twitter", "openbb", "ossinsight", "gdelt", "google_news"):
        assert getattr(merged.sources, name) == getattr(existing.sources, name)
    assert merged.sources.reddit.enabled is False
    assert merged.sources.reddit.fetch_comments == 42
    assert merged.sources.telegram.enabled is False
    assert len(merged.sources.github) == 2
    assert len(merged.sources.rss) == 1
    assert len(merged.sources.reddit.subreddits) == 1
    assert len(merged.sources.reddit.users) == 1
    assert len(merged.sources.telegram.channels) == 1
    assert merged.sources.github[0].enabled is False
    assert merged.sources.github[0].category == "old"
    assert merged.sources.rss[0].enabled is False
    assert merged.sources.rss[0].name == "Old"
    assert merged.sources.reddit.subreddits[0].enabled is False
    assert merged.sources.reddit.subreddits[0].min_score == 99
    assert merged.sources.reddit.users[0].enabled is False
    assert merged.sources.reddit.users[0].fetch_limit == 3
    assert merged.sources.telegram.channels[0].enabled is False
    assert merged.sources.telegram.channels[0].fetch_limit == 7


def test_data_dir_and_config_flags_are_forwarded_to_storage_and_presets(monkeypatch, tmp_path):
    data_dir = tmp_path / "state"
    data_dir.mkdir()
    (data_dir / "presets.json").touch()
    config_path = tmp_path / "custom" / "horizon.json"
    storage_calls = []
    load_presets_calls = []

    class RecordingStorage:
        def __init__(self, data_dir, config_path):
            storage_calls.append({"data_dir": data_dir, "config_path": config_path})

    _prepare_main(monkeypatch, load_presets_calls)
    monkeypatch.setattr(wizard, "StorageManager", RecordingStorage)
    monkeypatch.setattr(
        "sys.argv",
        ["horizon-wizard", "--data-dir", str(data_dir), "--config", str(config_path)],
    )

    with pytest.raises(_StopWizard):
        wizard.main()

    assert storage_calls == [{"data_dir": str(data_dir), "config_path": str(config_path)}]
    assert load_presets_calls == [
        {"presets_path": str(data_dir / "presets.json"), "prefer_api": True}
    ]


def test_data_dir_and_config_default_to_data_directory(monkeypatch):
    storage_calls = []
    load_presets_calls = []

    class RecordingStorage:
        def __init__(self, data_dir, config_path):
            storage_calls.append({"data_dir": data_dir, "config_path": config_path})

    _prepare_main(monkeypatch, load_presets_calls)
    monkeypatch.setattr(wizard, "StorageManager", RecordingStorage)
    monkeypatch.setattr("sys.argv", ["horizon-wizard"])

    with pytest.raises(_StopWizard):
        wizard.main()

    assert storage_calls == [{"data_dir": "data", "config_path": None}]
    assert load_presets_calls == [
        {"presets_path": str(Path("data") / "presets.json"), "prefer_api": True}
    ]


def test_missing_custom_presets_falls_back_to_bundled_file(monkeypatch, tmp_path):
    load_presets_calls = []

    class RecordingStorage:
        def __init__(self, data_dir, config_path):
            pass

    _prepare_main(monkeypatch, load_presets_calls)
    monkeypatch.setattr(wizard, "StorageManager", RecordingStorage)
    monkeypatch.setattr(
        "sys.argv", ["horizon-wizard", "--data-dir", str(tmp_path / "state")]
    )

    with pytest.raises(_StopWizard):
        wizard.main()

    assert load_presets_calls == [
        {"presets_path": str(Path("data") / "presets.json"), "prefer_api": True}
    ]


def test_log_level_flag_is_forwarded_to_configure_logging(monkeypatch):
    logging_calls = []
    load_presets_calls = []

    class RecordingStorage:
        def __init__(self, data_dir, config_path):
            pass

    _prepare_main(monkeypatch, load_presets_calls)
    monkeypatch.setattr(wizard, "StorageManager", RecordingStorage)
    monkeypatch.setattr(
        wizard,
        "configure_logging",
        lambda console, level=None: logging_calls.append(level),
    )
    monkeypatch.setattr("sys.argv", ["horizon-wizard", "--log-level", "debug"])

    with pytest.raises(_StopWizard):
        wizard.main()

    assert logging_calls == ["DEBUG"]
