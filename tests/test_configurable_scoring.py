from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.ai.analyzer import ContentAnalyzer
from src.ai.prompts import CONTENT_ANALYSIS_SYSTEM
from src.models import (
    ContentItem,
    FilteringConfig,
    ScoreCriterionConfig,
    SourceType,
)
from src.orchestrator import HorizonOrchestrator
from src.scoring import aggregate_custom_score
from src.storage.manager import StorageManager


def _item(item_id: str = "rss:test:1") -> ContentItem:
    return ContentItem(
        id=item_id,
        source_type=SourceType.RSS,
        title=f"Item {item_id}",
        url="https://example.com/item",
        published_at=datetime(2026, 7, 25, tzinfo=timezone.utc),
    )


def _criterion(
    name: str,
    threshold: float,
    description: str | None = None,
) -> ScoreCriterionConfig:
    return ScoreCriterionConfig(
        name=name,
        threshold=threshold,
        description=description or f"Relevance to {name}",
    )


class RecordingClient:
    def __init__(self, response: object):
        self.response = response
        self.calls: list[dict[str, str]] = []
        self.config = SimpleNamespace()

    async def complete(self, **kwargs: str) -> str:
        self.calls.append(kwargs)
        return json.dumps(self.response)


def _filter(
    filtering: FilteringConfig,
    items: list[ContentItem],
):
    orchestrator = HorizonOrchestrator.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(filtering=filtering)
    orchestrator.console = SimpleNamespace(print=lambda *args, **kwargs: None)
    return asyncio.run(
        orchestrator.filter_items(
            items,
            topic_dedup=False,
            apply_balance=False,
            log=False,
        )
    )


def test_legacy_config_keeps_existing_prompt_parser_and_threshold_behavior() -> None:
    filtering = FilteringConfig(ai_score_threshold=7.0)
    client = RecordingClient(
        {
            "score": 7,
            "reason": "Legacy relevant",
            "summary": "Legacy summary",
            "tags": ["legacy"],
        }
    )
    item = _item()

    asyncio.run(ContentAnalyzer(client, filtering)._analyze_item(item))
    result = _filter(filtering, [item])

    assert filtering.score_criteria is None
    assert client.calls[0]["system"] == CONTENT_ANALYSIS_SYSTEM
    assert '"score": <number>' in client.calls[0]["user"]
    assert item.ai_score == 7.0
    assert item.ai_scores == {}
    assert result.items == [item]
    assert result.unscored_count == 0


def test_single_custom_criterion_drives_prompt_parse_and_equal_threshold() -> None:
    filtering = FilteringConfig(
        score_criteria=[
            _criterion(
                "finance",
                6.0,
                "Relevance to markets and investment decisions",
            )
        ]
    )
    client = RecordingClient(
        {
            "scores": {"finance": 6},
            "reason": "Directly relevant",
            "summary": "Market update",
            "tags": ["finance"],
        }
    )
    item = _item()

    asyncio.run(ContentAnalyzer(client, filtering)._analyze_item(item))
    result = _filter(filtering, [item])

    system_prompt = client.calls[0]["system"]
    user_prompt = client.calls[0]["user"]
    assert '"name": "finance"' in system_prompt
    assert '"filter_threshold": 6.0' in system_prompt
    assert "markets and investment decisions" in system_prompt
    assert '"finance": "<number 0-10>"' in user_prompt
    assert item.ai_scores == {"finance": 6.0}
    assert item.ai_score == 6.0
    assert result.items == [item]


def test_multiple_criteria_any_keeps_item_when_one_dimension_matches() -> None:
    filtering = FilteringConfig(
        filter_mode="any",
        score_criteria=[
            _criterion("tech", 7.0),
            _criterion("finance", 6.0),
        ],
    )
    item = _item()
    item.ai_scores = {"tech": 5.0, "finance": 6.0}

    result = _filter(filtering, [item])

    assert result.items == [item]
    assert item.ai_score == 6.0


def test_multiple_criteria_all_requires_every_dimension() -> None:
    filtering = FilteringConfig(
        filter_mode="all",
        score_criteria=[
            _criterion("tech", 7.0),
            _criterion("finance", 6.0),
        ],
    )
    passing = _item("rss:test:passing")
    passing.ai_scores = {"tech": 7.0, "finance": 6.0}
    failing = _item("rss:test:failing")
    failing.ai_scores = {"tech": 8.0, "finance": 5.9}

    result = _filter(filtering, [passing, failing])

    assert result.items == [passing]
    assert passing.ai_score == 6.0
    assert failing.ai_score == 5.9


def test_filter_keeps_persisted_score_errors_diagnostic() -> None:
    legacy = _item("rss:test:legacy-missing")
    legacy_result = _filter(FilteringConfig(), [legacy])

    assert legacy_result.unscored_count == 1
    assert legacy.ai_analysis_error == "Missing legacy AI score"

    invalid_legacy = _item("rss:test:legacy-invalid")
    invalid_legacy.ai_score = float("nan")
    invalid_legacy_result = _filter(FilteringConfig(), [invalid_legacy])

    assert invalid_legacy_result.unscored_count == 1
    assert "Invalid legacy AI score" in (invalid_legacy.ai_analysis_error or "")

    custom_filtering = FilteringConfig(
        score_criteria=[_criterion("tech", 7.0)]
    )
    unexpected = _item("rss:test:unexpected")
    unexpected.ai_scores = {"tech": 8.0, "other": 9.0}
    malformed = _item("rss:test:malformed")
    malformed.ai_scores = {"tech": "8"}  # type: ignore[dict-item]

    custom_result = _filter(custom_filtering, [unexpected, malformed])

    assert custom_result.items == []
    assert custom_result.unscored_count == 2
    assert "unexpected criteria: other" in (unexpected.ai_analysis_error or "")
    assert "Invalid score for criterion 'tech'" in (malformed.ai_analysis_error or "")


