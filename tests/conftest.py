from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import socket
import pytest


@pytest.fixture
def public_example_dns(monkeypatch):
    """Resolve only the public fixture hosts used by HTTP-mocked unit tests.

    Keep URL validation active, and leave the dedicated SSRF suite untouched.
    Unexpected real hostname lookups fail rather than accessing the network.
    """
    def resolve(host, port, *args, **kwargs):
        assert host in {"example.com", "new-url.com"}, f"Unexpected DNS lookup in HTTP-mocked test: {host}"
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port))]
    monkeypatch.setattr(socket, "getaddrinfo", resolve)
