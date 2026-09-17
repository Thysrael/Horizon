from __future__ import annotations

import json
import os
from pathlib import Path

from src.mcp.horizon_adapter import (
    _load_mcp_secrets,
    apply_source_filter,
    get_enabled_sources,
    load_config,
    load_runtime,
    resolve_config_path,
    resolve_horizon_path,
)
from src.models import AIProvider, Config, SOURCE_REGISTRY, SourceType


def test_resolve_horizon_path_accepts_explicit_repo() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    assert resolve_horizon_path(str(repo_root)) == repo_root.resolve()


def test_resolve_config_path_defaults_to_repo_data_config(tmp_path: Path) -> None:
    # Create a temporary config.json so resolve_config_path doesn't raise
    config_path = tmp_path / "data" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("{}", encoding="utf-8")

    assert resolve_config_path(tmp_path) == config_path.resolve()


def test_load_mcp_secrets_loads_generic_env_keys(tmp_path: Path, monkeypatch) -> None:
    secrets_path = tmp_path / "mcp.secrets.json"
    secrets_path.write_text(
        json.dumps(
            {
                "env": {
                    "ANTHROPIC_API_KEY": "sk-ant-test",
                    "CUSTOM_TOKEN": "token-123",
                    "lowercase": "ignored",
                }
            }
        ),
        encoding="utf-8",
    )

    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("HORIZON_MCP_SECRETS_PATH", str(secrets_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CUSTOM_TOKEN", raising=False)

    _load_mcp_secrets(repo_root, override=False)

    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test"
    assert os.environ["CUSTOM_TOKEN"] == "token-123"
    assert "lowercase" not in os.environ


def test_load_config_expands_env_vars(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "ai": {
                    "provider": "openai",
                    "model": "test-model",
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "${TEST_BASE_URL}/v1",
                },
                "sources": {},
                "collection": {},
                "digest": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TEST_BASE_URL", "https://api.example.com")
    runtime = load_runtime(Path(__file__).resolve().parents[1])

    config = load_config(runtime, config_path)

    assert config.ai.base_url == "https://api.example.com/v1"


def test_apply_source_filter_handles_twitter_and_openbb() -> None:
    config = Config.model_validate(
        {
            "ai": {
                "provider": AIProvider.OPENAI,
                "model": "test-model",
                "api_key_env": "OPENAI_API_KEY",
            },
            "sources": {
                "twitter": {
                    "enabled": True,
                    "users": ["openai"],
                    "keywords": ["LLM"],
                },
                "openbb": {
                    "enabled": True,
                    "watchlists": [{"name": "ai", "symbols": ["NVDA"]}],
                },
            },
            "collection": {},
            "digest": {},
        }
    )

    filtered, chosen, unknown = apply_source_filter(config, ["twitter"])

    assert chosen == ["twitter"]
    assert unknown == []
    assert filtered.sources.twitter.enabled is True
    assert filtered.sources.twitter.users == ["openai"]
    assert filtered.sources.twitter.keywords == ["LLM"]
    assert filtered.sources.openbb.enabled is False
    assert filtered.sources.openbb.watchlists == []

    filtered_openbb, chosen_openbb, unknown_openbb = apply_source_filter(
        config, ["openbb"]
    )
    assert chosen_openbb == ["openbb"]
    assert unknown_openbb == []
    assert filtered_openbb.sources.twitter.enabled is False
    assert filtered_openbb.sources.twitter.users == []
    assert filtered_openbb.sources.twitter.keywords == []


def test_mcp_source_registry_covers_model_source_types() -> None:
    assert set(SOURCE_REGISTRY) == {source.value for source in SourceType}


def test_mcp_filter_and_reporting_support_every_registered_source() -> None:
    config = Config.model_validate(
        {
            "ai": {"provider": "openai", "model": "test", "api_key_env": "KEY"},
            "collection": {},
            "digest": {},
            "sources": {
                "github": [{"type": "user_events", "username": "alice"}],
                "hackernews": {"enabled": True},
                "rss": [{"name": "Feed", "url": "https://example.com/feed"}],
                "reddit": {"enabled": True, "subreddits": [{"subreddit": "python"}]},
                "telegram": {"enabled": True, "channels": [{"channel": "updates"}]},
                "twitter": {"enabled": True, "users": ["openai"]},
                "openbb": {"enabled": True, "watchlists": [{"name": "tech", "symbols": ["NVDA"]}]},
                "ossinsight": {"enabled": True},
                "gdelt": {"enabled": True},
                "google_news": {"enabled": True},
            },
        }
    )

    assert set(get_enabled_sources(config)) == set(SOURCE_REGISTRY)
    for source_name in SOURCE_REGISTRY:
        filtered, chosen, unknown = apply_source_filter(config, [source_name])
        assert chosen == [source_name]
        assert unknown == []
        assert get_enabled_sources(filtered) == [source_name]

    _, chosen, unknown = apply_source_filter(config, ["google_news", "invalid"])
    assert chosen == ["google_news"]
    assert unknown == ["invalid"]
