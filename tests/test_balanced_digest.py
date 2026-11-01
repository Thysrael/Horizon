import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from rich.console import Console

from src.models import (
    AIConfig,
    CategoryGroupConfig,
    ClassificationResult,
    Config,
    ContentAnalysis,
    ContentItem,
    DigestConfig,
    ProcessingConfig,
    ProcessingResult,
    ProfileSettingsConfig,
    SourceType,
    SourcesConfig,
)
from src.orchestrator import HorizonOrchestrator
from src.processing import ProfileRegistry


def make_item(
    item_id: str,
    score: float,
    category: str | None,
    profile: str = "tech-news",
    resolved_profile: str | None = None,
) -> ContentItem:
    metadata = {"category": category} if category is not None else {}
    return ContentItem(
        id=item_id,
        source_type=SourceType.RSS,
        title=item_id,
        url=f"https://example.com/{item_id}",
        published_at=datetime.now(timezone.utc),
        metadata=metadata,
        profile=profile,
        processing=ProcessingResult(
            classification=ClassificationResult(
                profile=resolved_profile or profile, method="source_override"
            ),
            analysis=ContentAnalysis(
                score=score, reason="test", summary=item_id
            ),
        ),
    )


def make_orchestrator(digest: DigestConfig) -> HorizonOrchestrator:
    orchestrator = HorizonOrchestrator.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(
        digest=digest,
        processing=ProcessingConfig(
            profile_settings={
                "tech-news": ProfileSettingsConfig(threshold=7.0),
                "tech-blog": ProfileSettingsConfig(
                    threshold=4.0, topic_dedup=False
                ),
                "finance-news": ProfileSettingsConfig(threshold=7.0),
            }
        ),
    )
    orchestrator.console = Console(record=True)
    return orchestrator


def test_unconfigured_balanced_digest_preserves_old_behavior() -> None:
    items = [make_item("lower", 7.0, "ai"), make_item("higher", 9.0, "finance")]
    result = make_orchestrator(DigestConfig()).apply_balanced_digest(items)

    assert result.enabled is False
    assert result.items is items


def test_category_groups_apply_limits_and_default_group_limit() -> None:
    filtering = DigestConfig(
        category_groups={
            "ai": CategoryGroupConfig(limit=2, categories=["ai", "ml"]),
            "finance": CategoryGroupConfig(limit=1, categories=["finance"]),
        },
        default_group_limit=1,
    )
    items = [
        make_item("ai-low", 7.0, "ai"),
        make_item("finance-low", 6.0, "finance"),
        make_item("other-high", 9.5, "world"),
        make_item("ai-high", 9.0, "ml"),
        make_item("finance-high", 8.5, "finance"),
        make_item("ai-mid", 8.0, "ai"),
        make_item("other-low", 5.0, None),
    ]

    result = make_orchestrator(filtering).apply_balanced_digest(items)

    assert [item.id for item in result.items] == [
        "other-high",
        "ai-high",
        "finance-high",
        "ai-mid",
    ]
    assert result.group_counts == {"other": 1, "ai": 2, "finance": 1}


def test_max_items_applies_after_group_limits() -> None:
    filtering = DigestConfig(
        max_items=2,
        category_groups={
            "ai": CategoryGroupConfig(limit=2, categories=["ai"]),
            "finance": CategoryGroupConfig(limit=2, categories=["finance"]),
        },
    )
    items = [
        make_item("finance", 8.0, "finance"),
        make_item("ai-top", 10.0, "ai"),
        make_item("ai-second", 9.0, "ai"),
    ]

    result = make_orchestrator(filtering).apply_balanced_digest(items)

    assert [item.id for item in result.items] == ["ai-top", "ai-second"]
    assert result.group_counts == {"ai": 2}