def test_uniform_threshold_override_is_validated_and_applied() -> None:
    filtering = FilteringConfig(
        score_criteria=[_criterion("tech", 9.0)]
    )
    item = _item()
    item.ai_scores = {"tech": 7.0}
    orchestrator = HorizonOrchestrator.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(filtering=filtering)
    orchestrator.console = SimpleNamespace(print=lambda *args, **kwargs: None)

    result = asyncio.run(
        orchestrator.filter_items(
            [item],
            threshold=7.0,
            topic_dedup=False,
            apply_balance=False,
            log=False,
        )
    )
    assert result.items == [item]

    with pytest.raises(ValueError, match="finite number from 0 to 10"):
        asyncio.run(
            orchestrator.filter_items(
                [item],
                threshold=11.0,
                topic_dedup=False,
                apply_balance=False,
                log=False,
            )
        )


def test_aggregate_rejects_unknown_mode_defensively() -> None:
    with pytest.raises(ValueError, match="Unsupported filter mode"):
        aggregate_custom_score({"tech": 7.0}, "unknown")


@pytest.mark.parametrize(
    ("scores", "error_fragment"),
    [
        ({"tech": 8.0}, "missing criteria: finance"),
        ({"tech": 8.0, "finance": 7.0, "other": 9.0}, "unexpected criteria: other"),
        ({"tech": "8", "finance": 7.0}, "finite number"),
        ({"tech": 8.0, "finance": 11}, "finite number"),
    ],
)
def test_custom_model_missing_or_malformed_scores_are_diagnostic(
    scores: dict[str, object],
    error_fragment: str,
) -> None:
    filtering = FilteringConfig(
        score_criteria=[
            _criterion("tech", 7.0),
            _criterion("finance", 6.0),
        ]
    )
    client = RecordingClient(
        {
            "scores": scores,
            "reason": "Model output",
            "summary": "Summary",
            "tags": ["test"],
        }
    )
    item = _item()

    asyncio.run(ContentAnalyzer(client, filtering)._analyze_item(item))
    result = _filter(filtering, [item])

    assert item.ai_score is None
    assert item.ai_scores == {}
    assert item.ai_analysis_error
    assert error_fragment in item.ai_analysis_error
    assert result.items == []
    assert result.unscored_count == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"score_criteria": []},
        {
            "score_criteria": [
                {
                    "name": "Tech",
                    "description": "First",
                    "threshold": 7,
                },
                {
                    "name": "tech",
                    "description": "Duplicate by case",
                    "threshold": 6,
                },
            ]
        },
        {
            "score_criteria": [
                {
                    "name": "finance",
                    "description": "Finance",
                    "threshold": -0.1,
                }
            ]
        },
        {
            "score_criteria": [
                {
                    "name": "finance",
                    "description": "Finance",
                    "threshold": 10.1,
                }
            ]
        },
        {
            "score_criteria": [
                {
                    "name": "finance",
                    "description": "Finance",
                    "threshold": "6",
                }
            ]
        },
        {"ai_score_threshold": float("nan")},
        {"filter_mode": "some"},
    ],
)
def test_invalid_custom_scoring_config_is_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        FilteringConfig(**kwargs)


def test_config_load_prompt_parse_and_final_filter_are_semantically_consistent(
    tmp_path,
) -> None:
    config_payload = {
        "version": "1.0",
        "ai": {
            "provider": "openai",
            "model": "test-model",
            "api_key_env": "TEST_API_KEY",
        },
        "sources": {},
        "filtering": {
            "ai_score_threshold": 9.5,
            "filter_mode": "any",
            "score_criteria": [
                {
                    "name": "tech",
                    "description": "Technical depth",
                    "threshold": 8.0,
                },
                {
                    "name": "finance",
                    "description": "Financial relevance",
                    "threshold": 6.0,
                },
            ],
        },
    }
    (tmp_path / "config.json").write_text(
        json.dumps(config_payload),
        encoding="utf-8",
    )
    config = StorageManager(data_dir=str(tmp_path)).load_config()
    client = RecordingClient(
        {
            "scores": {"tech": 4.0, "finance": 6.0},
            "reason": "Matches finance only",
            "summary": "Finance story",
            "tags": ["finance"],
        }
    )
    item = _item()

    asyncio.run(ContentAnalyzer(client, config.filtering)._analyze_item(item))
    result = _filter(config.filtering, [item])

    assert '"tech": "<number 0-10>"' in client.calls[0]["user"]
    assert '"finance": "<number 0-10>"' in client.calls[0]["user"]
    assert item.ai_scores == {"tech": 4.0, "finance": 6.0}
    assert result.items == [item]
    assert config.filtering.ai_score_threshold == 9.5
