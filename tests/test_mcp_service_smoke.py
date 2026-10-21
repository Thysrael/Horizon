from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from src.models import (
    ClassificationResult,
    ContentAnalysis,
    ContentItem,
    DigestConfig,
    ProcessingConfig,
    ProcessingResult,
    ProfileSettingsConfig,
    SourceType,
)
from src.ai.summarizer import DailySummarizer
from src.ai.enricher import EnrichmentBatchResult
from src.mcp.server import hz_get_metrics
from src.mcp.errors import HorizonMcpError
from src.mcp.service import HorizonPipelineService
from src.orchestrator import (
    BalancedDigestResult,
    FetchReport,
    HorizonOrchestrator,
    SourceFetchOutcome,
)
from src.services.webhook import WebhookDeliveryResult, WebhookDeliveryStatus
from src.processing import ProfileRegistry


PROFILES = ProfileRegistry.load(
    Path(__file__).resolve().parents[1] / "profiles", "tech-news"
)


def make_item(item_id: str, score: float | None = None) -> ContentItem:
    item = ContentItem(
        id=item_id,
        source_type=SourceType.RSS,
        title=f"Item {item_id}",
        url=f"https://example.com/{item_id}",
        content="content",
        author="tester",
        published_at=datetime.now(timezone.utc),
        profile="tech-news",
        processing=ProcessingResult(
            classification=ClassificationResult(
                profile="tech-news", method="source_override"
            ),
            analysis=(
                ContentAnalysis(score=score, reason="test", summary=item_id)
                if score is not None
                else None
            ),
        ),
    )
    return item