def test_group_by_profile_limits_by_resolved_profile_with_shared_quota() -> None:
    filtering = DigestConfig(
        max_items=4,
        group_by="profile",
        category_groups={
            "tech": CategoryGroupConfig(limit=2, categories=["tech-news", "tech-blog"]),
            "finance": CategoryGroupConfig(limit=1, categories=["finance-news"]),
        },
        default_group_limit=1,
    )
    items = [
        make_item("news-top", 9.8, "finance", profile="tech-news"),
        make_item("blog-top", 9.6, None, profile="tech-blog"),
        make_item("news-second", 9.4, "tech-news", profile="tech-news"),
        make_item(
            "finance-top", 9.0, "tech-news", profile="tech-news", resolved_profile="finance-news"
        ),
        make_item("finance-second", 8.8, "finance-news", profile="finance-news"),
        make_item("creator-top", 8.6, "tech-news", profile="ai-creator"),
        make_item("creator-second", 8.4, "tech-news", profile="ai-creator"),
    ]

    result = make_orchestrator(filtering).apply_balanced_digest(items)

    assert [item.id for item in result.items] == [
        "news-top",
        "blog-top",
        "finance-top",
        "creator-top",
    ]
    assert result.group_counts == {"tech": 2, "finance": 1, "other": 1}


def test_group_by_profile_leaves_unmatched_profiles_uncapped_by_default() -> None:
    filtering = DigestConfig(
        group_by="profile",
        category_groups={
            "finance": CategoryGroupConfig(limit=1, categories=["finance-news"]),
        },
    )
    items = [
        make_item("news-1", 9.0, "finance-news", profile="tech-news"),
        make_item("news-2", 8.0, "finance-news", profile="tech-news"),
        make_item("news-3", 7.0, "finance-news", profile="tech-news"),
    ]

    result = make_orchestrator(filtering).apply_balanced_digest(items)

    assert [item.id for item in result.items] == ["news-1", "news-2", "news-3"]
    assert result.group_counts == {"other": 3}


def test_max_items_works_without_category_groups() -> None:
    filtering = DigestConfig(max_items=1)
    items = [make_item("lower", 7.0, None), make_item("higher", 9.0, None)]

    result = make_orchestrator(filtering).apply_balanced_digest(items)

    assert [item.id for item in result.items] == ["higher"]


def test_default_group_limit_works_without_category_groups() -> None:
    filtering = DigestConfig(default_group_limit=1)
    items = [make_item("lower", 7.0, None), make_item("higher", 9.0, None)]

    result = make_orchestrator(filtering).apply_balanced_digest(items)

    assert [item.id for item in result.items] == ["higher"]
    assert result.group_counts == {"other": 1}


def test_filter_items_skips_ai_topic_dedup_for_disabled_profile(monkeypatch) -> None:
    orchestrator = make_orchestrator(DigestConfig())
    orchestrator.profiles = ProfileRegistry.load(
        Path(__file__).resolve().parents[1] / "profiles", "tech-news"
    )
    items = [make_item("first", 9.0, "blog"), make_item("second", 8.0, "blog")]
    for item in items:
        item.profile = "tech-blog"
        item.processing.classification.profile = "tech-blog"

    async def unexpected_dedup(input_items, *, log=True):  # type: ignore[no-untyped-def]
        raise AssertionError("AI topic dedup must be skipped for tech-blog")

    monkeypatch.setattr(orchestrator, "merge_topic_duplicates", unexpected_dedup)

    result = asyncio.run(
        orchestrator.filter_items(items, topic_dedup=True, apply_balance=False, log=False)
    )

    assert [item.id for item in result.items] == ["first", "second"]


def test_runtime_threshold_override_takes_priority() -> None:
    orchestrator = make_orchestrator(DigestConfig())
    item = make_item("item", 7.5, "ai")

    assert orchestrator.passes_profile_filter(item)
    assert not orchestrator.passes_profile_filter(item, threshold=8.0)


