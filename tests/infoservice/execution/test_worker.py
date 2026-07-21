from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.infoservice.delivery.telegram import DeliveryResult
from src.infoservice.execution.contracts import ReportExecutionResult
from src.infoservice.execution.worker import ExecutionContext, ExecutionService
from src.infoservice.scheduling.repository import ClaimedRun


class MemoryRunStore:
    def __init__(self, context: ExecutionContext) -> None:
        self.context = context
        self.claimed = False
        self.succeeded: list[tuple[ExecutionContext, ReportExecutionResult, str]] = []
        self.failed: list[tuple[ExecutionContext, str]] = []
        self.attempts = 0
        self.finalize = True

    async def claim_next(self, worker_id, now):
        if self.claimed:
            return None
        self.claimed = True
        return self.context.claim

    async def load(self, claim):
        return self.context

    async def record_attempt(self, context):
        self.attempts += 1

    async def record_success(self, context, result, status):
        self.succeeded.append((context, result, status))
        return self.finalize

    async def record_failure(self, context, summary):
        self.failed.append((context, summary))
        return self.finalize


def _context() -> ExecutionContext:
    now = datetime.now(timezone.utc)
    report = SimpleNamespace(id=uuid4(), name="Morning", custom_instruction=None, lookback_hours=24)
    credential = SimpleNamespace(ciphertext=b"encrypted", model="deepseek-v4-flash")
    return ExecutionContext(
        claim=ClaimedRun(uuid4(), report.id, now, "test", now),
        run=SimpleNamespace(id=uuid4(), attempt_count=0),
        report=report,
        credential=credential,
        chat_id=123,
    )


@pytest.mark.asyncio
async def test_worker_records_partial_result_and_delivers():
    context = _context()
    store = MemoryRunStore(context)
    result = ReportExecutionResult(
        markdown="# report", items=[], all_items_count=8,
        fetch_report={"sources": [{"source": "A", "status": "success"}, {"source": "B", "status": "failure"}]},
        usage={"total_tokens": 10},
    )
    executor = SimpleNamespace(execute=AsyncMock(return_value=result))
    delivery = SimpleNamespace(send=AsyncMock(return_value=DeliveryResult("sent")))
    renderer = SimpleNamespace(render=lambda value, name: "rendered")
    cipher = SimpleNamespace(decrypt=lambda value: "sk-private-key")
    worker = ExecutionService(
        store=store, executor=executor, delivery=delivery, renderer=renderer,
        cipher=cipher, worker_id="test", sleep=AsyncMock(),
    )

    assert await worker.run_once() is True

    assert store.attempts == 1
    assert store.succeeded[0][2] == "partial"
    delivery.send.assert_awaited_once_with(123, "rendered")


@pytest.mark.asyncio
async def test_worker_uses_persisted_credential_model_for_execution_request():
    context = _context()
    context.credential.model = "deepseek-reasoner"
    store = MemoryRunStore(context)
    result = ReportExecutionResult("# report", [], 0, {"sources": []}, {})
    executor = SimpleNamespace(execute=AsyncMock(return_value=result))
    worker = ExecutionService(
        store=store, executor=executor, delivery=SimpleNamespace(send=AsyncMock()),
        renderer=SimpleNamespace(render=lambda value, name: "rendered"),
        cipher=SimpleNamespace(decrypt=lambda value: "sk-private-key"), worker_id="test", sleep=AsyncMock(),
    )

    await worker.run_once()

    assert executor.execute.await_args.args[0].model == "deepseek-reasoner"


@pytest.mark.asyncio
async def test_worker_sends_safe_notice_when_every_source_failed():
    context = _context()
    store = MemoryRunStore(context)
    result = ReportExecutionResult(
        markdown="sk-should-never-be-delivered",
        items=[], all_items_count=0,
        fetch_report={"sources": [{"source": "RSS Feeds", "status": "failure", "error": "sk-private-key"}]}, usage={},
    )
    delivery = SimpleNamespace(send=AsyncMock(return_value=DeliveryResult("sent")))
    renderer = SimpleNamespace(render=Mock(return_value="unsafe sk-private-key"))
    worker = ExecutionService(
        store=store, executor=SimpleNamespace(execute=AsyncMock(return_value=result)), delivery=delivery, renderer=renderer,
        cipher=SimpleNamespace(decrypt=lambda value: "sk-private-key"), worker_id="test", sleep=AsyncMock(),
    )

    await worker.run_once()

    message = delivery.send.await_args.args[1]
    assert store.succeeded[0][2] == "failed"
    assert "sk-private-key" not in message
    assert "Не удалось" in message
    renderer.render.assert_not_called()


@pytest.mark.asyncio
async def test_delivery_failure_does_not_overwrite_a_durable_success():
    context = _context()
    store = MemoryRunStore(context)
    result = ReportExecutionResult("# report", [], 1, {"sources": [{"source": "GitHub", "status": "success"}]}, {})
    worker = ExecutionService(
        store=store, executor=SimpleNamespace(execute=AsyncMock(return_value=result)),
        delivery=SimpleNamespace(send=AsyncMock(side_effect=OSError("telegram unavailable"))),
        renderer=SimpleNamespace(render=lambda *_: "rendered"),
        cipher=SimpleNamespace(decrypt=lambda value: "sk-private-key"), worker_id="test", sleep=AsyncMock(),
    )

    await worker.run_once()

    assert store.succeeded[0][2] == "succeeded"
    assert store.failed == []


@pytest.mark.asyncio
async def test_lost_claim_is_not_delivered_or_finalized_again():
    context = _context()
    store = MemoryRunStore(context)
    store.finalize = False
    delivery = SimpleNamespace(send=AsyncMock())
    worker = ExecutionService(
        store=store, executor=SimpleNamespace(execute=AsyncMock(return_value=ReportExecutionResult("# report", [], 0, {"sources": []}, {}))),
        delivery=delivery, renderer=SimpleNamespace(render=lambda *_: "rendered"),
        cipher=SimpleNamespace(decrypt=lambda value: "sk-private-key"), worker_id="test", sleep=AsyncMock(),
    )

    await worker.run_once()

    delivery.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_key_fails_without_retry_and_is_redacted():
    context = _context()
    store = MemoryRunStore(context)
    cipher = SimpleNamespace(decrypt=lambda value: (_ for _ in ()).throw(ValueError("bad sk-secret-key")))
    delivery = SimpleNamespace(send=AsyncMock(return_value=DeliveryResult("sent")))
    worker = ExecutionService(
        store=store, executor=SimpleNamespace(execute=AsyncMock()),
        delivery=delivery, renderer=SimpleNamespace(render=AsyncMock()),
        cipher=cipher, worker_id="test", sleep=AsyncMock(),
    )

    assert await worker.run_once() is True

    assert store.attempts == 1
    assert len(store.failed) == 1
    assert "sk-secret-key" not in store.failed[0][1]
    assert "sk-secret-key" not in delivery.send.await_args.args[1]


@pytest.mark.asyncio
async def test_retryable_execution_is_attempted_three_times():
    context = _context()
    store = MemoryRunStore(context)
    error = OSError("temporary network failure")
    executor = SimpleNamespace(execute=AsyncMock(side_effect=[error, error, error]))
    worker = ExecutionService(
        store=store, executor=executor, delivery=SimpleNamespace(send=AsyncMock()),
        renderer=SimpleNamespace(render=AsyncMock()), cipher=SimpleNamespace(decrypt=lambda value: "sk-key"),
        worker_id="test", sleep=AsyncMock(),
    )

    await worker.run_once()

    assert executor.execute.await_count == 3
    assert store.attempts == 3
