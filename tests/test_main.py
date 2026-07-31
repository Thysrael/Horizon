from pathlib import Path
from types import SimpleNamespace

import pytest

from src import main as main_module


def test_missing_custom_config_reports_requested_path(monkeypatch, tmp_path):
    config_path = tmp_path / "custom" / "horizon.json"

    class MissingConfigStorage:
        def __init__(self, data_dir, config_path):
            self.config_path = Path(config_path)

        def load_config(self):
            raise FileNotFoundError

    output = []
    monkeypatch.setattr(main_module, "StorageManager", MissingConfigStorage)
    monkeypatch.setattr(
        main_module,
        "console",
        SimpleNamespace(
            print=lambda *args, **kwargs: output.append(" ".join(map(str, args)))
        ),
    )
    monkeypatch.setattr("sys.argv", ["horizon", "--config", str(config_path)])

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    rendered = "\n".join(output)
    assert exc_info.value.code == 1
    assert str(config_path) in rendered
    assert "horizon-wizard" not in rendered
