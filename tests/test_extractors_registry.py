from __future__ import annotations

from typing import Dict

from pydantic import TypeAdapter

from src.extractors import ExtractorRegistry, FirecrawlExtractor, TrafilaturaExtractor
from src.models import ExtractorConfig, FirecrawlExtractorConfig, TrafilaturaExtractorConfig


def test_default_trafilatura_registered():
    registry = ExtractorRegistry({})
    assert isinstance(registry.get("trafilatura"), TrafilaturaExtractor)


def test_default_trafilatura_uses_default_config():
    registry = ExtractorRegistry({})
    extractor = registry.get("trafilatura")
    assert extractor._config == TrafilaturaExtractorConfig()


def test_default_firecrawl_registered():
    registry = ExtractorRegistry({})
    extractor = registry.get("firecrawl")
    assert isinstance(extractor, FirecrawlExtractor)
    assert extractor._config == FirecrawlExtractorConfig()


def test_firecrawl_config_parsed_from_json():
    extractors = TypeAdapter(Dict[str, ExtractorConfig]).validate_python(
        {"fc": {"type": "firecrawl", "api_key_env": "MY_KEY"}}
    )
    named = ExtractorRegistry(extractors).get("fc")
    assert isinstance(named, FirecrawlExtractor)
    assert named._config.api_key_env == "MY_KEY"
    assert named._config.only_main_content is True


def test_unknown_name_returns_none():
    registry = ExtractorRegistry({})
    assert registry.get("nonexistent") is None


def test_user_config_overrides_default():
    registry = ExtractorRegistry({"trafilatura": TrafilaturaExtractorConfig(favor_precision=True)})
    extractor = registry.get("trafilatura")
    assert isinstance(extractor, TrafilaturaExtractor)
    assert extractor._config.favor_precision is True


def test_named_entry_added_alongside_defaults():
    registry = ExtractorRegistry({"my-ext": TrafilaturaExtractorConfig(favor_recall=True)})
    named = registry.get("my-ext")
    assert isinstance(named, TrafilaturaExtractor)
    assert named._config.favor_recall is True
    assert registry.get("trafilatura") is not None
