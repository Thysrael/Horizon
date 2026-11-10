import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src import main as cli
from src.collection_window import collection_hours
from src.mcp.errors import HorizonMcpError
from src.mcp.service import HorizonPipelineService
from src.models import CollectionConfig
from src.orchestrator import HorizonOrchestrator


@pytest.mark.parametrize("hours", [0, -1, True])
def test_boundary_rejects_nonpositive_collection_windows(hours):
    with pytest.raises(ValueError, match="hours must be greater than 0"):
        collection_hours(hours)


def test_boundary_accepts_positive_collection_windows():
    assert collection_hours(1) == 1
    assert collection_hours(24, None) == 24
    assert collection_hours(24, 3) == 3


def test_config_stores_a_nonpositive_window_without_checking():
    assert CollectionConfig(time_window_hours=0).time_window_hours == 0
    assert CollectionConfig(time_window_hours=-1).time_window_hours == -1


@pytest.mark.parametrize("hours", ["0", "-1"])
def test_cli_rejects_nonpositive_hours_at_the_boundary(hours, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["horizon", "--hours", hours])
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(cli, "configure_logging", lambda *args, **kwargs: None)
    config = SimpleNamespace(
        display=SimpleNamespace(icon_style="ascii"),
        ai=SimpleNamespace(provider="none"),
        collection=SimpleNamespace(time_window_hours=24),
    )
    monkeypatch.setattr(
        cli,
        "StorageManager",
        lambda *args, **kwargs: SimpleNamespace(load_config=lambda: config, config_path=Path("x")),
    )
    started = []
    monkeypatch.setattr(cli, "HorizonOrchestrator", lambda *args, **kwargs: started.append(True))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert started == []
    assert "hours must be greater than 0" in capsys.readouterr().err


def test_cli_rejects_a_nonpositive_configured_window(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["horizon"])
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(cli, "configure_logging", lambda *args, **kwargs: None)
    config = SimpleNamespace(
        display=SimpleNamespace(icon_style="ascii"),
        ai=SimpleNamespace(provider="none"),
        collection=SimpleNamespace(time_window_hours=0),
    )
    monkeypatch.setattr(
        cli,
        "StorageManager",
        lambda *args, **kwargs: SimpleNamespace(load_config=lambda: config, config_path=Path("x")),
    )
    started = []
    monkeypatch.setattr(cli, "HorizonOrchestrator", lambda *args, **kwargs: started.append(True))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert started == []


@pytest.mark.parametrize("hours", [0, -1])
def test_mcp_fetch_routes_nonpositive_hours_through_boundary(hours, tmp_path):
    service = HorizonPipelineService(runs_root=tmp_path)
    with pytest.raises(HorizonMcpError, match="hours must be greater than 0") as exc:
        asyncio.run(service.fetch_items(hours=hours))
    assert exc.value.code == "HZ_INVALID_INPUT"


def test_orchestrator_uses_the_resolved_window_without_checking_again():
    orchestrator = object.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(collection=SimpleNamespace(time_window_hours=0))
    since = orchestrator._determine_time_window(3)
    delta = datetime.now(timezone.utc) - since
    assert timedelta(hours=3) - timedelta(seconds=2) <= delta <= timedelta(hours=3) + timedelta(seconds=2)
    # A stored 0 is used as given. The boundary already ran before this call.
    since = orchestrator._determine_time_window(None)
    delta = datetime.now(timezone.utc) - since
    assert delta <= timedelta(seconds=2)
