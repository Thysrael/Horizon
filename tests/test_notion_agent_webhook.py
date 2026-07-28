from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.notion_agent.config import AgentConfig
from src.notion_agent.queue import EventQueue
from src.notion_agent.webhook import create_app


def _config(
    tmp_path: Path,
    *,
    verification_token: str = "verification-secret",
    bootstrap_secret: str = "bootstrap-secret",
) -> AgentConfig:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return AgentConfig.from_env(
        {
            "HORIZON_REPO_ROOT": str(repo),
            "NOTION_AGENT_RUNTIME_DIR": str(tmp_path / "runtime"),
            "NOTION_TOKEN": "notion-secret",
            "NOTION_DATA_SOURCE_ID": "67132048-6501-4156-be51-28a288d6b771",
            "NOTION_WORKSPACE_ID": "workspace-1",
            "NOTION_INTEGRATION_ID": "integration-1",
            "NOTION_WEBHOOK_VERIFICATION_TOKEN": verification_token,
            "NOTION_WEBHOOK_BOOTSTRAP_SECRET": bootstrap_secret,
            "GITHUB_REPOSITORY": "example/horizon",
            "NOTION_AGENT_DISABLE_WORKER": "true",
        }
    )


def _event(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "event-1",
        "type": "page.properties_updated",
        "workspace_id": "workspace-1",
        "integration_id": "integration-1",
        "entity": {"type": "page", "id": "page-1"},
        "data": {
            "parent": {
                "type": "data_source_id",
                "data_source_id": "67132048-6501-4156-be51-28a288d6b771",
            }
        },
    }
    payload.update(overrides)
    return payload


def _signed_body(payload: dict[str, object], token: str) -> tuple[bytes, str]:
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = "sha256=" + hmac.new(token.encode(), body, hashlib.sha256).hexdigest()
    return body, signature


def test_webhook_validates_signature_and_deduplicates(tmp_path: Path) -> None:
    config = _config(tmp_path)
    queue = EventQueue(config.runtime_dir / "events.sqlite3")
    body, signature = _signed_body(_event(), "verification-secret")

    with TestClient(create_app(config, queue=queue)) as client:
        first = client.post(
            "/notion/webhook",
            content=body,
            headers={
                "content-type": "application/json",
                "x-notion-signature": signature,
            },
        )
        second = client.post(
            "/notion/webhook",
            content=body,
            headers={
                "content-type": "application/json",
                "x-notion-signature": signature,
            },
        )

    assert first.status_code == 200
    assert first.json() == {"accepted": True, "duplicate": False}
    assert second.json() == {"accepted": True, "duplicate": True}
    assert queue.counts()["queued"] == 1


def test_webhook_rejects_invalid_signature(tmp_path: Path) -> None:
    config = _config(tmp_path)

    with TestClient(create_app(config)) as client:
        response = client.post(
            "/notion/webhook",
            json=_event(),
            headers={"x-notion-signature": "sha256=wrong"},
        )

    assert response.status_code == 401
    assert response.json()["reason"] == "invalid_signature"


def test_webhook_ignores_other_data_sources(tmp_path: Path) -> None:
    config = _config(tmp_path)
    payload = _event(
        data={
            "parent": {
                "type": "data_source_id",
                "data_source_id": "another-data-source",
            }
        }
    )
    body, signature = _signed_body(payload, "verification-secret")

    with TestClient(create_app(config)) as client:
        response = client.post(
            "/notion/webhook",
            content=body,
            headers={
                "content-type": "application/json",
                "x-notion-signature": signature,
            },
        )

    assert response.status_code == 200
    assert response.json()["reason"] == "data_source_ignored"


def test_webhook_captures_initial_verification_token(tmp_path: Path) -> None:
    config = _config(tmp_path, verification_token="")

    with TestClient(create_app(config)) as client:
        response = client.post(
            "/notion/webhook?setup=bootstrap-secret",
            json={"verification_token": "captured-secret"},
        )
        health = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["reason"] == "verification_token_captured"
    assert health.json()["verification_token_configured"] is True
    assert (
        config.verification_token_file.read_text(encoding="utf-8").strip()
        == "captured-secret"
    )


def test_webhook_rejects_unauthorized_verification_bootstrap(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path, verification_token="")

    with TestClient(create_app(config)) as client:
        response = client.post(
            "/notion/webhook?setup=wrong",
            json={"verification_token": "attacker-token"},
        )

    assert response.status_code == 403
    assert response.json()["reason"] == "verification_bootstrap_unauthorized"
    assert not config.verification_token_file.exists()


def test_webhook_ignores_event_without_a_data_source(tmp_path: Path) -> None:
    config = _config(tmp_path)
    body, signature = _signed_body(_event(data={}), "verification-secret")

    with TestClient(create_app(config)) as client:
        response = client.post(
            "/notion/webhook",
            content=body,
            headers={
                "content-type": "application/json",
                "x-notion-signature": signature,
            },
        )

    assert response.status_code == 200
    assert response.json()["reason"] == "data_source_ignored"
