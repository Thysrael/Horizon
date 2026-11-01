"""Offline integration checks for the portable skill adapter."""

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from src.mcp import horizon_adapter
from src.mcp.run_store import RunStore
from src.mcp.service import HorizonPipelineService
from src.models import ContentItem, SourceType


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/horizon/scripts/horizon_ops.py"
spec = importlib.util.spec_from_file_location("horizon_skill_ops", SCRIPT)
ops = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


@pytest.fixture
def config_file(tmp_path, monkeypatch):
    # Tests never load a developer's credentials or contact external services.
    monkeypatch.setattr(horizon_adapter, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(horizon_adapter, "_load_mcp_secrets", lambda *args, **kwargs: None)
    path = tmp_path / "custom-config.json"
    path.write_text(json.dumps({
        "ai": {"provider": "openai", "model": "test", "api_key_env": "SKILL_TEST_KEY"},
        "sources": {"hackernews": {"enabled": False}},
        "processing": {"profile_settings": {"tech-news": {"threshold": 4, "topic_dedup": False}}},
    }), encoding="utf-8")
    return path


def invoke(capsys, tmp_path, operation, params=None, *extra):
    code = ops.main([
        operation, "--horizon-path", str(ROOT), "--runs-root", str(tmp_path / "runs"),
        "--params", json.dumps(params or {}), *extra,
    ])
    return code, json.loads(capsys.readouterr().out)


def test_copied_helper_discovers_service_without_config(tmp_path):
    installed = tmp_path / "installed skill" / "horizon_ops.py"
    installed.parent.mkdir()
    shutil.copyfile(SCRIPT, installed)
    completed = subprocess.run(
        [sys.executable, str(installed), "run_pipeline", "--horizon-path", str(ROOT),
         "--runs-root", str(tmp_path / "runs"), "--describe"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    result = json.loads(completed.stdout)
    assert result["ok"]
    assert "save_to_horizon_data" in result["data"]["signature"]
    assert not (tmp_path / "runs").exists()


def test_explicit_missing_checkout_does_not_fall_back(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HORIZON_PATH", str(ROOT))
    assert ops.main(["list_runs", "--horizon-path", str(tmp_path)]) == 1
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "FileNotFoundError"


def test_validation_reports_missing_environment_as_native_result(tmp_path, config_file, monkeypatch, capsys):
    monkeypatch.delenv("SKILL_TEST_KEY", raising=False)
    code, result = invoke(capsys, tmp_path, "validate_config", {"config_path": str(config_file)})
    assert code == 0  # Dispatch succeeded; readiness is in the native payload.
    assert result["data"]["missing_env"] == ["SKILL_TEST_KEY"]
    assert result["data"]["config_path"] == str(config_file)


def test_invalid_config_error_does_not_echo_secret_input(tmp_path, config_file, capsys):
    payload = json.loads(config_file.read_text())
    payload["ai"]["max_tokens"] = "private-example-token"
    config_file.write_text(json.dumps(payload), encoding="utf-8")
    code, result = invoke(capsys, tmp_path, "validate_config", {"config_path": str(config_file)})
    assert code == 1
    assert result["error"]["fields"] == [{"location": ["ai", "max_tokens"], "type": "int_parsing"}]
    assert "private-example-token" not in json.dumps(result)


def test_filter_recovers_run_config_and_invalidates_only_downstream(tmp_path, config_file, capsys):
    store = RunStore(tmp_path / "runs")
    run_id = store.create_run()
    items = []
    for index, score in enumerate((4, 9)):
        item = ContentItem(
            id=f"rss:test:{index}", source_type=SourceType.RSS,
            title=f"Article {index}", url=f"https://example.com/{index}",
            published_at=datetime.now(timezone.utc), profile="tech-news",
            processing={
                "classification": {"profile": "tech-news", "method": "source_override"},
                "analysis": {"score": score, "reason": "fixture", "summary": "Fixture summary"},
            },
        )
        items.append(item.model_dump(mode="json"))
    store.save_items(run_id, "raw", items)
    scored = store.save_items(run_id, "scored", items)
    before = scored.read_bytes()
    store.save_items(run_id, "enriched", items)
    summary = store.save_summary(run_id, "zh", "old digest")
    store.update_meta(run_id, {"config_path": str(config_file), "horizon_path": str(ROOT)})
    config_before = config_file.read_bytes()

    code, result = invoke(capsys, tmp_path, "filter_items", {
        "run_id": run_id, "threshold": 8, "topic_dedup": False,
    })

    assert code == 0
    assert result["data"]["kept"] == 1
    assert store.load_items(run_id, "filtered")[0]["id"] == "rss:test:1"
    assert scored.read_bytes() == before
    assert store.has_stage(run_id, "raw")
    assert not store.has_stage(run_id, "enriched")
    assert not summary.exists()
    assert config_file.read_bytes() == config_before


def test_read_stage_from_copied_helper_needs_no_active_config(tmp_path):
    store = RunStore(tmp_path / "runs")
    run_id = store.create_run()
    store.save_items(run_id, "raw", [{"id": "one"}, {"id": "two"}])
    params = tmp_path / "parameters.json"
    params.write_text(json.dumps({"run_id": run_id, "stage": "raw", "max_items": 1}), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "get_run_stage", "--runs-root", str(store.root),
         "--params-file", str(params)],
        cwd=tmp_path, env={**os.environ, "HORIZON_PATH": str(ROOT)},
        capture_output=True, text=True, check=True,
    )
    data = json.loads(completed.stdout)["data"]
    assert data == {"run_id": run_id, "stage": "raw", "count": 2, "items": [{"id": "one"}], "truncated": True}


def test_native_partial_result_and_stdout_are_preserved(tmp_path, monkeypatch, capsys):
    async def fetch(self, hours=24, horizon_path=None, config_path=None):
        print("provider diagnostic")
        return {"fetched": 2, "fetch_status": "partial_failure", "fetch_report": {"failed_count": 1}}

    monkeypatch.setattr(HorizonPipelineService, "fetch_items", fetch)
    code, result = invoke(capsys, tmp_path, "fetch_items", {"hours": 12})
    assert code == 0
    assert result["data"]["fetch_status"] == "partial_failure"
    assert result["data"]["fetch_report"]["failed_count"] == 1


@pytest.mark.parametrize("params", [{"made_up_option": True}, ["not", "an", "object"]])
def test_bad_parameters_do_not_execute_service(tmp_path, monkeypatch, capsys, params):
    def list_runs(self, limit=20):
        pytest.fail("Invalid arguments must not invoke the service")

    monkeypatch.setattr(HorizonPipelineService, "list_runs", list_runs)
    code, result = invoke(capsys, tmp_path, "list_runs", params)
    assert code == 1
    assert result["ok"] is False
