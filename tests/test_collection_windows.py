from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src import main as cli
from src.models import CollectionConfig
from src.orchestrator import HorizonOrchestrator


@pytest.mark.parametrize("hours", [0, -1])
def test_config_rejects_nonpositive_collection_windows(hours):
    with pytest.raises(ValidationError):
        CollectionConfig(time_window_hours=hours)


@pytest.mark.parametrize("hours", [0, -1])
def test_programmatic_run_rejects_nonpositive_overrides(hours):
    orchestrator = object.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(collection=CollectionConfig())
    with pytest.raises(ValueError, match="greater than 0"):
        orchestrator._determine_time_window(hours)


@pytest.mark.parametrize("hours", ["0", "-1"])
def test_cli_rejects_nonpositive_hours_before_loading_workspace(hours, monkeypatch):
    monkeypatch.setattr("sys.argv", ["horizon", "--hours", hours])
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(cli, "configure_logging", lambda *args, **kwargs: None)
    loaded = []
    monkeypatch.setattr(cli, "StorageManager", lambda *args, **kwargs: loaded.append(True))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert loaded == []
