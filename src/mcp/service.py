"""Application service for staged Horizon pipeline execution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .errors import HorizonMcpError
from .horizon_adapter import (
    apply_source_filter,
    dicts_to_items,
    get_enabled_sources,
    get_source_counts,
    items_to_dicts,
    load_config,
    load_runtime,
    make_orchestrator,
    make_storage,
    resolve_config_path,
    resolve_horizon_path,
)
from .run_store import RunStore
from ..services.webhook import WebhookNotifier


def _default_runs_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "mcp-runs"


@dataclass
class PipelineContext:
    """Resolved execution context per call."""

    horizon_path: Path
    config_path: Path
    runtime: Any
    config: Any


class HorizonPipelineService:
    """High-level staged pipeline service."""

    def __init__(self, runs_root: Path | None = None):
        self.runs_root = Path(runs_root).resolve() if runs_root else _default_runs_root().resolve()
        self._run_store: RunStore | None = None

    @property
    def run_store(self) -> RunStore:
        if self._run_store is None:
            self._run_store = RunStore(self.runs_root)
        return self._run_store

    def list_runs(self, limit: int = 20) -> dict[str, Any]:
        """List recent runs and stage availability."""

        runs = self.run_store.list_runs(limit=limit)
        items = []
        for run in runs:
            run_id = run["run_id"]
            stages = {}
            for stage in ("raw", "scored", "filtered", "enriched"):
                stages[stage] = self.run_store.has_stage(run_id, stage)
            items.append(
                {
                    "run_id": run_id,
                    "created_at": run.get("created_at"),
                    "updated_at": run.get("updated_at"),
                    "stages": stages,
                    "meta": run.get("meta", {}),
                }
            )
        return {"count": len(items), "items": items}

    def get_run_meta(self, run_id: str) -> dict[str, Any]:
        """Read run metadata."""

        try:
            meta = self.run_store.load_meta(run_id)
        except FileNotFoundError as exc:
            raise HorizonMcpError(
                code="HZ_RUN_NOT_FOUND",
                message=f"run_id={run_id} does not exist.",
                details={"run_id": run_id},
            ) from exc
        return {"run_id": run_id, "meta": meta}

    def get_run_stage(
        self,
        run_id: str,
        stage: str,
        max_items: int = 200,
    ) -> dict[str, Any]:
        """Read staged item payload (JSON)."""

        if max_items <= 0:
            raise HorizonMcpError(code="HZ_INVALID_INPUT", message="max_items must be greater than 0.")
        try:
            items = self.run_store.load_items(run_id, stage)
        except ValueError as exc:
            raise HorizonMcpError(
                code="HZ_INVALID_STAGE",
                message=str(exc),
                details={"stage": stage},
            ) from exc
        except FileNotFoundError as exc:
            raise HorizonMcpError(
                code="HZ_STAGE_NOT_FOUND",
                message=f"run_id={run_id} is missing stage artifact: {stage}",
                details={"run_id": run_id, "stage": stage},
            ) from exc

        return {
            "run_id": run_id,
            "stage": stage,
            "count": len(items),
            "items": items[:max_items],
            "truncated": len(items) > max_items,
        }

    def get_run_summary(self, run_id: str, language: str = "zh") -> dict[str, Any]:
        """Read generated markdown summary for a run."""

        try:
            markdown = self.run_store.load_summary(run_id, language)
        except FileNotFoundError as exc:
            raise HorizonMcpError(
                code="HZ_SUMMARY_NOT_FOUND",
                message=f"run_id={run_id} is missing summary for language={language}.",
                details={"run_id": run_id, "language": language},
            ) from exc
        return {
            "run_id": run_id,
            "language": language,
            "summary": markdown,
        }

    def get_effective_config(
        self,
        horizon_path: str | None = None,
        config_path: str | None = None,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return effective config after optional source filtering."""

        ctx, selected_sources, unknown_sources = self._build_context(
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
        )
        return {
            "horizon_path": str(ctx.horizon_path),
            "config_path": str(ctx.config_path),
            "selected_sources": selected_sources,
            "unknown_sources": unknown_sources,
            "config": ctx.config.model_dump(mode="json"),
        }

    async def validate_config(
        self,
        horizon_path: str | None = None,
        config_path: str | None = None,
        sources: list[str] | None = None,
        check_env: bool = True,
    ) -> dict[str, Any]:
        ctx, selected_sources, unknown_sources = self._build_context(
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
        )

        warnings: list[str] = []
        missing_env: list[str] = []

        if check_env:
            required = [ctx.config.ai.api_key_env]
            for key in required:
                if not os.getenv(key):
                    missing_env.append(key)

            if ctx.config.sources.github and not os.getenv("GITHUB_TOKEN"):
                warnings.append("GITHUB_TOKEN is not set; GitHub fetching may hit strict rate limits.")

            if getattr(ctx.config, "email", None) and ctx.config.email and ctx.config.email.enabled:
                pwd_key = ctx.config.email.password_env
                if not os.getenv(pwd_key):
                    missing_env.append(pwd_key)

            if getattr(ctx.config, "webhook", None) and ctx.config.webhook and ctx.config.webhook.enabled:
                if ctx.config.webhook.url_env and not os.getenv(ctx.config.webhook.url_env):
                    missing_env.append(ctx.config.webhook.url_env)

        return {
            "horizon_path": str(ctx.horizon_path),
            "config_path": str(ctx.config_path),
            "ai": {
                "provider": ctx.config.ai.provider.value,
                "model": ctx.config.ai.model,
                "languages": list(ctx.config.ai.languages),
                "api_key_env": ctx.config.ai.api_key_env,
            },
            "filtering": {
                "ai_score_threshold": ctx.config.filtering.ai_score_threshold,
                "time_window_hours": ctx.config.filtering.time_window_hours,
                "max_items": ctx.config.filtering.max_items,
                "category_groups": {
                    key: group.model_dump(mode="json")
                    for key, group in ctx.config.filtering.category_groups.items()
                },
                "default_group": ctx.config.filtering.default_group,
                "default_group_limit": ctx.config.filtering.default_group_limit,
            },
            "enabled_sources": get_enabled_sources(ctx.config),
            "selected_sources": selected_sources,
            "unknown_sources": unknown_sources,
            "missing_env": missing_env,
            "warnings": warnings,
        }

    async def fetch_items(
        self,
        hours: int = 24,
        run_id: str | None = None,
        horizon_path: str | None = None,
        config_path: str | None = None,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        if hours <= 0:
            raise HorizonMcpError(code="HZ_INVALID_INPUT", message="hours must be greater than 0.")

        ctx, selected_sources, unknown_sources = self._build_context(
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
        )

        storage = make_storage(ctx.runtime, ctx.config_path)
        orchestrator = make_orchestrator(ctx.runtime, ctx.config, storage)

        run_id = self.run_store.create_run(run_id)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        raw_items = await orchestrator.fetch_all_sources(since)
        merged_items = orchestrator.merge_cross_source_duplicates(raw_items)

        self.run_store.save_items(run_id, "raw", items_to_dicts(merged_items))
        meta = self.run_store.update_meta(
            run_id,
            {
                "horizon_path": str(ctx.horizon_path),
                "config_path": str(ctx.config_path),
                "hours": hours,
                "since": since.isoformat(),
                "source_selection": selected_sources,
                "unknown_sources": unknown_sources,
                "raw_count_before_merge": len(raw_items),
                "raw_count": len(merged_items),
            },
        )

        return {
            "run_id": run_id,
            "fetched": len(merged_items),
            "raw_before_merge": len(raw_items),
            "source_counts": get_source_counts(merged_items),
            "artifact": str((self.run_store.run_dir(run_id) / "raw_items.json").resolve()),
            "meta": meta,
        }

    async def score_items(
        self,
        run_id: str,
        source_stage: str = "raw",
        horizon_path: str | None = None,
        config_path: str | None = None,
    ) -> dict[str, Any]:
        items, ctx = self._load_stage_items(
            run_id=run_id,
            stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
        )

        if not items:
            raise HorizonMcpError(code="HZ_EMPTY_INPUT", message="No items available for scoring.")

        ai_client = ctx.runtime.create_ai_client(ctx.config.ai)
        analyzer = ctx.runtime.ContentAnalyzer(ai_client)
        scored_items = await analyzer.analyze_batch(items)

        self.run_store.save_items(run_id, "scored", items_to_dicts(scored_items))
        score_threshold = ctx.config.filtering.ai_score_threshold
        above_threshold = [x for x in scored_items if x.ai_score and x.ai_score >= score_threshold]

        meta = self.run_store.update_meta(
            run_id,
            {
                "scored_count": len(scored_items),
                "scored_threshold": score_threshold,
                "scored_above_threshold": len(above_threshold),
            },
        )

        return {
            "run_id": run_id,
            "scored": len(scored_items),
            "above_threshold": len(above_threshold),
            "score_distribution": self._score_distribution(scored_items),
            "artifact": str((self.run_store.run_dir(run_id) / "scored_items.json").resolve()),
            "meta": meta,
        }

    async def filter_items(
        self,
        run_id: str,
        threshold: float | None = None,
        source_stage: str = "scored",
        topic_dedup: bool = True,
        horizon_path: str | None = None,
        config_path: str | None = None,
    ) -> dict[str, Any]:
        items, ctx = self._load_stage_items(
            run_id=run_id,
            stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
        )

        effective_threshold = threshold if threshold is not None else ctx.config.filtering.ai_score_threshold

        important_items = [item for item in items if item.ai_score and item.ai_score >= effective_threshold]
        important_items.sort(key=lambda x: x.ai_score or 0, reverse=True)

        before_dedup = len(important_items)
        orchestrator = None
        if topic_dedup and important_items:
            storage = make_storage(ctx.runtime, ctx.config_path)
            orchestrator = make_orchestrator(ctx.runtime, ctx.config, storage)
            important_items = await orchestrator.merge_topic_duplicates(important_items)
        after_dedup = len(important_items)

        filtering = ctx.config.filtering
        balanced_enabled = bool(
            getattr(filtering, "category_groups", {})
            or getattr(filtering, "max_items", None) is not None
        )
        balanced_group_counts: dict[str, int] = {}
        if balanced_enabled:
            if orchestrator is None:
                storage = make_storage(ctx.runtime, ctx.config_path)
                orchestrator = make_orchestrator(ctx.runtime, ctx.config, storage)
            balanced_result = orchestrator.apply_balanced_digest(
                important_items,
                log=False,
            )
            important_items = balanced_result.items
            balanced_group_counts = balanced_result.group_counts

        self.run_store.save_items(run_id, "filtered", items_to_dicts(important_items))
        meta = self.run_store.update_meta(
            run_id,
            {
                "filtered_count": len(important_items),
                "filter_threshold": effective_threshold,
                "topic_dedup_enabled": topic_dedup,
                "topic_dedup_removed": before_dedup - after_dedup,
                "balanced_digest_enabled": balanced_enabled,
                "balanced_digest_group_counts": balanced_group_counts,
                "balanced_digest_removed": after_dedup - len(important_items),
            },
        )

        return {
            "run_id": run_id,
            "kept": len(important_items),
            "threshold": effective_threshold,
            "removed_by_topic_dedup": before_dedup - after_dedup,
            "removed_by_balanced_digest": after_dedup - len(important_items),
            "balanced_digest_enabled": balanced_enabled,
            "group_counts": balanced_group_counts,
            "source_counts": get_source_counts(important_items),
            "artifact": str((self.run_store.run_dir(run_id) / "filtered_items.json").resolve()),
            "meta": meta,
        }

    async def enrich_items(
        self,
        run_id: str,
        source_stage: str = "filtered",
        horizon_path: str | None = None,
        config_path: str | None = None,
    ) -> dict[str, Any]:
        items, ctx = self._load_stage_items(
            run_id=run_id,
            stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
        )

        if not items:
            raise HorizonMcpError(code="HZ_EMPTY_INPUT", message="No items available for enrichment.")

        ai_client = ctx.runtime.create_ai_client(ctx.config.ai)
        enricher = ctx.runtime.ContentEnricher(ai_client)
        await enricher.enrich_batch(items)

        self.run_store.save_items(run_id, "enriched", items_to_dicts(items))

        citation_count = 0
        for item in items:
            citation_count += len(item.metadata.get("sources", []))

        meta = self.run_store.update_meta(
            run_id,
            {
                "enriched_count": len(items),
                "citation_count": citation_count,
            },
        )

        return {
            "run_id": run_id,
            "enriched": len(items),
            "citation_count": citation_count,
            "artifact": str((self.run_store.run_dir(run_id) / "enriched_items.json").resolve()),
            "meta": meta,
        }

    async def generate_summary(
        self,
        run_id: str,
        language: str = "zh",
        source_stage: str | None = None,
        horizon_path: str | None = None,
        config_path: str | None = None,
        save_to_horizon_data: bool = False,
    ) -> dict[str, Any]:
        stage = source_stage or self._pick_summary_stage(run_id)
        items, ctx = self._load_stage_items(
            run_id=run_id,
            stage=stage,
            horizon_path=horizon_path,
            config_path=config_path,
        )

        total_fetched = self._total_fetched(run_id, fallback=len(items))
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        summarizer = ctx.runtime.DailySummarizer()
        summary = await summarizer.generate_summary(
            items,
            date_str,
            total_fetched,
            language=language,
        )

        run_summary_path = self.run_store.save_summary(run_id, language, summary)
        published_path = None
        if save_to_horizon_data:
            storage = make_storage(ctx.runtime, ctx.config_path)
            published_path = storage.save_daily_summary(date_str, summary, language=language)

        summary_meta = {
            "summary_stage": stage,
            "summary_language": language,
            "summary_generated_at": datetime.now(timezone.utc).isoformat(),
            "summary_artifact": str(run_summary_path.resolve()),
        }
        if published_path:
            summary_meta["summary_published_path"] = str(Path(published_path).resolve())
        meta = self.run_store.update_meta(run_id, summary_meta)

        return {
            "run_id": run_id,
            "language": language,
            "source_stage": stage,
            "total_fetched": total_fetched,
            "items_used": len(items),
            "summary_path": str(run_summary_path.resolve()),
            "published_path": str(Path(published_path).resolve()) if published_path else None,
            "preview": summary[:1200],
            "meta": meta,
        }

    async def run_pipeline(
        self,
        hours: int = 24,
        languages: list[str] | None = None,
        threshold: float | None = None,
        horizon_path: str | None = None,
        config_path: str | None = None,
        sources: list[str] | None = None,
        enrich: bool = True,
        topic_dedup: bool = True,
        save_to_horizon_data: bool = False,
    ) -> dict[str, Any]:
        fetch_result = await self.fetch_items(
            hours=hours,
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
        )
        run_id = fetch_result["run_id"]

        score_result = await self.score_items(
            run_id=run_id,
            horizon_path=horizon_path,
            config_path=config_path,
        )

        filter_result = await self.filter_items(
            run_id=run_id,
            threshold=threshold,
            topic_dedup=topic_dedup,
            horizon_path=horizon_path,
            config_path=config_path,
        )

        enrich_result: dict[str, Any] | None = None
        stage_for_summary = "filtered"
        if enrich:
            enrich_result = await self.enrich_items(
                run_id=run_id,
                source_stage="filtered",
                horizon_path=horizon_path,
                config_path=config_path,
            )
            stage_for_summary = "enriched"

        ctx, _, _ = self._build_context(
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
        )
        final_languages = languages if languages else list(ctx.config.ai.languages)

        summaries = []
        for lang in final_languages:
            summary_result = await self.generate_summary(
                run_id=run_id,
                language=lang,
                source_stage=stage_for_summary,
                horizon_path=horizon_path,
                config_path=config_path,
                save_to_horizon_data=save_to_horizon_data,
            )
            summaries.append(summary_result)

        return {
            "run_id": run_id,
            "fetch": fetch_result,
            "score": score_result,
            "filter": filter_result,
            "enrich": enrich_result,
            "summaries": summaries,
            "meta": self.run_store.load_meta(run_id),
        }

    def _build_context(
        self,
        horizon_path: str | None,
        config_path: str | None,
        sources: list[str] | None,
    ) -> tuple[PipelineContext, list[str], list[str]]:
        resolved_horizon = resolve_horizon_path(horizon_path)
        runtime = load_runtime(resolved_horizon)
        resolved_config = resolve_config_path(resolved_horizon, config_path)
        config = load_config(runtime, resolved_config)
        effective_config, selected_sources, unknown_sources = apply_source_filter(config, sources)

        return (
            PipelineContext(
                horizon_path=resolved_horizon,
                config_path=resolved_config,
                runtime=runtime,
                config=effective_config,
            ),
            selected_sources,
            unknown_sources,
        )

    def _load_stage_items(
        self,
        run_id: str,
        stage: str,
        horizon_path: str | None,
        config_path: str | None,
    ) -> tuple[list[Any], PipelineContext]:
        ctx, _, _ = self._build_context(horizon_path=horizon_path, config_path=config_path, sources=None)
        try:
            payload = self.run_store.load_items(run_id, stage)
        except FileNotFoundError as exc:
            raise HorizonMcpError(
                code="HZ_STAGE_NOT_FOUND",
                message=f"run_id={run_id} is missing stage artifact: {stage}",
                details={"run_id": run_id, "stage": stage},
            ) from exc
        items = dicts_to_items(ctx.runtime, payload)
        return items, ctx

    def _pick_summary_stage(self, run_id: str) -> str:
        for stage in ("enriched", "filtered", "scored", "raw"):
            if self.run_store.has_stage(run_id, stage):
                return stage
        raise HorizonMcpError(
            code="HZ_STAGE_NOT_FOUND",
            message=f"run_id={run_id} has no usable stage for summary generation.",
            details={"run_id": run_id},
        )

    def _total_fetched(self, run_id: str, fallback: int) -> int:
        try:
            raw = self.run_store.load_items(run_id, "raw")
            return len(raw)
        except Exception:
            return fallback

    @staticmethod
    def _score_distribution(items: list[Any]) -> dict[str, int]:
        buckets = {"0-2": 0, "3-4": 0, "5-6": 0, "7-8": 0, "9-10": 0}
        for item in items:
            score = float(item.ai_score or 0.0)
            if score < 3:
                buckets["0-2"] += 1
            elif score < 5:
                buckets["3-4"] += 1
            elif score < 7:
                buckets["5-6"] += 1
            elif score < 9:
                buckets["7-8"] += 1
            else:
                buckets["9-10"] += 1
        return buckets

    async def send_webhook(
        self,
        date: str,
        language: str = "zh",
        important_items: int = 0,
        all_items: int = 0,
        result: str = "success",
        summary: str = "",
        horizon_path: str | None = None,
        config_path: str | None = None,
    ) -> dict[str, Any]:
        """Send a webhook notification using the configured webhook settings."""

        ctx, _, _ = self._build_context(
            horizon_path=horizon_path,
            config_path=config_path,
            sources=None,
        )

        webhook_config = ctx.config.webhook
        if not webhook_config or not webhook_config.enabled:
            return {
                "sent": False,
                "reason": "Webhook is not enabled in configuration.",
            }

        notifier = WebhookNotifier(webhook_config)
        variables = {
            "date": date,
            "language": language,
            "important_items": important_items,
            "all_items": all_items,
            "result": result,
            "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
            "message_title": f"Horizon {date} webhook",
            "message_kind": "manual",
            "summary": summary,
        }

        await notifier.notify(variables)

        return {
            "sent": True,
            "variables": {k: (v if k != "summary" else f"<{len(v)} chars>") for k, v in variables.items()},
        }