def test_profile_without_threshold_bypasses_score_filter() -> None:
    orchestrator = make_orchestrator(DigestConfig())
    orchestrator.config.processing.profile_settings = {}

    assert orchestrator.passes_profile_filter(make_item("item", 1.0, "ai"))


def test_rejects_settings_for_unknown_profile() -> None:
    config = Config(
        ai=AIConfig(
            provider="openai",
            model="test",
            api_key_env="TEST_API_KEY",
        ),
        sources=SourcesConfig(),
        processing=ProcessingConfig(
            profile_settings={
                "missing": ProfileSettingsConfig(threshold=7.0)
            }
        ),
    )

    with pytest.raises(ValueError, match="Unknown processing profile: missing"):
        HorizonOrchestrator(config, SimpleNamespace())


def test_appends_profiles_missing_from_configured_order() -> None:
    config = Config(
        ai=AIConfig(
            provider="openai",
            model="test",
            api_key_env="TEST_API_KEY",
        ),
        sources=SourcesConfig(),
        digest=DigestConfig(profile_order=["tech-news", "tech-blog"]),
    )

    HorizonOrchestrator(config, SimpleNamespace())

    assert config.digest.profile_order == [
        "tech-news",
        "tech-blog",
        "ai-creator",
        "finance-news",
    ]


def test_rejects_unknown_profile_order() -> None:
    profile_order = ["tech-news", "tech-blog", "finance-news", "missing"]
    config = Config(
        ai=AIConfig(
            provider="openai",
            model="test",
            api_key_env="TEST_API_KEY",
        ),
        sources=SourcesConfig(),
        digest=DigestConfig(profile_order=profile_order),
    )

    with pytest.raises(ValueError, match="contains unknown profiles.*missing"):
        HorizonOrchestrator(config, SimpleNamespace())


def make_grouped_config(group_by: str) -> Config:
    return Config(
        ai=AIConfig(
            provider="openai",
            model="test",
            api_key_env="TEST_API_KEY",
        ),
        sources=SourcesConfig(),
        digest=DigestConfig(
            group_by=group_by,
            category_groups={
                "tech": CategoryGroupConfig(
                    limit=1, categories=["tech-news", "missing-profile"]
                )
            },
        ),
    )


def test_group_by_profile_rejects_unknown_profiles() -> None:
    with pytest.raises(ValueError, match="unknown profiles.*missing-profile"):
        HorizonOrchestrator(make_grouped_config("profile"), SimpleNamespace())


def test_group_by_category_does_not_check_profile_ids() -> None:
    HorizonOrchestrator(make_grouped_config("category"), SimpleNamespace())


def test_duplicate_category_warns_and_first_group_wins() -> None:
    filtering = DigestConfig(
        category_groups={
            "first": CategoryGroupConfig(limit=1, categories=["shared"]),
            "second": CategoryGroupConfig(limit=2, categories=["shared"]),
        }
    )
    orchestrator = make_orchestrator(filtering)

    result = orchestrator.apply_balanced_digest(
        [make_item("top", 9.0, "shared"), make_item("second", 8.0, "shared")]
    )

    assert [item.id for item in result.items] == ["top"]
    assert result.duplicate_categories == ["shared"]
    assert "using 'first'" in orchestrator.console.export_text()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_items": 0},
        {"default_group_limit": 0},
        {"category_groups": {"ai": {"limit": 0, "categories": ["ai"]}}},
        {"category_groups": {"ai": {"limit": 1, "categories": []}}},
        {"group_by": "source"},
        {"profile_order": ["tech-news", "tech-news"]},
        {"profile_order": ["tech-news", ""]},
    ],
)
def test_digest_config_rejects_invalid_values(kwargs) -> None:
    with pytest.raises(ValidationError):
        DigestConfig(**kwargs)


