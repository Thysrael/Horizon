"""InfoService adapter for Horizon's reusable execution pipeline."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable

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
            config = self._build_config(request.config, request.model)
            storage = self._storage
            if storage is None:
                temporary_storage = TemporaryDirectory(prefix="infoservice-horizon-")
                storage = StorageManager(temporary_storage.name)
            orchestrator = HorizonOrchestrator(config, storage, runtime_api_key=runtime_api_key)
            execute_kwargs: dict[str, Any] = {
                "force_hours": request.lookback_hours,
                "custom_instruction": request.custom_instruction,
            }
            item_filter = self._build_item_filter(request.config)
            if item_filter is not None:
                execute_kwargs["item_filter"] = item_filter
            result = await orchestrator.execute(**execute_kwargs)
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

    def _build_config(self, report: Any, request_model: str | None = None) -> Config:
        sources = self._build_sources(getattr(report, "sources", []))
        model = self._model or request_model or getattr(self._credential, "model", None) or getattr(report, "model", None) or "deepseek-v4-flash"
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

    @staticmethod
    def _build_item_filter(report: Any) -> Callable[[Any], bool] | None:
        """Build InfoService-only category and topic exclusion rules.

        Horizon's legacy configuration has no report-level categories or
        exclusions.  Keep these rules at the adapter boundary so its CLI and
        webhook execution remain unchanged.
        """
        categories = {
            value.strip().casefold()
            for value in getattr(report, "categories", []) or []
            if isinstance(value, str) and value.strip()
        }
        exclusions = {
            value.strip().casefold()
            for value in getattr(report, "exclusions", []) or []
            if isinstance(value, str) and value.strip()
        }
        if not categories and not exclusions:
            return None

        def includes(item: Any) -> bool:
            metadata = getattr(item, "metadata", {}) or {}
            category_value = metadata.get("category")
            category = (
                category_value.strip().casefold()
                if isinstance(category_value, str)
                else ""
            )
            if categories and category not in categories:
                return False
            if category in exclusions:
                return False

            searchable = " ".join(
                str(value)
                for value in (
                    getattr(item, "title", ""),
                    getattr(item, "content", ""),
                    getattr(item, "ai_summary", ""),
                    getattr(item, "ai_reason", ""),
                    *getattr(item, "ai_tags", []),
                )
                if value
            ).casefold()
            return not any(exclusion in searchable for exclusion in exclusions)

        return includes

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