def test_validate_config_smoke(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (repo_root / "data" / "config.example.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    result = asyncio.run(
        service.validate_config(
            horizon_path=str(repo_root),
            config_path=str(config_path),
            check_env=False,
        )
    )

    assert result["config_path"] == str(config_path.resolve())
    assert result["enabled_sources"]
    assert result["missing_env"] == []


def test_validate_config_rejects_unknown_group_by_profile(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config = json.loads(
        (repo_root / "data" / "config.example.json").read_text(encoding="utf-8")
    )
    config["digest"]["group_by"] = "profile"
    config["digest"]["category_groups"] = {
        "tech": {"limit": 1, "categories": ["tech-news", "missing-profile"]}
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    with pytest.raises(HorizonMcpError) as exc_info:
        asyncio.run(
            service.validate_config(
                horizon_path=str(repo_root),
                config_path=str(config_path),
                check_env=False,
            )
        )

    assert exc_info.value.code == "HZ_CONFIG_INVALID"
    assert "missing-profile" in exc_info.value.details["error"]


def test_get_effective_config_can_filter_sources(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config_path = tmp_path / "config.json"
    config_path.write_text(
        (repo_root / "data" / "config.example.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    result = service.get_effective_config(
        horizon_path=str(repo_root),
        config_path=str(config_path),
        sources=["rss"],
    )

    assert result["selected_sources"] == ["rss"]
    assert result["config"]["sources"]["github"] == []
    assert result["config"]["sources"]["rss"]


def test_get_effective_config_redacts_expanded_query_and_header_secrets(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config = json.loads((repo_root / "data" / "config.example.json").read_text(encoding="utf-8"))
    config["sources"]["rss"][0]["url"] = "https://example.com/feed?key=${FEED_TOKEN}&view=full"
    config["sources"]["rss"][1]["url"] = "https://${URL_USER}:${URL_PASSWORD}@example.com/private"
    config["webhook"]["headers"] = "Authorization: Bearer ${AUTH_TOKEN}\nX-Trace: useful"
    config["webhook"]["request_body"] = {"api_key": "${BODY_KEY}", "message": "useful"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv("FEED_TOKEN", "feed-secret")
    monkeypatch.setenv("AUTH_TOKEN", "header-secret")
    monkeypatch.setenv("BODY_KEY", "body-secret")
    monkeypatch.setenv("URL_USER", "private-user")
    monkeypatch.setenv("URL_PASSWORD", "private-password")

    result = HorizonPipelineService(runs_root=tmp_path / "runs").get_effective_config(
        horizon_path=str(repo_root), config_path=str(config_path)
    )
    rendered = json.dumps(result)

    assert "feed-secret" not in rendered
    assert "header-secret" not in rendered
    assert "body-secret" not in rendered
    assert "private-user" not in rendered
    assert "private-password" not in rendered
    assert result["config"]["sources"]["rss"][0]["url"] == (
        "https://example.com/feed?key=%3Credacted%3E&view=full"
    )
    assert result["config"]["sources"]["rss"][1]["url"] == "https://<redacted>@example.com/private"
    assert result["config"]["webhook"]["headers"] == "Authorization: <redacted>\nX-Trace: useful"
    assert result["config"]["webhook"]["request_body"] == {
        "api_key": "<redacted>",
        "message": "useful",
    }
    assert result["config"]["ai"]["api_key_env"] == "OPENAI_API_KEY"


def test_metrics_tool_smoke() -> None:
    result = hz_get_metrics()

    assert result["ok"] is True
    assert result["tool"] == "hz_get_metrics"


def test_fetch_items_uses_public_orchestrator_api(tmp_path: Path, monkeypatch) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    monkeypatch.setattr(service, "_profiles", lambda ctx: PROFILES)
    config_path = tmp_path / "config.json"

    monkeypatch.setattr(
        service,
        "_build_context",
        lambda **kwargs: (
            SimpleNamespace(
                horizon_path=tmp_path,
                config_path=config_path,
                config=SimpleNamespace(),
            ),
            ["rss"],
            [],
        ),
    )
    monkeypatch.setattr("src.mcp.service.make_storage", lambda config_path: object())

    class FakeOrchestrator:
        last_fetch_report = None

        async def fetch_all_sources(self, since):  # type: ignore[no-untyped-def]
            return [make_item("item-1"), make_item("item-2")]

        def merge_cross_source_duplicates(self, items):  # type: ignore[no-untyped-def]
            return items[:1]

    def build_orchestrator(config, storage, console, profiles):  # type: ignore[no-untyped-def]
        assert console is service.console
        assert profiles is PROFILES
        return FakeOrchestrator()

    monkeypatch.setattr(
        "src.mcp.service.HorizonOrchestrator",
        build_orchestrator,
    )

    result = asyncio.run(service.fetch_items(hours=6))

    assert result["fetched"] == 1
    assert result["raw_before_merge"] == 2
    assert service.run_store.load_items(result["run_id"], "raw")[0]["id"] == "item-1"


def test_fetch_items_includes_fetch_report_in_response_and_metadata(
    tmp_path: Path, monkeypatch
) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    monkeypatch.setattr(service, "_profiles", lambda ctx: PROFILES)
    config_path = tmp_path / "config.json"

    monkeypatch.setattr(
        service,
        "_build_context",
        lambda **kwargs: (
            SimpleNamespace(
                horizon_path=tmp_path,
                config_path=config_path,
                config=SimpleNamespace(),
            ),
            ["rss", "github"],
            [],
        ),
    )
    monkeypatch.setattr("src.mcp.service.make_storage", lambda config_path: object())

    class FakeOrchestrator:
        last_fetch_report = FetchReport(
            [
                SourceFetchOutcome("RSS Feeds", "success", [make_item("item-1")]),
                SourceFetchOutcome("GitHub", "failure", error="RuntimeError: down"),
            ]
        )

        async def fetch_all_sources(self, since):  # type: ignore[no-untyped-def]
            return [make_item("item-1")]

        def merge_cross_source_duplicates(self, items):  # type: ignore[no-untyped-def]
            return items

    monkeypatch.setattr(
        "src.mcp.service.HorizonOrchestrator",
        lambda config, storage, console, profiles: FakeOrchestrator(),
    )

    result = asyncio.run(service.fetch_items(hours=6))

    assert result["fetch_status"] == "partial_failure"
    assert result["fetch_report"]["failed"] == 1
    assert result["fetch_report"]["sources"][1]["source"] == "GitHub"
    assert result["meta"]["fetch_status"] == "partial_failure"
    assert service.run_store.load_meta(result["run_id"])["fetch_report"] == result["fetch_report"]


def test_filter_items_uses_public_filtering_pipeline_api(tmp_path: Path, monkeypatch) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    monkeypatch.setattr(service, "_profiles", lambda ctx: PROFILES)
    service.run_store.create_run("run-topic-dedup")

    monkeypatch.setattr(
        service,
        "_load_stage_items",
        lambda **kwargs: (
            [make_item("item-1", score=9.0), make_item("item-2", score=8.0)],
            SimpleNamespace(
                config_path=tmp_path / "config.json",
                config=SimpleNamespace(digest=SimpleNamespace()),
            ),
        ),
    )
    monkeypatch.setattr("src.mcp.service.make_storage", lambda config_path: object())

    class FakeOrchestrator:
        async def select_digest_items(self, items, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs == {"threshold": None, "topic_dedup": True, "log": False}
            kept = items[:1]
            return SimpleNamespace(
                items=kept,
                    threshold_count=2,
                    topic_dedup_count=1,
                    topic_dedup_removed=1,
                    eligible_count=None,
                    balanced_digest=BalancedDigestResult(items=kept),
            )

    monkeypatch.setattr(
        "src.mcp.service.HorizonOrchestrator",
        lambda config, storage, console, profiles: FakeOrchestrator(),
    )

    result = asyncio.run(service.filter_items(run_id="run-topic-dedup", topic_dedup=True))

    assert result["kept"] == 1
    assert result["removed_by_topic_dedup"] == 1
    assert service.run_store.load_items("run-topic-dedup", "filtered")[0]["id"] == "item-1"


def test_filter_items_applies_balanced_digest(tmp_path: Path, monkeypatch) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    monkeypatch.setattr(service, "_profiles", lambda ctx: PROFILES)
    service.run_store.create_run("run-balanced")
    filtering = SimpleNamespace(
        max_items=1,
        category_groups={},
    )

    monkeypatch.setattr(
        service,
        "_load_stage_items",
        lambda **kwargs: (
            [make_item("item-1", score=9.0), make_item("item-2", score=8.0)],
            SimpleNamespace(
                config_path=tmp_path / "config.json",
                config=SimpleNamespace(digest=filtering),
            ),
        ),
    )
    monkeypatch.setattr("src.mcp.service.make_storage", lambda config_path: object())

    class FakeOrchestrator:
        async def select_digest_items(self, items, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs == {"threshold": None, "topic_dedup": False, "log": False}
            kept = items[:1]
            return SimpleNamespace(
                items=kept,
                    threshold_count=2,
                    topic_dedup_count=2,
                    topic_dedup_removed=0,
                    eligible_count=None,
                    balanced_digest=BalancedDigestResult(
                    items=kept,
                    enabled=True,
                    group_counts={"other": 1},
                ),
            )

    monkeypatch.setattr(
        "src.mcp.service.HorizonOrchestrator",
        lambda config, storage, console, profiles: FakeOrchestrator(),
    )

    result = asyncio.run(
        service.filter_items(run_id="run-balanced", topic_dedup=False)
    )

    assert result["kept"] == 1
    assert result["removed_by_balanced_digest"] == 1
    assert result["balanced_digest_enabled"] is True
    assert result["group_counts"] == {"other": 1}


def test_filter_items_matches_native_filtering_pipeline(tmp_path: Path, monkeypatch) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    monkeypatch.setattr(service, "_profiles", lambda ctx: PROFILES)
    service.run_store.create_run("run-parity")
    filtering = DigestConfig(max_items=1)
    config = SimpleNamespace(
        digest=filtering,
        processing=ProcessingConfig(
            profile_settings={
                "tech-news": ProfileSettingsConfig(threshold=7.0)
            }
        ),
        sources=SimpleNamespace(twitter=None),
    )
    items = [
        make_item("mid", score=8.0),
        make_item("top", score=10.0),
        make_item("low", score=6.0),
        make_item("second", score=9.0),
    ]

    def make_filtering_orchestrator() -> HorizonOrchestrator:
        orchestrator = HorizonOrchestrator.__new__(HorizonOrchestrator)
        orchestrator.config = config
        orchestrator.profiles = PROFILES

        async def merge_topic_duplicates(input_items, *, log=True):  # type: ignore[no-untyped-def]
            assert log is False
            return input_items[::2]

        orchestrator.merge_topic_duplicates = merge_topic_duplicates  # type: ignore[method-assign]
        return orchestrator

    native_result = asyncio.run(
        make_filtering_orchestrator().select_digest_items(
            items, topic_dedup=True, log=False
        )
    )
    monkeypatch.setattr(
        service,
        "_load_stage_items",
        lambda **kwargs: (
            items,
            SimpleNamespace(
                config_path=tmp_path / "config.json",
                config=config,
            ),
        ),
    )
    monkeypatch.setattr("src.mcp.service.make_storage", lambda config_path: object())
    monkeypatch.setattr(
        "src.mcp.service.HorizonOrchestrator",
        lambda loaded_config, storage, console, profiles: make_filtering_orchestrator(),
    )

    mcp_result = asyncio.run(service.filter_items(run_id="run-parity"))

    assert [item.id for item in native_result.items] == ["top"]
    assert native_result.threshold_count == 3
    assert native_result.topic_dedup_count == 2
    assert native_result.topic_dedup_removed == 1
    assert mcp_result["kept"] == len(native_result.items)
    assert mcp_result["removed_by_topic_dedup"] == native_result.topic_dedup_removed
    assert mcp_result["removed_by_balanced_digest"] == (
        native_result.topic_dedup_count - len(native_result.items)
    )
    assert mcp_result["balanced_digest_enabled"] == native_result.balanced_digest.enabled
    assert mcp_result["group_counts"] == native_result.balanced_digest.group_counts
    assert [
        item["id"] for item in service.run_store.load_items("run-parity", "filtered")
    ] == [item.id for item in native_result.items]


def test_generate_summary_persists_informative_empty_summary(
    tmp_path: Path, monkeypatch
) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    profile_order = ["tech-news", "tech-blog", "finance-news"]
    received_orders = []

    class RecordingSummarizer(DailySummarizer):
        def __init__(self, *, profile_names=None, profile_order=None):  # type: ignore[no-untyped-def]
            received_orders.append(profile_order)
            super().__init__(
                profile_names=profile_names,
                profile_order=profile_order,
            )

    monkeypatch.setattr(service, "_profiles", lambda ctx: PROFILES)
    monkeypatch.setattr("src.mcp.service.DailySummarizer", RecordingSummarizer)
    service.run_store.create_run("run-empty")
    service.run_store.save_items("run-empty", "raw", [])
    service.run_store.save_items("run-empty", "filtered", [])

    monkeypatch.setattr(
        service,
        "_build_context",
        lambda **kwargs: (
            SimpleNamespace(
                config=SimpleNamespace(
                    digest=SimpleNamespace(profile_order=profile_order)
                ),
            ),
            [],
            [],
        ),
    )

    result = asyncio.run(
        service.generate_summary(
            run_id="run-empty", language="en", source_stage="filtered"
        )
    )

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expected = asyncio.run(
        DailySummarizer().generate_summary([], date_str, 0, language="en")
    )
    persisted = Path(result["summary_path"]).read_text(encoding="utf-8")

    assert result["items_used"] == 0
    assert received_orders == [profile_order]
    assert persisted == expected
    assert result["preview"] == expected[:1200]


def test_run_pipeline_skips_enrichment_when_filter_is_empty(
    tmp_path: Path, monkeypatch
) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    calls: list[tuple[str, str]] = []

    async def fetch_items(**kwargs):  # type: ignore[no-untyped-def]
        return {"run_id": "run-empty"}

    async def score_items(**kwargs):  # type: ignore[no-untyped-def]
        return {"scored": 1}

    async def filter_items(**kwargs):  # type: ignore[no-untyped-def]
        return {"kept": 0}

    async def enrich_items(**kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("enrichment must be skipped for empty filtered input")

    async def generate_summary(**kwargs):  # type: ignore[no-untyped-def]
        calls.append((kwargs["language"], kwargs["source_stage"]))
        return {"items_used": 0, "preview": ""}

    monkeypatch.setattr(service, "fetch_items", fetch_items)
    monkeypatch.setattr(service, "score_items", score_items)
    monkeypatch.setattr(service, "filter_items", filter_items)
    monkeypatch.setattr(service, "enrich_items", enrich_items)
    monkeypatch.setattr(service, "generate_summary", generate_summary)
    monkeypatch.setattr(
        service,
        "_build_context",
        lambda **kwargs: (
            SimpleNamespace(config=SimpleNamespace(ai=SimpleNamespace(languages=["en", "zh"]))),
            [],
            [],
        ),
    )
    monkeypatch.setattr(service.run_store, "load_meta", lambda run_id: {})

    result = asyncio.run(service.run_pipeline(enrich=True))

    assert result["enrich"] is None
    assert calls == [("en", "filtered"), ("zh", "filtered")]
    assert [summary["preview"] for summary in result["summaries"]] == ["", ""]


def test_run_pipeline_uses_filtered_stage_when_all_enrichment_fails(
    tmp_path: Path, monkeypatch
) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    calls: list[str] = []

    async def fetch_items(**kwargs):  # type: ignore[no-untyped-def]
        return {"run_id": "run-failed-enrichment"}

    async def score_items(**kwargs):  # type: ignore[no-untyped-def]
        return {"scored": 1}

    async def filter_items(**kwargs):  # type: ignore[no-untyped-def]
        return {"kept": 1}

    async def enrich_items(**kwargs):  # type: ignore[no-untyped-def]
        return {"status": "failure", "enriched": 0, "failed": 1}

    async def generate_summary(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs["source_stage"])
        return {"items_used": 1, "preview": "analysis-only"}

    monkeypatch.setattr(service, "fetch_items", fetch_items)
    monkeypatch.setattr(service, "score_items", score_items)
    monkeypatch.setattr(service, "filter_items", filter_items)
    monkeypatch.setattr(service, "enrich_items", enrich_items)
    monkeypatch.setattr(service, "generate_summary", generate_summary)
    monkeypatch.setattr(
        service,
        "_build_context",
        lambda **kwargs: (
            SimpleNamespace(config=SimpleNamespace(ai=SimpleNamespace(languages=["zh"]))),
            [],
            [],
        ),
    )
    monkeypatch.setattr(service.run_store, "load_meta", lambda run_id: {})

    result = asyncio.run(service.run_pipeline())

    assert calls == ["filtered"]
    assert result["enrich"]["status"] == "failure"


def test_enrich_items_propagates_batch_failure(tmp_path: Path, monkeypatch) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    item = make_item("failed", score=9.0)

    class FailingOrchestrator:
        async def enrich_items(self, items) -> None:  # type: ignore[no-untyped-def]
            raise RuntimeError("enrichment failed")

    ctx = SimpleNamespace(
        config=SimpleNamespace(ai=SimpleNamespace(languages=["en"])),
    )
    monkeypatch.setattr(service, "_load_stage_items", lambda **kwargs: ([item], ctx))
    monkeypatch.setattr(service, "_orchestrator", lambda loaded_ctx: FailingOrchestrator())

    with pytest.raises(RuntimeError, match="enrichment failed"):
        asyncio.run(service.enrich_items("run-failed"))


def test_enrich_items_reports_partial_failure_truthfully(
    tmp_path: Path, monkeypatch
) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    service.run_store.create_run("run-partial")
    successful_item = make_item("successful", score=9.0)
    failed_item = make_item("failed", score=8.0)

    class PartiallyFailingOrchestrator:
        async def enrich_items(self, items):  # type: ignore[no-untyped-def]
            return EnrichmentBatchResult(
                succeeded_ids=[successful_item.id],
                failures={failed_item.id: "ValueError: empty story"},
            )

    ctx = SimpleNamespace(
        config=SimpleNamespace(ai=SimpleNamespace(languages=["en"])),
    )
    monkeypatch.setattr(
        service,
        "_load_stage_items",
        lambda **kwargs: ([successful_item, failed_item], ctx),
    )
    monkeypatch.setattr(
        service,
        "_orchestrator",
        lambda loaded_ctx: PartiallyFailingOrchestrator(),
    )

    result = asyncio.run(service.enrich_items("run-partial"))

    assert result["status"] == "partial_failure"
    assert result["enriched"] == 1
    assert result["failed"] == 1
    assert result["failed_ids"] == [failed_item.id]
    assert result["meta"]["enrichment_status"] == "partial_failure"
    assert result["meta"]["enriched_count"] == 1
    assert len(service.run_store.load_items("run-partial", "enriched")) == 2


def test_enrich_items_does_not_create_stage_when_all_items_fail(
    tmp_path: Path, monkeypatch
) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    service.run_store.create_run("run-all-failed")
    item = make_item("failed", score=8.0)

    class FailingOrchestrator:
        async def enrich_items(self, items):  # type: ignore[no-untyped-def]
            return EnrichmentBatchResult(
                failures={item.id: "ValueError: empty story"}
            )

    ctx = SimpleNamespace(config=SimpleNamespace())
    monkeypatch.setattr(service, "_load_stage_items", lambda **kwargs: ([item], ctx))
    monkeypatch.setattr(service, "_orchestrator", lambda loaded_ctx: FailingOrchestrator())

    result = asyncio.run(service.enrich_items("run-all-failed"))

    assert result["status"] == "failure"
    assert result["artifact"] is None
    assert service.run_store.has_stage("run-all-failed", "enriched") is False


def test_send_webhook_reports_delivery_failure_truthfully(
    tmp_path: Path, monkeypatch
) -> None:
    service = HorizonPipelineService(runs_root=tmp_path / "mcp-runs")
    webhook_config = SimpleNamespace(enabled=True)
    monkeypatch.setattr(
        service,
        "_build_context",
        lambda **kwargs: (
            SimpleNamespace(config=SimpleNamespace(webhook=webhook_config)),
            [],
            [],
        ),
    )

    class FakeNotifier:
        def __init__(self, config, console) -> None:  # type: ignore[no-untyped-def]
            assert config is webhook_config
            assert console is service.console

        async def notify(self, variables):  # type: ignore[no-untyped-def]
            return WebhookDeliveryResult(
                WebhookDeliveryStatus.PLATFORM_FAILURE,
                status_code=200,
                detail="platform rejected payload",
            )

    monkeypatch.setattr("src.mcp.service.WebhookNotifier", FakeNotifier)

    result = asyncio.run(service.send_webhook(date="2026-04-24", summary="digest"))

    assert result["sent"] is False
    assert result["status"] == "platform_failure"
    assert result["status_code"] == 200