def test_run_applies_balanced_digest_before_enrichment(tmp_path, monkeypatch) -> None:
    config = Config(
        ai=AIConfig(
            provider="openai",
            model="test",
            api_key_env="TEST_API_KEY",
            languages=[],
        ),
        sources=SourcesConfig(),
        processing=ProcessingConfig(
            profile_settings={
                "tech-news": ProfileSettingsConfig(threshold=7.0)
            }
        ),
        digest=DigestConfig(
            max_items=1,
            category_groups={
                "ai": CategoryGroupConfig(limit=1, categories=["ai"]),
                "finance": CategoryGroupConfig(limit=1, categories=["finance"]),
            },
        ),
    )
    storage = SimpleNamespace()
    orchestrator = HorizonOrchestrator(config, storage)
    items = [
        make_item("ai", 9.0, "ai"),
        make_item("finance", 8.0, "finance"),
        make_item("below-threshold", 6.0, "ai"),
    ]
    enriched_ids: list[str] = []

    async def fetch_all_sources(since):  # type: ignore[no-untyped-def]
        return items

    async def analyze_content(input_items):  # type: ignore[no-untyped-def]
        return input_items

    async def merge_topic_duplicates(input_items, *, log=True):  # type: ignore[no-untyped-def]
        return input_items

    async def expand_twitter_discussion(input_items):  # type: ignore[no-untyped-def]
        return None

    async def enrich_important_items(input_items):  # type: ignore[no-untyped-def]
        enriched_ids.extend(item.id for item in input_items)

    monkeypatch.setattr(orchestrator, "fetch_all_sources", fetch_all_sources)
    monkeypatch.setattr(orchestrator, "analyze_items", analyze_content)
    monkeypatch.setattr(orchestrator, "merge_topic_duplicates", merge_topic_duplicates)
    monkeypatch.setattr(orchestrator, "_expand_twitter_discussion", expand_twitter_discussion)
    monkeypatch.setattr(orchestrator, "enrich_items", enrich_important_items)
    monkeypatch.chdir(tmp_path)

    asyncio.run(orchestrator.run())

    assert enriched_ids == ["ai"]


def test_run_balances_after_twitter_reanalysis(tmp_path, monkeypatch) -> None:
    config = Config(
        ai=AIConfig(
            provider="openai",
            model="test",
            api_key_env="TEST_API_KEY",
            languages=[],
        ),
        sources=SourcesConfig(),
        digest=DigestConfig(max_items=1),
    )
    orchestrator = HorizonOrchestrator(config, SimpleNamespace())
    items = [make_item("first", 9.0, "ai"), make_item("second", 8.0, "ai")]
    enriched_ids: list[str] = []

    async def fetch_all_sources(since):  # type: ignore[no-untyped-def]
        return items

    async def analyze_content(input_items):  # type: ignore[no-untyped-def]
        return input_items

    async def merge_topic_duplicates(input_items, *, log=True):  # type: ignore[no-untyped-def]
        return input_items

    async def expand_twitter_discussion(input_items):  # type: ignore[no-untyped-def]
        input_items[0].processing.analysis.score = 7.0
        input_items[1].processing.analysis.score = 10.0
        input_items.sort(
            key=lambda item: item.processing.analysis.score or 0,
            reverse=True,
        )

    async def enrich_important_items(input_items):  # type: ignore[no-untyped-def]
        enriched_ids.extend(item.id for item in input_items)

    monkeypatch.setattr(orchestrator, "fetch_all_sources", fetch_all_sources)
    monkeypatch.setattr(orchestrator, "analyze_items", analyze_content)
    monkeypatch.setattr(orchestrator, "merge_topic_duplicates", merge_topic_duplicates)
    monkeypatch.setattr(orchestrator, "_expand_twitter_discussion", expand_twitter_discussion)
    monkeypatch.setattr(orchestrator, "enrich_items", enrich_important_items)
    monkeypatch.chdir(tmp_path)

    asyncio.run(orchestrator.run())

    assert enriched_ids == ["second"]
