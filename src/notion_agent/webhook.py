"""FastAPI webhook listener for Notion connection events."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
from collections.abc import Mapping
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import AgentConfig, VerificationTokenStore
from .executor import LocalAgentExecutor, WorkerLoop
from .queue import EventQueue

LOGGER = logging.getLogger(__name__)


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _verify_signature(raw_body: bytes, signature: str, token: str) -> bool:
    expected = (
        "sha256="
        + hmac.new(token.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    )
    return hmac.compare_digest(signature, expected)


def _event_data_source(payload: Mapping[str, Any]) -> str:
    data = _mapping(payload.get("data"))
    parent = _mapping(data.get("parent"))
    return _text(parent.get("data_source_id") or parent.get("id"))


def _event_page_id(payload: Mapping[str, Any]) -> str:
    entity = _mapping(payload.get("entity"))
    if entity.get("type") != "page":
        return ""
    return _text(entity.get("id"))


def create_app(
    config: AgentConfig,
    *,
    queue: EventQueue | None = None,
    executor: LocalAgentExecutor | None = None,
) -> FastAPI:
    """Create the local listener with an optional background Codex worker."""

    event_queue = queue or EventQueue(config.runtime_dir / "events.sqlite3")
    token_store = VerificationTokenStore(config)
    task_executor = executor or LocalAgentExecutor(config)
    worker = WorkerLoop(
        event_queue,
        task_executor,
        poll_seconds=config.queue_poll_seconds,
    )
    worker_thread: threading.Thread | None = None

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        nonlocal worker_thread
        if not config.disable_worker:
            worker_thread = threading.Thread(
                target=worker.run,
                name="horizon-notion-agent",
                daemon=True,
            )
            worker_thread.start()
        try:
            yield
        finally:
            worker.stop()
            if worker_thread is not None:
                worker_thread.join(timeout=10)

    app = FastAPI(
        title="Horizon Notion Agent",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.config = config
    app.state.event_queue = event_queue
    app.state.token_store = token_store
    app.state.worker = worker

    @app.get("/healthz")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "worker_enabled": not config.disable_worker,
            "verification_token_configured": bool(token_store.get()),
            "queue": event_queue.counts(),
        }

    @app.post("/notion/webhook")
    async def notion_webhook(request: Request) -> JSONResponse:
        raw_body = await request.body()
        if len(raw_body) > config.max_webhook_bytes:
            return JSONResponse(
                status_code=413,
                content={"accepted": False, "reason": "payload_too_large"},
            )
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"accepted": False, "reason": "invalid_json"},
            )
        if not isinstance(payload, dict):
            return JSONResponse(
                status_code=400,
                content={"accepted": False, "reason": "invalid_payload"},
            )

        bootstrap_token = _text(payload.get("verification_token"))
        if bootstrap_token:
            supplied_secret = request.query_params.get("setup", "")
            expected_secret = config.webhook_bootstrap_secret
            if (
                not expected_secret
                or not supplied_secret
                or not hmac.compare_digest(supplied_secret, expected_secret)
            ):
                return JSONResponse(
                    status_code=403,
                    content={
                        "accepted": False,
                        "reason": "verification_bootstrap_unauthorized",
                    },
                )
            captured = token_store.capture(bootstrap_token)
            status_code = 200 if captured else 409
            return JSONResponse(
                status_code=status_code,
                content={
                    "accepted": captured,
                    "reason": (
                        "verification_token_captured"
                        if captured
                        else "verification_token_conflict"
                    ),
                },
            )

        token = token_store.get()
        signature = request.headers.get("x-notion-signature", "")
        if (
            not token
            or not signature
            or not _verify_signature(raw_body, signature, token)
        ):
            return JSONResponse(
                status_code=401,
                content={"accepted": False, "reason": "invalid_signature"},
            )

        event_type = _text(payload.get("type"))
        if event_type not in config.allowed_event_types:
            return JSONResponse(
                status_code=200,
                content={"accepted": False, "reason": "event_type_ignored"},
            )
        if (
            config.notion_workspace_id
            and _text(payload.get("workspace_id")) != config.notion_workspace_id
        ):
            return JSONResponse(
                status_code=403,
                content={"accepted": False, "reason": "workspace_mismatch"},
            )
        if (
            config.notion_integration_id
            and _text(payload.get("integration_id")) != config.notion_integration_id
        ):
            return JSONResponse(
                status_code=403,
                content={"accepted": False, "reason": "integration_mismatch"},
            )

        data_source_id = _event_data_source(payload)
        if not data_source_id or not config.matches_data_source(data_source_id):
            return JSONResponse(
                status_code=200,
                content={"accepted": False, "reason": "data_source_ignored"},
            )

        event_id = _text(payload.get("id"))
        page_id = _event_page_id(payload)
        if not event_id or not page_id:
            return JSONResponse(
                status_code=400,
                content={"accepted": False, "reason": "event_identity_missing"},
            )

        inserted = event_queue.enqueue(
            event_id=event_id,
            event_type=event_type,
            page_id=page_id,
            payload=payload,
        )
        LOGGER.info(
            "Accepted Notion event %s for page %s (new=%s)",
            event_id,
            page_id,
            inserted,
        )
        return JSONResponse(
            status_code=200,
            content={
                "accepted": True,
                "duplicate": not inserted,
            },
        )

    return app
