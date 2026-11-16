"""SSRF-safe HTTP URL validation and request execution.

Publicness is decided from the system resolver. Public DNS-over-HTTPS is a
fallback, not the default: it runs only when every non-public system answer
falls inside the proxy fake-IP range (``198.18.0.0/15`` by default). A proxy
that maps public names into that range would otherwise reject real articles,
while a genuine private answer still fails without a public lookup.

The DoH address is never a connection target and never becomes an allowlist:
if public DNS returns a non-public address, the URL is still rejected.
``safe_request`` keeps calling httpx with the original hostname so the system
resolver and proxy still carry the fetch.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx
# Bound at import so the fallback lookup stays on a fresh system HTTP client.
# A caller-supplied client, or a patch of httpx.AsyncClient, must not reroute
# this DNS check or pin its answers onto the article fetch.
from httpx import AsyncClient as _DoHAsyncClient


class UnsafeURLError(ValueError):
    """Raised when a URL may target a non-public network resource."""


# Cloudflare first. Google is used only when Cloudflare cannot return a
# definitive A and AAAA answer. Both speak the DNS-JSON format.
_DOH_ENDPOINTS = (
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/resolve",
)
_DOH_ACCEPT = "application/dns-json"
_DOH_TIMEOUT_SECONDS = 5.0
_DOH_QUERY_TYPES = ("A", "AAAA")
_RR_TYPE_CODES = {"A": 1, "AAAA": 28}
_DNS_NOERROR = 0
_DNS_NXDOMAIN = 3
_DEFINITIVE_DNS_STATUSES = {_DNS_NOERROR, _DNS_NXDOMAIN}

# Ranges an egress proxy uses to stand in for public names. They are not
# public addresses, but an answer entirely inside them says nothing about the
# real destination, so the check asks public DNS instead of rejecting.
_FAKE_IP_NETWORKS = (ipaddress.ip_network("198.18.0.0/15"),)


def validate_http_url(url: str) -> str:
    """Validate the non-network portions of an HTTP(S) URL."""
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise UnsafeURLError(f"Invalid URL: {exc}") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise UnsafeURLError("URL must use http or https")
    if not parsed.hostname:
        raise UnsafeURLError("URL has no hostname")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeURLError("URL must not contain embedded credentials")
    if port is not None and not 1 <= port <= 65535:
        raise UnsafeURLError("URL port is out of range")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise UnsafeURLError("localhost destinations are not allowed")
    return url


class _DoHTransportError(Exception):
    """A DNS-over-HTTPS endpoint could not return a definitive answer."""


@dataclass(frozen=True)
class _DoHResult:
    status: int
    addresses: set[str]


def _parse_ip(address: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Parse a resolver answer, ignoring any IPv6 zone identifier."""

    try:
        return ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError as exc:
        raise UnsafeURLError(f"Resolver returned an invalid address: {address}") from exc


def _is_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip.is_global
        and not ip.is_loopback
        and not ip.is_private
        and not ip.is_link_local
        and not ip.is_multicast
        and not ip.is_reserved
        and not ip.is_unspecified
    )


def _is_fake_ip(address: str) -> bool:
    """Say whether one answer sits in a proxy fake-IP range."""

    try:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError:
        return False
    return any(ip in network for network in _FAKE_IP_NETWORKS if network.version == ip.version)


def _require_public_addresses(addresses: set[str], hostname: str) -> None:
    """Reject any non-public address in the answer."""

    for address in addresses:
        if not _is_public_ip(_parse_ip(address)):
            raise UnsafeURLError(f"Destination resolves to a non-public address: {address}")


