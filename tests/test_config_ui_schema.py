from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.config_ui.app import create_app
from src.config_ui.security import SessionStore
from src.config_ui.ui_metadata import SECTIONS, UI_METADATA


BASE_URL = "http://127.0.0.1:8765"


def test_authenticated_schema_includes_model_ui_and_initialization_metadata(
    tmp_path: Path,
):
    sessions = SessionStore("bootstrap-token")
    app = create_app(tmp_path / "config.json", session_store=sessions)

    with TestClient(app, base_url=BASE_URL) as client:
        bootstrap = client.post(
            "/api/v1/session/bootstrap",
            headers={"Origin": BASE_URL},
            json={"token": "bootstrap-token"},
        )
        assert bootstrap.status_code == 200
        response = client.get("/api/v1/schema")

    body = response.json()
    assert response.status_code == 200
    assert {"version", "ai", "sources", "filtering"} <= set(
        body["schema"]["properties"]
    )
    assert body["ui"] == UI_METADATA
    assert body["ui"]["sections"] == SECTIONS
    assert body["ui"]["conditions"][0]["preserve_when_hidden"] is True
    assert "minimal" in body["initialization"]


def test_schema_requires_a_process_local_session(tmp_path: Path):
    app = create_app(tmp_path / "config.json")

    with TestClient(app, base_url=BASE_URL) as client:
        response = client.get("/api/v1/schema")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_session"
