"""Application service for staged Horizon pipeline execution."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from rich.console import Console

from ..ai.summarizer import DailySummarizer
from ..models import Config, ContentItem
from ..orchestrator import HorizonOrchestrator
from ..processing import ProfileRegistry
from .errors import HorizonMcpError
from .horizon_adapter import (
    apply_source_filter,
    dicts_to_items,
    get_enabled_sources,
    get_source_counts,
    items_to_dicts,
    load_config,
    load_environment,
    make_storage,
    resolve_config_path,
    resolve_horizon_path,
)
from .run_store import RunStore
from ..services.webhook import WebhookNotifier


_REDACTED = "<redacted>"
_SENSITIVE_NAME = re.compile(
    r"(?:^|[-_])(authorization|cookie|credential|key|password|secret|signature|token|api[-_]?key)(?:$|[-_])",
    re.IGNORECASE,
)


def _redact_config(value: Any, key: str = "") -> Any:
    """Redact secrets from expanded config while preserving its structure."""
    if key.lower().endswith("_env"):
        return value
    if _SENSITIVE_NAME.search(key):
        return _REDACTED
    if isinstance(value, dict):
        return {item_key: _redact_config(item, str(item_key)) for item_key, item in value.items()}
    if isinstance(value, list):
        return [_redact_config(item) for item in value]
    if not isinstance(value, str):
        return value

    lines = value.splitlines()
    if any(":" in line for line in lines):
        redacted_lines = []
        for line in lines:
            name, separator, header_value = line.partition(":")
            if separator and _SENSITIVE_NAME.search(name.strip()):
                line = f"{name}:{' ' if header_value.startswith(' ') else ''}{_REDACTED}"
            redacted_lines.append(line)
        value = "\n".join(redacted_lines)

    try:
        parts = urlsplit(value)
        if parts.scheme in {"http", "https"} and parts.netloc:
            netloc = parts.netloc
            if parts.username is not None or parts.password is not None:
                netloc = f"{_REDACTED}@{parts.hostname or ''}"
                if parts.port is not None:
                    netloc += f":{parts.port}"
            query = [
                (name, _REDACTED if _SENSITIVE_NAME.search(name) else item_value)
                for name, item_value in parse_qsl(parts.query, keep_blank_values=True)
            ]
            value = urlunsplit(parts._replace(netloc=netloc, query=urlencode(query)))
    except ValueError:
        pass
    return value


def _default_runs_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "mcp-runs"


@dataclass
class PipelineContext:
    """Resolved execution context per call."""

    horizon_path: Path
    config_path: Path
    config: Config


class HorizonPipelineService:
    """High-level staged pipeline service."""

    def __init__(
        self,
        runs_root: Path | None = None,
        console: Console | None = None,
    ):
        self.runs_root = Path(runs_root).resolve() if runs_root else _default_runs_root().resolve()
        self.console = console or Console(stderr=True)
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
            "config": _redact_config(ctx.config.model_dump(mode="json")),
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

        try:
            self._profiles(ctx).validate_digest_references(ctx.config.digest)
        except ValueError as exc:
            raise HorizonMcpError(
                code="HZ_CONFIG_INVALID",
                message="Config references unknown processing profiles.",
                details={"config_path": str(ctx.config_path), "error": str(exc)},
            ) from exc

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
            "collection": {
                "time_window_hours": ctx.config.collection.time_window_hours,
            },
            "digest": {
                "max_items": ctx.config.digest.max_items,
                "profile_order": list(ctx.config.digest.profile_order),
                "category_groups": {
                    key: group.model_dump(mode="json")
                    for key, group in ctx.config.digest.category_groups.items()
                },
                "group_by": ctx.config.digest.group_by,
                "default_group": ctx.config.digest.default_group,
                "default_group_limit": ctx.config.digest.default_group_limit,
            },
            "enabled_sources": get_enabled_sources(ctx.config),
            "processing": {
                "profiles_dir": ctx.config.processing.profiles_dir,
                "default_profile": ctx.config.processing.default_profile,
            },
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

        orchestrator = self._orchestrator(ctx)

        run_id = self.run_store.create_run(run_id)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        raw_items = await orchestrator.fetch_all_sources(since)
        merged_items = orchestrator.merge_cross_source_duplicates(raw_items)
        report = orchestrator.last_fetch_report
        fetch_report = report.to_dict() if report is not None else None

        self.run_store.save_items(run_id, "raw", items_to_dicts(merged_items))
        meta_updates = {
            "horizon_path": str(ctx.horizon_path),
            "config_path": str(ctx.config_path),
            "hours": hours,
            "since": since.isoformat(),
            "source_selection": selected_sources,
            "unknown_sources": unknown_sources,
            "raw_count_before_merge": len(raw_items),
            "raw_count": len(merged_items),
        }
        if fetch_report is not None:
            meta_updates["fetch_status"] = fetch_report.get("status")
            meta_updates["fetch_report"] = fetch_report
        meta = self.run_store.update_meta(run_id, meta_updates)

        response = {
            "run_id": run_id,
            "fetched": len(merged_items),
            "raw_before_merge": len(raw_items),
            "source_counts": get_source_counts(merged_items),
            "artifact": str((self.run_store.run_dir(run_id) / "raw_items.json").resolve()),
            "meta": meta,
        }
        if fetch_report is not None:
            response["fetch_status"] = fetch_report.get("status")
            response["fetch_report"] = fetch_report
        return response

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

        orchestrator = self._orchestrator(ctx)
        scored_items = await orchestrator.analyze_items(items)

        self.run_store.save_items(run_id, "scored", items_to_dicts(scored_items))
        selected = [
            item for item in scored_items if orchestrator.passes_profile_filter(item)
        ]

        meta = self.run_store.update_meta(
            run_id,
            {
                "scored_count": len(scored_items),
                "selected_count": len(selected),
            },
        )

        return {
            "run_id": run_id,
            "scored": len(scored_items),
            "selected": len(selected),
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

        orchestrator = self._orchestrator(ctx)
        filtering_result = await orchestrator.select_digest_items(
            items,
            threshold=threshold,
            topic_dedup=topic_dedup,
            log=False,
        )
        important_items = filtering_result.items
        balanced_result = filtering_result.balanced_digest
        balanced_enabled = balanced_result.enabled
        balanced_group_counts = balanced_result.group_counts
        eligible_count = (
            filtering_result.eligible_count
            if filtering_result.eligible_count is not None
            else filtering_result.topic_dedup_count
        )

        self.run_store.save_items(run_id, "filtered", items_to_dicts(important_items))
        meta = self.run_store.update_meta(
            run_id,
            {
                "filtered_count": len(important_items),
                "filter_threshold_override": threshold,
                "topic_dedup_enabled": topic_dedup,
                "topic_dedup_removed": filtering_result.topic_dedup_removed,
                "reanalysis_filtered_count": (
                    filtering_result.topic_dedup_count - eligible_count
                ),
                "balanced_digest_enabled": balanced_enabled,
                "balanced_digest_group_counts": balanced_group_counts,
                "balanced_digest_removed": (
                    eligible_count - len(important_items)
                ),
            },
        )

        return {
            "run_id": run_id,
            "kept": len(important_items),
            "threshold_override": threshold,
            "removed_by_topic_dedup": filtering_result.topic_dedup_removed,
            "removed_after_reanalysis": (
                filtering_result.topic_dedup_count - eligible_count
            ),
            "removed_by_balanced_digest": (
                eligible_count - len(important_items)
            ),
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

        orchestrator = self._orchestrator(ctx)
        enrichment_result = await orchestrator.enrich_items(items)

        artifact_path = None
        if enrichment_result.status == "failure":
            self.run_store.invalidate_from(run_id, "enriched")
        else:
            artifact_path = self.run_store.save_items(
                run_id, "enriched", items_to_dicts(items)
            )

        citation_count = 0
        for item in items:
            if item.processing:
                citation_count += sum(
                    len(artifact.sources)
                    for artifact in item.processing.artifacts.values()
                )

        meta = self.run_store.update_meta(
            run_id,
            {
                "enrichment_status": enrichment_result.status,
                "enriched_count": enrichment_result.succeeded_count,
                "enrichment_failed_count": enrichment_result.failed_count,
                "enrichment_failed_ids": enrichment_result.failed_ids,
                "citation_count": citation_count,
            },
        )

        return {
            "run_id": run_id,
            "status": enrichment_result.status,
            "enriched": enrichment_result.succeeded_count,
            "failed": enrichment_result.failed_count,
            "failed_ids": enrichment_result.failed_ids,
            "citation_count": citation_count,
            "artifact": str(artifact_path.resolve()) if artifact_path else None,
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

        summarizer = DailySummarizer(
            profile_names=self._profiles(ctx).names,
            profile_order=ctx.config.digest.profile_order,
        )
        summary = await summarizer.generate_summary(
            items,
            date_str,
            total_fetched,
            language=language,
        )

        run_summary_path = self.run_store.save_summary(run_id, language, summary)
        published_path = None
        if save_to_horizon_data:
            storage = make_storage(ctx.config_path)
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
        if enrich and filter_result["kept"] > 0:
            enrich_result = await self.enrich_items(
                run_id=run_id,
                source_stage="filtered",
                horizon_path=horizon_path,
                config_path=config_path,
            )
            if enrich_result["status"] != "failure":
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
        load_environment(resolved_horizon)
        resolved_config = resolve_config_path(resolved_horizon, config_path)
        config = load_config(resolved_config)
        effective_config, selected_sources, unknown_sources = apply_source_filter(config, sources)

        return (
            PipelineContext(
                horizon_path=resolved_horizon,
                config_path=resolved_config,
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
    ) -> tuple[list[ContentItem], PipelineContext]:
        ctx, _, _ = self._build_context(horizon_path=horizon_path, config_path=config_path, sources=None)
        try:
            payload = self.run_store.load_items(run_id, stage)
        except FileNotFoundError as exc:
            raise HorizonMcpError(
                code="HZ_STAGE_NOT_FOUND",
                message=f"run_id={run_id} is missing stage artifact: {stage}",
                details={"run_id": run_id, "stage": stage},
            ) from exc
        items = dicts_to_items(payload)
        return items, ctx

    def _orchestrator(self, ctx: PipelineContext) -> HorizonOrchestrator:
        storage = make_storage(ctx.config_path)
        return HorizonOrchestrator(
            ctx.config,
            storage,
            console=self.console,
            profiles=self._profiles(ctx),
        )

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
    def _profiles(ctx: PipelineContext) -> ProfileRegistry:
        return ProfileRegistry.load(
            Path(ctx.config.processing.profiles_dir).expanduser(),
            ctx.config.processing.default_profile,
            base_dir=ctx.horizon_path,
        )

    @staticmethod
    def _score_distribution(items: list[ContentItem]) -> dict[str, int]:
        buckets = {"unscored": 0, "0-2": 0, "3-4": 0, "5-6": 0, "7-8": 0, "9-10": 0}
        for item in items:
            analysis = item.processing.analysis if item.processing else None
            if not analysis or analysis.score is None:
                buckets["unscored"] += 1
                continue
            score = float(analysis.score)
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
        if not webhook_config:
            return {
                "sent": False,
                "status": "disabled",
                "reason": "Webhook is not configured.",
            }

        notifier = WebhookNotifier(webhook_config, console=self.console)
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

        delivery = await notifier.notify(variables)

        return {
            **delivery.to_dict(),
            "variables": {k: (v if k != "summary" else f"<{len(v)} chars>") for k, v in variables.items()},
        }
