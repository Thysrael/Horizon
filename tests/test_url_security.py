from __future__ import annotations

import asyncio
import socket
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.url_security import UnsafeURLError, safe_request, validate_public_http_url


def _run(coro):
    return asyncio.run(coro)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://169.254.169.254/",
        "http://0.0.0.0/",
        "http://224.0.0.1/",
        "http://192.0.2.1/",
        "http://[::1]/",
        "http://[fc00::1]/",
        "http://[fe80::1]/",
        "http://[::]/",
        "http://[ff02::1]/",
        "http://[2001:db8::1]/",
        "http://198.18.0.1/",
    ],
)
def test_rejects_non_public_ip_destinations(url):
    with pytest.raises(UnsafeURLError, match="non-public"):
        _run(validate_public_http_url(url))


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/",
        "https://service.localhost./hook",
        "ftp://example.com/file",
        "https://user:secret@example.com/hook",
    ],
)
def test_rejects_unsafe_url_forms(url):
    with pytest.raises(UnsafeURLError):
        _run(validate_public_http_url(url))


def test_rejects_hostname_when_any_resolved_ip_is_private():
    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(return_value={"93.184.216.34", "10.0.0.2"}),
    ):
        with pytest.raises(UnsafeURLError, match="10.0.0.2"):
            _run(validate_public_http_url("https://example.com/hook"))


def test_accepts_public_ipv4_and_ipv6_dns_answers():
    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(return_value={"93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946"}),
    ):
        assert _run(validate_public_http_url("https://example.com/hook"))


def test_redirect_is_validated_before_second_request():
    redirect = MagicMock(
        status_code=302,
        headers={"location": "http://127.0.0.1/admin"},
    )
    client = MagicMock()
    client.get = AsyncMock(return_value=redirect)

    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(side_effect=[{"93.184.216.34"}, {"127.0.0.1"}]),
    ):
        with pytest.raises(UnsafeURLError, match="non-public"):
            _run(safe_request(client, "GET", "https://example.com/start"))

    client.get.assert_awaited_once_with(
        "https://example.com/start", follow_redirects=False
    )


def test_public_relative_redirect_is_followed():
    redirect = MagicMock(status_code=301, headers={"location": "/next"})
    success = MagicMock(status_code=200, headers={})
    client = MagicMock()
    client.get = AsyncMock(side_effect=[redirect, success])

    with patch(
        "src.url_security._resolve_hostname",
        new=AsyncMock(return_value={"93.184.216.34"}),
    ):
        result = _run(safe_request(client, "GET", "https://example.com/start"))

    assert result is success
    assert client.get.await_args_list[1].args == ("https://example.com/next",)
    assert client.get.await_args_list[1].kwargs == {"follow_redirects": False}


class _DoHResponse:
    def __init__(self, payload: dict):
        self.status_code = 200
        self._payload = payload

    def json(self):
        return self._payload


@contextmanager
def _mock_doh(answers: dict[str, list[str]], *, fail_hosts: tuple[str, ...] = ()):
    """Replace the DNS-over-HTTPS client. ``answers`` maps A/AAAA to IPs."""

    calls: list[dict] = []

    class _Client:
        def __init__(self, *_args, **kwargs):
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_exc):
            return False

        async def get(self, url, params=None, headers=None):
            calls.append({"url": url, "params": params, "headers": headers, "client": self})
            if any(host in url for host in fail_hosts):
                raise httpx.ConnectError("doh endpoint unavailable")
            rrtype = (params or {}).get("type")
            type_code = {"A": 1, "AAAA": 28}[rrtype]
            return _DoHResponse(
                {
                    "Status": 0,
                    "Answer": [
                        {
                            "name": (params or {}).get("name"),
                            "type": type_code,
                            "TTL": 60,
                            "data": ip,
                        }
                        for ip in answers.get(rrtype, [])
                    ],
                }
            )

    with patch("src.url_security._DoHAsyncClient", _Client):
        yield calls


