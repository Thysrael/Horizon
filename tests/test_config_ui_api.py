from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.config_ui.app import create_app
from src.config_ui.initialization import minimal_config
from src.config_ui.security import SessionStore


BASE_URL = "http://127.0.0.1:8765"
ORIGIN = BASE_URL


@contextmanager
def _authenticated_client(
    config_path: Path,
) -> Iterator[tuple[TestClient, dict[str, str]]]:
    sessions = SessionStore("bootstrap-token")
    app = create_app(config_path, session_store=sessions)
    with TestClient(app, base_url=BASE_URL) as client:
        response = client.post(
            "/api/v1/session/bootstrap",
            headers={"Origin": ORIGIN},
            json={"token": "bootstrap-token"},
        )
        assert response.status_code == 200
        yield client, {
            "Origin": ORIGIN,
            "X-CSRF-Token": response.json()["csrf_token"],
        }


def _write_config(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        f"{json.dumps(data, indent=2, ensure_ascii=False)}\n",
        encoding="utf-8",
    )


def test_config_api_requires_a_session(tmp_path: Path):
    app = create_app(tmp_path / "config.json")

    with TestClient(app, base_url=BASE_URL) as client:
        response = client.get("/api/v1/config")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_session"


def test_missing_config_is_returned_without_writing_initialization_drafts(
    tmp_path: Path,
):
    path = tmp_path / "config.json"

    with _authenticated_client(path) as (client, _headers):
        current = client.get("/api/v1/config")
        schema = client.get("/api/v1/schema")

    assert current.status_code == 200
    assert current.json()["exists"] is False
    assert current.json()["config"] is None
    assert current.json()["revision"] is None
    assert schema.json()["initialization"]["minimal"] == minimal_config()
    assert not path.exists()


def test_read_validate_diff_create_save_and_revision_conflict(tmp_path: Path):
    path = tmp_path / "config.json"
    initial = minimal_config()
    initial["future_feature"] = {"mode": "preserve-me"}
    create_patch = [{"op": "add", "path": "", "value": initial}]

    with _authenticated_client(path) as (client, headers):
        draft = client.post(
            "/api/v1/config/diff",
            headers=headers,
            json={"revision": None, "patch": create_patch},
        )
        assert not path.exists()

        created = client.patch(
            "/api/v1/config",
            headers=headers,
            json={
                "revision": None,
                "patch": create_patch,
                "acknowledge_warnings": True,
            },
        )
        original_revision = created.json()["revision"]
        current = client.get("/api/v1/config")
        validation = client.post(
            "/api/v1/config/validate",
            headers=headers,
            json={"config": current.json()["config"]},
        )
        saved = client.patch(
            "/api/v1/config",
            headers=headers,
            json={
                "revision": original_revision,
                "patch": [
                    {
                        "op": "replace",
                        "path": "/filtering/time_window_hours",
                        "value": 48,
                    }
                ],
                "acknowledge_warnings": True,
            },
        )
        conflict = client.patch(
            "/api/v1/config",
            headers=headers,
            json={
                "revision": original_revision,
                "patch": [
                    {
                        "op": "replace",
                        "path": "/filtering/time_window_hours",
                        "value": 72,
                    }
                ],
                "acknowledge_warnings": True,
            },
        )

    assert draft.status_code == 200
    assert draft.json()["changed"] is True
    assert created.status_code == 200
    assert created.json()["backup_id"] is None
    assert current.status_code == 200
    assert current.json()["exists"] is True
    assert current.json()["config"]["future_feature"] == {"mode": "preserve-me"}
    assert validation.status_code == 200
    assert validation.json()["validation"]["valid"] is True
    assert saved.status_code == 200
    assert saved.json()["backup_id"]
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "revision_conflict"
    assert json.loads(path.read_text(encoding="utf-8"))["future_feature"] == {
        "mode": "preserve-me"
    }


