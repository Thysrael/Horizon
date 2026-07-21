"""One-run execution orchestration with durable outcome recording."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

import httpx
from cryptography.fernet import InvalidToken
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from src.infoservice.db.models import LLMCredential, Report, ReportRun, RunStatus, SourceRunResult, SourceRunStatus
from src.infoservice.execution.contracts import ReportExecutionRequest, ReportExecutionResult
from src.infoservice.security.credentials import CredentialCipher
from src.infoservice.scheduling.repository import ClaimedRun, RunRepository

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExecutionContext:
    claim: ClaimedRun
    run: Any
    report: Any
    credential: Any
    chat_id: int


@dataclass(frozen=True, slots=True)
class SourceResultPayload:
    source_id: UUID
    status: str
    items_found: int
    error_summary: str | None


class ExecutionStore(Protocol):
    async def claim_next(self, worker_id: str, now: datetime) -> ClaimedRun | None: ...
    async def load(self, claim: ClaimedRun) -> ExecutionContext: ...
    async def touch_claim(self, context: ExecutionContext) -> bool: ...
    async def record_attempt(self, context: ExecutionContext) -> None: ...
    async def record_success(self, context: ExecutionContext, result: ReportExecutionResult, status: str) -> bool: ...
    async def record_failure(self, context: ExecutionContext, summary: str) -> bool: ...


class SqlExecutionStore:
    """Database implementation. A claimed run is only ever loaded by its id."""

    def __init__(self, session_factory: Any) -> None:
        self._factory = session_factory
        self._claims = RunRepository(session_factory)

    async def claim_next(self, worker_id: str, now: datetime) -> ClaimedRun | None:
        return await self._claims.claim_next(worker_id, now)

    async def load(self, claim: ClaimedRun) -> ExecutionContext:
        async with self._factory() as session:
            stmt = (
                select(ReportRun)
                .where(ReportRun.id == claim.id, ReportRun.report_id == claim.report_id)
                .options(joinedload(ReportRun.report).joinedload(Report.user), joinedload(ReportRun.report).joinedload(Report.sources))
            )
            run = (await session.scalars(stmt)).unique().one()
            credential = await session.scalar(
                select(LLMCredential).where(
                    LLMCredential.user_id == run.report.user_id,
                    LLMCredential.provider == "deepseek",
                )
            )
            session.expunge(run)
            return ExecutionContext(claim, run, run.report, credential, run.report.user.chat_id)

    async def touch_claim(self, context: ExecutionContext) -> bool:
        return await self._claims.touch_claim(context.claim, datetime.now(timezone.utc))

    async def record_attempt(self, context: ExecutionContext) -> None:
        async with self._factory.begin() as session:
            run = await session.get(ReportRun, context.claim.id)
            if run is not None:
                run.attempt_count += 1

    async def record_success(self, context: ExecutionContext, result: ReportExecutionResult, status: str) -> bool:
        async with self._factory.begin() as session:
            finalized = await session.execute(
                update(ReportRun)
                .where(ReportRun.id == context.claim.id, ReportRun.status == RunStatus.RUNNING, ReportRun.worker_id == context.claim.worker_id)
                .values(status=RunStatus(status), finished_at=datetime.now(timezone.utc), items_seen=result.all_items_count,
                        items_selected=len(result.items), result_markdown=result.markdown)
            )
            if finalized.rowcount != 1:
                return False
            run = await session.get(ReportRun, context.claim.id)
            assert run is not None
            for outcome in _source_result_payloads(context.report.sources, _source_outcomes(result.fetch_report)):
                session.add(SourceRunResult(
                    report_run_id=run.id, source_id=outcome.source_id,
                    status=SourceRunStatus(outcome.status),
                    items_found=outcome.items_found,
                    error_summary=outcome.error_summary,
                ))
            return True

    async def record_failure(self, context: ExecutionContext, summary: str) -> bool:
        async with self._factory.begin() as session:
            finalized = await session.execute(
                update(ReportRun)
                .where(ReportRun.id == context.claim.id, ReportRun.status == RunStatus.RUNNING, ReportRun.worker_id == context.claim.worker_id)
                .values(status=RunStatus.FAILED, finished_at=datetime.now(timezone.utc), error_summary=_safe_error(summary))
            )
            return finalized.rowcount == 1


class ExecutionService:
    def __init__(self, *, store: ExecutionStore, executor: Any, delivery: Any, renderer: Any,
                 cipher: CredentialCipher, worker_id: str, sleep: Any = asyncio.sleep,
                 semaphore: asyncio.Semaphore | None = None, heartbeat_interval: float = 30) -> None:
        self.store, self.executor, self.delivery, self.renderer = store, executor, delivery, renderer
        self.cipher, self.worker_id, self._sleep = cipher, worker_id, sleep
        self._semaphore = semaphore or asyncio.Semaphore(1)
        self._heartbeat_interval = heartbeat_interval

    async def run_once(self) -> bool:
        claim = await self.store.claim_next(self.worker_id, datetime.now(timezone.utc))
        if claim is None:
            return False
        context: ExecutionContext | None = None
        plaintext = ""
        started = datetime.now(timezone.utc)
        heartbeat_stop = asyncio.Event()
        heartbeat_task: asyncio.Task[None] | None = None
        async with self._semaphore:
            try:
                context = await self.store.load(claim)
                heartbeat_task = asyncio.create_task(self._keep_claim_alive(context, heartbeat_stop))
                await self.store.record_attempt(context)
                plaintext = self.cipher.decrypt(_ciphertext(context.credential))
                result = await self._execute_with_retries(context, plaintext)
                status = _result_status(result.fetch_report)
                finalized = await self.store.record_success(context, result, status)
                if finalized is False:
                    logger.info("report_run_lost_claim", extra={"run_id": str(claim.id), "report_id": str(claim.report_id)})
                    return True
                try:
                    rendered = _failure_notification(context.report) if status == "failed" else self.renderer.render(
                        _with_presentation_context(result, context.report, status), context.report.name
                    )
                    delivery = await self.delivery.send(context.chat_id, rendered)
                    delivery_status = getattr(delivery, "status", "unknown")
                except Exception:
                    delivery_status = "failed"
                    logger.warning("report_delivery_failed", extra={"run_id": str(claim.id), "report_id": str(claim.report_id)})
                logger.info("report_run_finished", extra={"run_id": str(claim.id), "report_id": str(claim.report_id), "status": status, "duration_ms": int((datetime.now(timezone.utc)-started).total_seconds()*1000), "items_seen": result.all_items_count, "items_selected": len(result.items), "delivery_status": delivery_status})
            except Exception as error:
                if context is not None:
                    finalized = await self.store.record_failure(context, _safe_error(f"{type(error).__name__}: {error}"))
                    if finalized is not False:
                        try:
                            await self.delivery.send(context.chat_id, _failure_notification(context.report))
                        except Exception:
                            logger.warning("report_failure_notification_failed", extra={"run_id": str(claim.id)})
                logger.warning("report_run_failed", extra={"run_id": str(claim.id), "report_id": str(claim.report_id), "error": _safe_error(f"{type(error).__name__}: {error}")})
            finally:
                plaintext = ""
                heartbeat_stop.set()
                if heartbeat_task is not None:
                    await heartbeat_task
        return True

    async def _keep_claim_alive(self, context: ExecutionContext, stop_event: asyncio.Event) -> None:
        """Persist a lease renewal while a report run is executing.

        Scheduler recovery uses this per-run lease rather than process-level
        liveness, so a healthy worker cannot have a long Horizon execution
        requeued underneath it.
        """
        while not stop_event.is_set():
            try:
                if not await self.store.touch_claim(context):
                    return
            except Exception:
                logger.warning("report_run_heartbeat_failed", extra={"run_id": str(context.claim.id)})
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self._heartbeat_interval)
            except TimeoutError:
                pass

    async def _execute_with_retries(self, context: ExecutionContext, api_key: str) -> ReportExecutionResult:
        for attempt in range(3):
            try:
                request = ReportExecutionRequest(
                    context.report.id,
                    context.report,
                    api_key,
                    context.report.custom_instruction,
                    context.report.lookback_hours,
                    getattr(context.credential, "model", None),
                )
                return await self.executor.execute(request)
            except Exception as error:
                if not _is_retryable(error) or attempt == 2:
                    raise
                await self.store.record_attempt(context)
                await self._sleep(2**attempt)
        raise AssertionError("unreachable")


def _ciphertext(credential: Any) -> str:
    if credential is None:
        raise ValueError("No DeepSeek credential configured")
    value = credential.ciphertext
    return value.decode("ascii") if isinstance(value, bytes) else value


def _source_outcomes(fetch_report: Any) -> list[dict[str, Any]]:
    if isinstance(fetch_report, dict):
        return [outcome for outcome in fetch_report.get("sources", []) if isinstance(outcome, dict)]
    return []


_HORIZON_OUTCOME_TYPES = {
    "github": "github",
    "hacker news": "hackernews",
    "rss feeds": "rss",
    "reddit": "reddit",
    "telegram": "telegram",
    "twitter": "twitter",
    "openbb": "openbb",
    "oss insight": "ossinsight",
    "gdelt": "gdelt",
    "google news": "google_news",
}


def _source_result_payloads(sources: Any, outcomes: list[dict[str, Any]]) -> list[SourceResultPayload]:
    """Expand Horizon's per-type fetch outcome to every enabled source record.

    Horizon aggregates multiple RSS/GitHub/etc. configurations into a single
    scraper, so an aggregate item count cannot be attributed honestly when a
    report has several sources of the same type.  Persist an explicit result
    for each source and use zero for that ambiguous per-source count.
    """
    active_sources = [source for source in sources if getattr(source, "enabled", True)]
    by_type: dict[str, list[Any]] = {}
    for source in active_sources:
        by_type.setdefault(str(source.source_type).casefold(), []).append(source)

    outcome_by_type: dict[str, dict[str, Any]] = {}
    for outcome in outcomes:
        label = str(outcome.get("source", "")).strip().casefold()
        source_type = _HORIZON_OUTCOME_TYPES.get(label, label)
        if source_type in by_type:
            outcome_by_type[source_type] = outcome

    payloads: list[SourceResultPayload] = []
    for source_type, typed_sources in by_type.items():
        outcome = outcome_by_type.get(source_type)
        if outcome is None:
            continue
        failed = outcome.get("status") == "failure"
        error = _safe_error(str(outcome.get("error", ""))) if failed else None
        count = int(outcome.get("item_count", 0) or 0) if len(typed_sources) == 1 else 0
        for source in typed_sources:
            payloads.append(SourceResultPayload(
                source_id=source.id,
                status="failed" if failed else "succeeded",
                items_found=count,
                error_summary=error,
            ))
    return payloads


def _result_status(fetch_report: Any) -> str:
    outcomes = _source_outcomes(fetch_report)
    failed = sum(item.get("status") == "failure" for item in outcomes)
    succeeded = sum(item.get("status") != "failure" for item in outcomes)
    if failed and succeeded:
        return "partial"
    if failed and not succeeded:
        return "failed"
    return "succeeded"


def _with_presentation_context(result: ReportExecutionResult, report: Any, status: str) -> ReportExecutionResult:
    """Attach only user-safe collection facts needed by Telegram's overview."""
    lookback = getattr(report, "lookback_hours", None)
    period = f"last {int(lookback)} hours" if isinstance(lookback, int) and lookback > 0 else None
    failed_sources: tuple[str, ...] = ()
    if status == "partial":
        failed_sources = tuple(
            str(outcome.get("source", "unknown source")).strip() or "unknown source"
            for outcome in _source_outcomes(result.fetch_report)
            if outcome.get("status") == "failure"
        )
    return replace(
        result,
        presentation_period=period,
        presentation_items_selected=len(result.items),
        failed_sources=failed_sources,
    )


def _failure_notification(report: Any) -> str:
    language = str(getattr(report, "language", "ru")).casefold()
    if language.startswith("en"):
        return "We could not collect this report right now. Please try again later."
    return "Не удалось собрать отчёт. Попробуйте ещё раз позже."


def _is_retryable(error: Exception) -> bool:
    if isinstance(error, (InvalidToken, ValueError)):
        return False
    if isinstance(error, (httpx.NetworkError, httpx.TimeoutException, OSError, TimeoutError)):
        return True
    status = getattr(error, "status_code", None)
    return status == 429 or isinstance(status, int) and status >= 500


def _safe_error(value: str) -> str:
    return _redact(value)[:1000]


def _redact(value: str) -> str:
    from src.infoservice.security.credentials import _API_KEY_PATTERN
    return _API_KEY_PATTERN.sub("[REDACTED]", value)
