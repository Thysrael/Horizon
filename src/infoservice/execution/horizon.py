"""InfoService adapter for Horizon's reusable execution pipeline."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from src.infoservice.sources.catalog import SourceCatalog
from src.models import AIConfig, Config, FilteringConfig, SourcesConfig
from src.orchestrator import HorizonOrchestrator
from src.storage.manager import StorageManager

from .contracts import ReportExecutionRequest, ReportExecutionResult


class HorizonReportExecutor:
    """Execute one InfoService report without Horizon's delivery side effects."""

    def __init__(self, settings: Any | None = None, credential: Any | None = None, *, model: str | None = None, storage: Any | None = None) -> None:
        self._settings = settings or type("Capabilities", (), {"enable_twitter": False, "enable_openbb": False})()
        self._credential = credential
        self._model = model
        self._storage = storage

    async def execute(self, request: ReportExecutionRequest) -> ReportExecutionResult:
        runtime_api_key = request.api_key
        temporary_storage: TemporaryDirectory[str] | None = None
        try:
            config = self._build_config(request.config)
            storage = self._storage
            if storage is None:
                temporary_storage = TemporaryDirectory(prefix="infoservice-horizon-")
                storage = StorageManager(temporary_storage.name)
            orchestrator = HorizonOrchestrator(config, storage, runtime_api_key=runtime_api_key)
            result = await orchestrator.execute(
                force_hours=request.lookback_hours,
                custom_instruction=request.custom_instruction,
            )
            language = config.ai.languages[0]
            return ReportExecutionResult(
                markdown=result.summaries[language],
                items=[item.model_copy(deep=True) for item in result.important_items],
                all_items_count=result.all_items_count,
                fetch_report=result.fetch_report.to_dict() if hasattr(result.fetch_report, "to_dict") else result.fetch_report,
                usage=result.usage,
            )
        finally:
            runtime_api_key = ""
            if temporary_storage is not None:
                temporary_storage.cleanup()

    def _build_config(self, report: Any) -> Config:
        sources = self._build_sources(getattr(report, "sources", []))
        model = self._model or getattr(self._credential, "model", None) or getattr(report, "model", None) or "deepseek-v4-flash"
        exclusions = list(getattr(report, "exclusions", []) or [])
        return Config(
            ai=AIConfig(provider="deepseek", model=model, api_key_env="", languages=[getattr(report, "language", "en")]),
            sources=sources,
            filtering=FilteringConfig(
                ai_score_threshold=getattr(report, "ai_score_threshold", 7.0),
                time_window_hours=getattr(report, "lookback_hours", 24),
                max_items=getattr(report, "max_items", 10),
            ),
            email=None,
            webhook=None,
        )

    def _build_sources(self, records: Any) -> SourcesConfig:
        grouped: dict[str, list[Any]] = defaultdict(list)
        for source in records:
            if not getattr(source, "enabled", True):
                continue
            grouped[source.source_type].append(SourceCatalog.validate(source.source_type, source.config, self._settings))

        payload: dict[str, Any] = {}
        if grouped.get("github"):
            payload["github"] = grouped["github"]
        if grouped.get("rss"):
            payload["rss"] = grouped["rss"]
        if grouped.get("hackernews"):
            payload["hackernews"] = grouped["hackernews"][-1]
        if grouped.get("telegram"):
            payload["telegram"] = {"enabled": True, "channels": grouped["telegram"]}
        if grouped.get("reddit"):
            payload["reddit"] = {
                "enabled": True,
                "subreddits": [item for item in grouped["reddit"] if hasattr(item, "subreddit")],
                "users": [item for item in grouped["reddit"] if hasattr(item, "username")],
            }
        for source_type in ("google_news", "gdelt", "ossinsight", "twitter"):
            if grouped.get(source_type):
                payload[source_type] = grouped[source_type][-1]
        if grouped.get("openbb"):
            watchlists = [watchlist for item in grouped["openbb"] for watchlist in item.watchlists]
            payload["openbb"] = {"enabled": True, "watchlists": watchlists}
        return SourcesConfig.model_validate(payload)
