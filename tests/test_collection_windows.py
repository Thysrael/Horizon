import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src import main as cli
from src.collection_window import require_positive_hours
from src.mcp.errors import HorizonMcpError
from src.mcp.service import HorizonPipelineService
from src.models import CollectionConfig
from src.orchestrator import HorizonOrchestrator


@pytest.mark.parametrize("hours", [0, -1, True])
def test_boundary_rejects_nonpositive_collection_windows(hours):
    with pytest.raises(ValueError, match="hours must be greater than 0"):
        require_positive_hours(hours)


def test_boundary_accepts_positive_collection_windows():
    assert require_positive_hours(1) == 1
    assert require_positive_hours(24) == 24


@pytest.mark.parametrize("hours", [0, -1])
def test_config_routes_nonpositive_windows_through_boundary(hours):
    with pytest.raises(ValidationError, match="hours must be greater than 0"):
        CollectionConfig(time_window_hours=hours)


@pytest.mark.parametrize("hours", ["0", "-1"])
def test_cli_rejects_nonpositive_hours_before_loading_workspace(hours, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["horizon", "--hours", hours])
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(cli, "configure_logging", lambda *args, **kwargs: None)
    loaded = []
    monkeypatch.setattr(cli, "StorageManager", lambda *args, **kwargs: loaded.append(True))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert loaded == []
    assert "hours must be greater than 0" in capsys.readouterr().err


@pytest.mark.parametrize("hours", [0, -1])
def test_mcp_fetch_routes_nonpositive_hours_through_boundary(hours, tmp_path):
    service = HorizonPipelineService(runs_root=tmp_path)
    with pytest.raises(HorizonMcpError, match="hours must be greater than 0") as exc:
        asyncio.run(service.fetch_items(hours=hours))
    assert exc.value.code == "HZ_INVALID_INPUT"


def test_orchestrator_uses_validated_override_without_checking_again():
    orchestrator = object.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(collection=CollectionConfig(time_window_hours=24))
    since = orchestrator._determine_time_window(require_positive_hours(3))
    delta = datetime.now(timezone.utc) - since
    assert timedelta(hours=3) - timedelta(seconds=2) <= delta <= timedelta(hours=3) + timedelta(seconds=2)


def test_orchestrator_uses_configured_window_when_override_is_absent():
    orchestrator = object.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(collection=CollectionConfig(time_window_hours=5))
    since = orchestrator._determine_time_window(None)
    delta = datetime.now(timezone.utc) - since
    assert timedelta(hours=5) - timedelta(seconds=2) <= delta <= timedelta(hours=5) + timedelta(seconds=2)
