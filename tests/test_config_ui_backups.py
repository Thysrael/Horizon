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


@contextmanager
def _authenticated_client(
    config_path: Path,
) -> Iterator[tuple[TestClient, dict[str, str]]]:
    sessions = SessionStore("bootstrap-token")
    app = create_app(config_path, session_store=sessions)
    with TestClient(app, base_url=BASE_URL) as client:
        bootstrap = client.post(
            "/api/v1/session/bootstrap",
            headers={"Origin": BASE_URL},
            json={"token": "bootstrap-token"},
        )
        assert bootstrap.status_code == 200
        yield client, {
            "Origin": BASE_URL,
            "X-CSRF-Token": bootstrap.json()["csrf_token"],
        }


def _write_config(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        f"{json.dumps(data, indent=2, ensure_ascii=False)}\n",
        encoding="utf-8",
    )


def _save_threshold(
    client: TestClient,
    headers: dict[str, str],
    revision: str,
    value: float,
):
    return client.patch(
        "/api/v1/config",
        headers=headers,
        json={
            "revision": revision,
            "patch": [
                {
                    "op": "replace",
                    "path": "/filtering/ai_score_threshold",
                    "value": value,
                }
            ],
            "acknowledge_warnings": True,
        },
    )


def test_backup_list_and_diff_return_only_public_redacted_data(tmp_path: Path):
    path = tmp_path / "config.json"
    old_secret = "old-private-token"
    new_secret = "new-private-token"
    config = minimal_config()
    config["future_secret"] = old_secret
    _write_config(path, config)

    with _authenticated_client(path) as (client, headers):
        revision = client.get("/api/v1/config").json()["revision"]
        saved = client.patch(
            "/api/v1/config",
            headers=headers,
            json={
                "revision": revision,
                "patch": [
                    {
                        "op": "replace",
                        "path": "/future_secret",
                        "value": new_secret,
                    }
                ],
                "acknowledge_warnings": True,
            },
        )
        backup_id = saved.json()["backup_id"]
        backups = client.get("/api/v1/backups")
        diff = client.get(f"/api/v1/backups/{backup_id}/diff")

    assert saved.status_code == 200
    assert backups.status_code == 200
    assert backups.json()["backups"][0]["id"] == backup_id
    assert "path" not in backups.json()["backups"][0]
    assert diff.status_code == 200
    assert diff.json()["changed"] is True
    assert old_secret not in diff.text
    assert new_secret not in diff.text
    assert "redacted" in diff.text


def test_backup_api_rejects_invalid_and_traversal_identifiers(tmp_path: Path):
    path = tmp_path / "config.json"
    _write_config(path, minimal_config())

    with _authenticated_client(path) as (client, _headers):
        invalid = client.get("/api/v1/backups/not-a-backup/diff")
        traversal = client.get("/api/v1/backups/..%2Fconfig.json/diff")

    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_backup_id"
    assert traversal.status_code in {404, 422}
    assert str(path) not in traversal.text


def test_restore_requires_confirmation_and_current_revision(tmp_path: Path):
    path = tmp_path / "config.json"
    _write_config(path, minimal_config())

    with _authenticated_client(path) as (client, headers):
        original_revision = client.get("/api/v1/config").json()["revision"]
        saved = _save_threshold(client, headers, original_revision, 8.0)
        assert saved.status_code == 200
        backup_id = saved.json()["backup_id"]
        current_revision = saved.json()["revision"]

        unconfirmed = client.post(
            f"/api/v1/backups/{backup_id}/restore",
            headers=headers,
            json={"revision": current_revision, "confirm": False},
        )
        stale = client.post(
            f"/api/v1/backups/{backup_id}/restore",
            headers=headers,
            json={
                "revision": original_revision,
                "confirm": True,
                "acknowledge_warnings": True,
            },
        )
        restored = client.post(
            f"/api/v1/backups/{backup_id}/restore",
            headers=headers,
            json={
                "revision": current_revision,
                "confirm": True,
                "acknowledge_warnings": True,
            },
        )

    assert unconfirmed.status_code == 422
    assert unconfirmed.json()["error"]["code"] == "restore_not_confirmed"
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "revision_conflict"
    assert restored.status_code == 200
    assert json.loads(path.read_text(encoding="utf-8"))["filtering"][
        "ai_score_threshold"
    ] == 7.0
