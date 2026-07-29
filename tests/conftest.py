from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def mock_public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep HTTP-mocking tests independent from the host DNS resolver."""

    async def resolve_as_public(_hostname: str, _port: int) -> set[str]:
        return {"93.184.216.34"}

    monkeypatch.setattr(
        "src.url_security._resolve_hostname",
        resolve_as_public,
    )