def test_invalid_patch_and_configuration_errors_are_stable_and_sanitized(
    tmp_path: Path,
):
    path = tmp_path / "config.json"
    private_value = "private-invalid-value-must-not-escape"
    _write_config(path, minimal_config())

    with _authenticated_client(path) as (client, headers):
        revision = client.get("/api/v1/config").json()["revision"]
        invalid_patch = client.post(
            "/api/v1/config/diff",
            headers=headers,
            json={
                "revision": revision,
                "patch": [
                    {
                        "op": private_value,
                        "path": "/filtering/time_window_hours",
                    }
                ],
            },
        )
        invalid_config = client.patch(
            "/api/v1/config",
            headers=headers,
            json={
                "revision": revision,
                "patch": [
                    {
                        "op": "replace",
                        "path": "/filtering/time_window_hours",
                        "value": private_value,
                    }
                ],
                "acknowledge_warnings": True,
            },
        )

    assert invalid_patch.status_code == 422
    assert invalid_patch.json()["error"]["code"] == "unsupported_operation"
    assert invalid_config.status_code == 422
    assert invalid_config.json()["error"]["code"] == "configuration_invalid"
    assert invalid_config.json()["error"]["report"]["valid"] is False
    assert private_value not in invalid_patch.text
    assert private_value not in invalid_config.text


def test_warning_acknowledgement_is_required_before_initial_create(
    tmp_path: Path,
    monkeypatch,
):
    path = tmp_path / "config.json"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    patch = [{"op": "add", "path": "", "value": minimal_config()}]

    with _authenticated_client(path) as (client, headers):
        rejected = client.patch(
            "/api/v1/config",
            headers=headers,
            json={"revision": None, "patch": patch},
        )
        accepted = client.patch(
            "/api/v1/config",
            headers=headers,
            json={
                "revision": None,
                "patch": patch,
                "acknowledge_warnings": True,
            },
        )

    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "warnings_not_acknowledged"
    assert rejected.json()["error"]["report"]["missing_env"] == ["OPENAI_API_KEY"]
    assert accepted.status_code == 200
    assert path.is_file()


def test_config_writes_keep_origin_session_and_csrf_protection(tmp_path: Path):
    path = tmp_path / "config.json"
    sessions = SessionStore("bootstrap-token")
    app = create_app(path, session_store=sessions)
    payload = {
        "revision": None,
        "patch": [{"op": "add", "path": "", "value": minimal_config()}],
        "acknowledge_warnings": True,
    }

    with TestClient(app, base_url=BASE_URL) as client:
        no_session = client.patch(
            "/api/v1/config",
            headers={"Origin": ORIGIN},
            json=payload,
        )
        bootstrap = client.post(
            "/api/v1/session/bootstrap",
            headers={"Origin": ORIGIN},
            json={"token": "bootstrap-token"},
        )
        no_origin = client.patch("/api/v1/config", json=payload)
        no_csrf = client.patch(
            "/api/v1/config",
            headers={"Origin": ORIGIN},
            json=payload,
        )
        accepted = client.patch(
            "/api/v1/config",
            headers={
                "Origin": ORIGIN,
                "X-CSRF-Token": bootstrap.json()["csrf_token"],
            },
            json=payload,
        )

    assert no_session.status_code == 401
    assert no_session.json()["error"]["code"] == "invalid_session"
    assert no_origin.status_code == 403
    assert no_origin.json()["error"]["code"] == "invalid_origin"
    assert no_csrf.status_code == 403
    assert no_csrf.json()["error"]["code"] == "invalid_csrf"
    assert accepted.status_code == 200


def test_io_errors_do_not_expose_exception_details(tmp_path: Path, monkeypatch):
    private_detail = "private-path-or-secret-from-os-error"
    sessions = SessionStore("bootstrap-token")
    app = create_app(tmp_path / "config.json", session_store=sessions)

    with TestClient(app, base_url=BASE_URL) as client:
        bootstrap = client.post(
            "/api/v1/session/bootstrap",
            headers={"Origin": ORIGIN},
            json={"token": "bootstrap-token"},
        )
        assert bootstrap.status_code == 200
        monkeypatch.setattr(
            app.state.config_service,
            "load",
            lambda: (_ for _ in ()).throw(OSError(private_detail)),
        )
        response = client.get("/api/v1/config")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "configuration_io_error"
    assert private_detail not in response.text