@contextmanager
def _system_fake_ip(address: str = "198.18.0.1"):
    """Make the system resolver answer with a proxy fake-IP address."""

    def fake_getaddrinfo(_host, port, *_args, **_kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                (address, port),
            )
        ]

    with patch("socket.getaddrinfo", side_effect=fake_getaddrinfo):
        yield


def test_doh_public_answer_is_accepted():
    with _system_fake_ip(), _mock_doh(
        {
            "A": ["93.184.216.34"],
            "AAAA": ["2606:2800:220:1:248:1893:25c8:1946"],
        }
    ) as calls:
        assert _run(validate_public_http_url("https://example.com/hook")) == (
            "https://example.com/hook"
        )

    assert calls
    assert all(call["headers"]["Accept"] == "application/dns-json" for call in calls)
    assert all("cloudflare-dns.com" in call["url"] for call in calls)
    assert {call["params"]["type"] for call in calls} == {"A", "AAAA"}
    assert all(call["params"]["name"] == "example.com" for call in calls)
    assert all(call["client"].kwargs["follow_redirects"] is False for call in calls)


def test_doh_private_answer_is_rejected():
    with _system_fake_ip(), _mock_doh({"A": ["10.0.0.2"], "AAAA": []}):
        with pytest.raises(UnsafeURLError, match="non-public address: 10.0.0.2"):
            _run(validate_public_http_url("https://example.com/hook"))


def test_doh_private_aaaa_rejects_public_a():
    with _system_fake_ip(), _mock_doh({"A": ["93.184.216.34"], "AAAA": ["fc00::1"]}):
        with pytest.raises(UnsafeURLError, match="non-public address: fc00::1"):
            _run(validate_public_http_url("https://example.com/hook"))


def test_doh_benchmark_range_is_not_allowlisted():
    """198.18.0.0/15 is the box egress range and stays non-public."""

    with _system_fake_ip(), _mock_doh({"A": ["198.18.0.1"], "AAAA": []}):
        with pytest.raises(UnsafeURLError, match="non-public address: 198.18.0.1"):
            _run(validate_public_http_url("https://example.com/hook"))


def test_system_fake_ip_does_not_block_when_doh_is_public():
    """Box resolvers return 198.18.0.1; public DoH still allows the article.

    The fetch keeps the original hostname. The DoH address is not pinned.
    """

    response = MagicMock(status_code=200, headers={})
    client = MagicMock()
    client.get = AsyncMock(return_value=response)

    with _system_fake_ip(), _mock_doh({"A": ["93.184.216.34"], "AAAA": []}):
        assert _run(validate_public_http_url("https://example.com/article"))
        result = _run(safe_request(client, "GET", "https://example.com/article"))

    assert result is response
    client.get.assert_awaited_once_with(
        "https://example.com/article", follow_redirects=False
    )


def test_public_system_answer_does_not_query_public_dns():
    """The common path stays on the system resolver and never leaves the box."""

    def public_getaddrinfo(_host, port, *_args, **_kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", port),
            )
        ]

    with patch("socket.getaddrinfo", side_effect=public_getaddrinfo), _mock_doh(
        {"A": ["10.0.0.2"], "AAAA": []}
    ) as calls:
        assert _run(validate_public_http_url("https://example.com/hook")) == (
            "https://example.com/hook"
        )

    assert calls == []


def test_doh_falls_back_to_google_when_cloudflare_is_unreachable():
    with _system_fake_ip(), _mock_doh(
        {"A": ["93.184.216.34"], "AAAA": []},
        fail_hosts=("cloudflare-dns.com",),
    ) as calls:
        assert _run(validate_public_http_url("https://example.com/hook"))

    hosts = [call["url"] for call in calls]
    assert any("cloudflare-dns.com" in url for url in hosts)
    assert any("dns.google" in url for url in hosts)