def _is_ip_literal(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return True


async def _resolve_hostname(hostname: str, port: int) -> set[str]:
    """Return the system resolver's answers for ``hostname``.

    These are the addresses the HTTP client will actually use, because the
    request keeps the original hostname.
    """

    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            results = await asyncio.to_thread(
                socket.getaddrinfo,
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise UnsafeURLError(f"Could not resolve hostname: {hostname}") from exc
        return {str(result[4][0]) for result in results}
    return {str(literal)}


async def _resolve_via_public_doh(hostname: str) -> set[str]:
    """Resolve A and AAAA for ``hostname`` through public DNS-over-HTTPS.

    Only called when the system answer is a proxy fake-IP. The client is a
    fresh httpx client on the system HTTP path, including environment
    proxies. It is not the caller's fetch client, and the addresses it learns
    are not substituted into later requests.
    """

    async with _DoHAsyncClient(
        timeout=_DOH_TIMEOUT_SECONDS,
        follow_redirects=False,
        trust_env=True,
    ) as client:
        last_error: Exception | None = None
        for endpoint in _DOH_ENDPOINTS:
            try:
                addresses = await _addresses_from_doh_endpoint(client, endpoint, hostname)
            except _DoHTransportError as exc:
                last_error = exc
                continue
            if not addresses:
                raise UnsafeURLError(f"Hostname resolved to no addresses: {hostname}")
            return addresses
    raise UnsafeURLError(f"Could not resolve hostname: {hostname}") from last_error


async def _addresses_from_doh_endpoint(
    client: httpx.AsyncClient,
    endpoint: str,
    hostname: str,
) -> set[str]:
    """Return every A and AAAA address from one resolver, or fail the endpoint.

    A partial answer is not accepted. A public A record must not hide a
    private AAAA record, and a failed query must not look like "no address".
    """

    results = await asyncio.gather(
        *(_query_doh(client, endpoint, hostname, rrtype) for rrtype in _DOH_QUERY_TYPES),
        return_exceptions=True,
    )
    answers: list[_DoHResult] = []
    failures: list[Exception] = []
    for result in results:
        if isinstance(result, _DoHResult):
            answers.append(result)
        elif isinstance(result, Exception):
            failures.append(result)
        else:
            raise result

    if failures or len(answers) != len(results):
        cause = failures[0] if failures else None
        raise _DoHTransportError(f"Could not query {endpoint} for {hostname}") from cause
    if any(answer.status not in _DEFINITIVE_DNS_STATUSES for answer in answers):
        raise _DoHTransportError(f"DNS resolver failure for {hostname} via {endpoint}")

    addresses: set[str] = set()
    for answer in answers:
        if answer.status == _DNS_NOERROR:
            addresses.update(answer.addresses)
    return addresses


async def _query_doh(
    client: httpx.AsyncClient,
    endpoint: str,
    hostname: str,
    rrtype: str,
) -> _DoHResult:
    try:
        response = await client.get(
            endpoint,
            params={"name": hostname, "type": rrtype},
            headers={"Accept": _DOH_ACCEPT},
        )
    except httpx.HTTPError as exc:
        raise _DoHTransportError(str(exc)) from exc

    if response.status_code != 200:
        raise _DoHTransportError(f"HTTP {response.status_code} from {endpoint}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise _DoHTransportError(f"Invalid DNS JSON from {endpoint}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("Status"), int):
        raise _DoHTransportError(f"Unexpected DNS JSON from {endpoint}")

    raw_answers = payload.get("Answer", [])
    if raw_answers is None:
        raw_answers = []
    if not isinstance(raw_answers, list):
        raise _DoHTransportError(f"Unexpected DNS answers from {endpoint}")

    type_code = _RR_TYPE_CODES[rrtype]
    addresses: set[str] = set()
    if payload["Status"] == _DNS_NOERROR:
        for answer in raw_answers:
            if not isinstance(answer, dict) or answer.get("type") != type_code:
                continue
            data = answer.get("data")
            if isinstance(data, str) and data.strip():
                addresses.add(data.strip())
    return _DoHResult(status=payload["Status"], addresses=addresses)


async def validate_public_http_url(url: str) -> str:
    """Require the destination to be globally routable.

    The system resolver decides first. Public DoH is consulted only when every
    non-public answer is a proxy fake-IP, so a normal public lookup and every
    genuine private answer both settle without an outbound DNS query.
    """

    validate_http_url(url)
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").rstrip(".")
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)

    if _is_ip_literal(hostname):
        _require_public_addresses({hostname}, hostname)
        return url

    addresses = await _resolve_hostname(hostname, port)
    if not addresses:
        raise UnsafeURLError(f"Hostname resolved to no addresses: {hostname}")

    blocked = {address for address in addresses if not _is_public_ip(_parse_ip(address))}
    if not blocked:
        return url
    if not all(_is_fake_ip(address) for address in blocked):
        _require_public_addresses(blocked, hostname)

    public_addresses = await _resolve_via_public_doh(hostname)
    _require_public_addresses(public_addresses, hostname)
    return url


async def safe_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_redirects: int = 10,
    **kwargs,
) -> httpx.Response:
    """Make a request after validating the initial URL and each redirect hop."""
    current_method = method.upper()
    current_url = url
    current_kwargs = kwargs

    for redirect_count in range(max_redirects + 1):
        await validate_public_http_url(current_url)
        request = getattr(client, current_method.lower())
        response = await request(current_url, follow_redirects=False, **current_kwargs)
        if response.status_code not in {301, 302, 303, 307, 308}:
            return response

        location = response.headers.get("location")
        if not location:
            return response
        if redirect_count == max_redirects:
            raise UnsafeURLError("Too many redirects")

        current_url = urljoin(current_url, location)
        if response.status_code == 303 or (
            response.status_code in {301, 302} and current_method == "POST"
        ):
            current_method = "GET"
            current_kwargs = {
                key: value
                for key, value in current_kwargs.items()
                if key not in {"content", "data", "files", "json"}
            }

    raise UnsafeURLError("Too many redirects")
