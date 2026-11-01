"""Official Sign in with ChatGPT for local and self-hosted Horizon installations."""

from __future__ import annotations

import base64
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
import time
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlsplit
import uuid
import webbrowser

from filelock import FileLock
import httpx
import jwt

from .errors import AIProviderUnavailableError


ISSUER = "https://auth.openai.com"
RESOURCE = "https://api.openai.com/v1"
AUTHORIZE_URL = f"{ISSUER}/api/accounts/authorize"
TOKEN_URL = f"{ISSUER}/api/accounts/oauth/token"
DISCOVERY_URL = f"{ISSUER}/.well-known/openid-configuration"
PLAN_SCOPE = "chatgpt.tokens.use.direct"
SCOPES = f"openid profile email offline_access resource.invoke {PLAN_SCOPE}"
MANAGE_USAGE_URL = "https://chatgpt.com/settings/usage"
_TOKEN_FIELDS = ("access_token", "refresh_token", "id_token", "expires_at")
_INVALID_REFRESH = {
    "invalid_grant", "invalid_refresh_token", "token_expired",
    "refresh_token_expired", "refresh_token_invalidated", "refresh_token_reused",
}


def auth_directory() -> Path:
    override = os.environ.get("HORIZON_CHATGPT_AUTH_DIR")
    if override:
        return Path(override).expanduser()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return config_home / "horizon" / "chatgpt"


def _atomic_json(path: Path, data: dict) -> None:
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _read_json(path: Path, default: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError
        return value
    except FileNotFoundError:
        return default
    except (ValueError, UnicodeError):
        raise AIProviderUnavailableError(f"Invalid ChatGPT state file: {path}") from None


def _safe_code(value: Any) -> str:
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,100}", value) else "unknown_error"


def _json_object(response: httpx.Response) -> dict:
    try:
        data = response.json()
        if isinstance(data, dict):
            return data
    except ValueError:
        pass
    raise RuntimeError("Invalid JSON response from the ChatGPT service.") from None


def api_error(body: Any, status: int | None = None, request_id: str | None = None) -> RuntimeError:
    """Expose actionable codes without echoing response text or credentials."""
    error = body.get("error", body) if isinstance(body, dict) else {}
    code = _safe_code(error.get("code") if isinstance(error, dict) else None)
    if code == "subscription_sharing_usage_limit_exceeded":
        message = f"ChatGPT plan usage limit reached. Manage usage: {MANAGE_USAGE_URL}"
        terminal = True
    else:
        terminal = status in {400, 401, 403, 404, 422} or code in {
            "subscription_sharing_user_not_eligible", "subscription_sharing_unsupported_capability",
            "subscription_sharing_route_not_supported", "subscription_sharing_invalid_user",
            "chatpass_v2_scope_not_authorized", "chatpass_v2_invalid_authorization_context",
        }
        message = "ChatGPT request failed"
        if code == "subscription_sharing_user_not_eligible":
            message += "; plan usage is unavailable for this account, workspace, or policy"
        elif status in {401, 403} or code in {
            "subscription_sharing_invalid_user", "chatpass_v2_scope_not_authorized",
            "chatpass_v2_invalid_authorization_context",
        }:
            message += "; check the selected account and permissions with horizon-chatgpt status"
    details = [code]
    param = error.get("param") if isinstance(error, dict) else None
    if isinstance(param, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.\[\]-]{0,100}", param):
        details.append(f"parameter {param}")
    if status is not None:
        details.append(f"HTTP {status}")
    if request_id and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id):
        details.append(f"request {request_id}")
    cls = AIProviderUnavailableError if terminal else RuntimeError
    return cls(f"{message} ({', '.join(details)})")


class ChatGPTAuth:
    """Persist registrations separately and serialize rotating-token refreshes."""

    def __init__(self, directory: Path | None = None, *, http_client: httpx.Client | None = None):
        self.directory = directory if directory is not None else auth_directory()
        self.credentials_path = self.directory / "credentials.json"
        self.host_path = self.directory / "host.json"
        self.http_client = http_client

    @contextmanager
    def _locked(self):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Separate lock instances also serialize threads using the same auth object.
        with FileLock(self.directory / ".lock", timeout=60, mode=0o600):
            state = _read_json(self.credentials_path, {"accounts": {}, "active": None})
            if not isinstance(state.get("accounts"), dict):
                raise AIProviderUnavailableError("Invalid ChatGPT account store.")
            yield state

    @contextmanager
    def _http(self):
        try:
            if self.http_client is not None:
                yield self.http_client
            else:
                with httpx.Client(timeout=20, follow_redirects=False) as client:
                    yield client
        except httpx.HTTPError:
            raise RuntimeError("Could not reach the ChatGPT service; saved credentials were retained.") from None

    @staticmethod
    def _account(state: dict, account: str | None) -> dict:
        key = account or state.get("active")
        record = state["accounts"].get(key)
        if not isinstance(record, dict):
            raise AIProviderUnavailableError("No ChatGPT account selected. Run horizon-chatgpt login.")
        return record

    def _host_id(self) -> str:
        host = _read_json(self.host_path, {})
        if "ext_agent_host_id" not in host:
            host = {"ext_agent_host_id": f"urn:uuid:{uuid.uuid4()}"}
            _atomic_json(self.host_path, host)
        if not isinstance(host["ext_agent_host_id"], str) or not host["ext_agent_host_id"]:
            raise AIProviderUnavailableError("Invalid ChatGPT host ID.")
        return host["ext_agent_host_id"]

    def initialize(self) -> dict[str, str]:
        """Create this runtime's identity before importing a VM credential session."""
        with self._locked():
            return {"directory": str(self.directory), "ext_agent_host_id": self._host_id()}

    @staticmethod
    def _public(record: dict, active: str | None) -> dict:
        connected = bool(record.get("access_token") and record.get("refresh_token"))
        return {
            "client_id": record.get("client_id"),
            "email": record.get("email"),
            "active": record.get("client_id") == active,
            "connected": connected,
            "plan_usage": connected and PLAN_SCOPE in record.get("scopes", []),
            "expires_at": record.get("expires_at"),
        }

    def status(self, account: str | None = None) -> dict:
        with self._locked() as state:
            if not account and not state.get("active"):
                return {"client_id": None, "connected": False, "plan_usage": False}
            return self._public(self._account(state, account), state.get("active"))

    def accounts(self) -> list[dict]:
        with self._locked() as state:
            return [self._public(record, state.get("active")) for record in state["accounts"].values()]

    def select(self, account: str) -> None:
        with self._locked() as state:
            self._account(state, account)
            state["active"] = account
            _atomic_json(self.credentials_path, state)

    @staticmethod
    def _discovery(client: httpx.Client) -> dict:
        response = client.get(DISCOVERY_URL)
        response.raise_for_status()
        metadata = _json_object(response)
        if metadata.get("issuer") != ISSUER:
            raise AIProviderUnavailableError("Unexpected ChatGPT authorization issuer.")
        return metadata

    @staticmethod
    def _auth_endpoint(metadata: dict, name: str) -> str:
        endpoint = metadata.get(name, "")
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or parsed.netloc != "auth.openai.com":
            raise AIProviderUnavailableError("Unexpected ChatGPT authorization endpoint.")
        return endpoint

    def _identity(self, client: httpx.Client, token: str, client_id: str, nonce: str | None = None) -> dict:
        metadata = self._discovery(client)
        response = client.get(self._auth_endpoint(metadata, "jwks_uri"))
        response.raise_for_status()
        try:
            header = jwt.get_unverified_header(token)
            key = next(key for key in response.json()["keys"] if key.get("kid") == header.get("kid"))
            claims = jwt.decode(
                token, jwt.PyJWK.from_dict(key, algorithm="RS256").key,
                algorithms=["RS256"], audience=client_id, issuer=ISSUER,
                options={"require": ["exp", "iss", "sub", "aud"]},
            )
            if not isinstance(claims["sub"], str) or not claims["sub"]:
                raise ValueError
            if claims.get("azp", client_id) != client_id or (
                isinstance(claims["aud"], list) and len(claims["aud"]) > 1 and claims.get("azp") != client_id
            ):
                raise ValueError
            if nonce is not None and (
                not isinstance(claims.get("nonce"), str)
                or not secrets.compare_digest(claims["nonce"], nonce)
            ):
                raise ValueError
            return {"issuer": claims["iss"], "subject": claims["sub"], "email": claims.get("email")}
        except (jwt.PyJWTError, ValueError, KeyError, StopIteration, TypeError, AttributeError):
            raise AIProviderUnavailableError("ChatGPT ID-token validation failed; credentials were not replaced.") from None

    @staticmethod
    def _token_update(data: dict, previous: dict) -> dict:
        try:
            if data.get("token_type", "").lower() != "bearer":
                raise ValueError
            for name in ("access_token", "refresh_token"):
                if not isinstance(data.get(name), str) or not data[name]:
                    raise ValueError
            lifetime = float(data["expires_in"])
            if not 0 < lifetime < float("inf"):
                raise ValueError
            scope = data.get("scope")
            if scope is not None and not isinstance(scope, str):
                raise ValueError
            return {
                **previous,
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
                "id_token": data.get("id_token") or previous.get("id_token"),
                "scopes": scope.split() if scope is not None else previous.get("scopes", []),
                "expires_at": time.time() + lifetime,
            }
        except (ValueError, TypeError, KeyError, AttributeError):
            raise AIProviderUnavailableError("Invalid ChatGPT token response; credentials were not replaced.") from None

    def sign_in(
        self, account: str | None = None, *, new_account: bool = False,
        enable_plan: bool = False, timeout: float = 300,
        open_browser: Callable[[str], Any] = webbrowser.open,
        show_url: Callable[[str], Any] = print,
    ) -> dict:
        if new_account and account:
            raise ValueError("Choose either a saved account or a new account.")
        with self._locked() as state:
            host_id = self._host_id()
            previous = {} if new_account or not (account or state.get("active")) else dict(self._account(state, account))
        client_id = previous.get("client_id", "dynamic_agent_client")
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state_value, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        received = threading.Event()
        callback_lock = threading.Lock()
        callback: dict[str, str] = {}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # Callback URLs contain authorization codes.

            def do_GET(self):
                parsed = urlsplit(self.path)
                params = parse_qs(parsed.query, keep_blank_values=True)
                valid_state = params.get("state", [])
                if parsed.path != "/auth/callback":
                    self.send_error(404)
                    return
                if len(valid_state) != 1 or not secrets.compare_digest(valid_state[0].encode(), state_value.encode()):
                    self.send_error(400, "Invalid authorization state")
                    return
                with callback_lock:
                    if received.is_set():
                        self.send_error(409)
                        return
                    if any(len(values) != 1 for values in params.values()):
                        callback["error"] = "invalid_callback"
                    else:
                        callback.update({key: values[0] for key, values in params.items()})
                    received.set()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Authorization received. Return to Horizon to see the result.")

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.timeout = 1
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        redirect_uri = f"http://127.0.0.1:{server.server_port}/auth/callback"
        params = {
            "client_id": client_id, "ext_agent_host_id": host_id,
            "response_type": "code", "redirect_uri": redirect_uri,
            "scope": SCOPES, "resource": RESOURCE, "state": state_value,
            "nonce": nonce, "code_challenge_method": "S256", "code_challenge": challenge,
        }
        if client_id == "dynamic_agent_client":
            params["agent_name_hint"] = "Horizon"
        if enable_plan:
            params["prompt"] = "consent"
        # Login hints are optional. Keeping tokens out of this URL also makes the
        # manual-browser flow safe to display in a terminal.
        url = f"{AUTHORIZE_URL}?{urlencode(params)}"
        try:
            if not open_browser(url):
                show_url(url)
            if not received.wait(timeout):
                raise AIProviderUnavailableError("ChatGPT sign-in timed out. Run horizon-chatgpt login again.")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        if callback.get("error"):
            raise AIProviderUnavailableError("ChatGPT sign-in was declined or the callback was invalid.")
        issued = callback.get("client_id", client_id)
        if not callback.get("code") or not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", issued) or issued == "dynamic_agent_client" or (
            client_id != "dynamic_agent_client" and issued != client_id
        ):
            raise AIProviderUnavailableError("Invalid ChatGPT client registration callback.")

        with self._locked() as state, self._http() as client:
            # Retain a newly issued registration even if its code exchange fails.
            record = state["accounts"].setdefault(issued, {"client_id": issued})
            _atomic_json(self.credentials_path, state)
            response = client.post(TOKEN_URL, data={
                "grant_type": "authorization_code", "client_id": issued,
                "code": callback["code"], "code_verifier": verifier,
                "redirect_uri": redirect_uri, "resource": RESOURCE,
            })
            if response.status_code != 200:
                raise AIProviderUnavailableError(
                    f"ChatGPT code exchange failed (HTTP {response.status_code}). "
                    f"Reconnect with horizon-chatgpt login --account {issued}."
                )
            data = _json_object(response)
            identity = self._identity(client, data.get("id_token", ""), issued, nonce)
            if record.get("subject") and (
                identity["subject"] != record["subject"] or identity["issuer"] != record["issuer"]
            ):
                raise AIProviderUnavailableError("ChatGPT account identity changed; saved credentials were not replaced.")
            record = self._token_update(data, {"client_id": issued, **identity})
            state["accounts"][issued] = record
            state["active"] = issued
            _atomic_json(self.credentials_path, state)
            return self._public(record, issued)

    def access_token(self, account: str | None = None) -> str:
        with self._locked() as state:
            record = self._account(state, account)
            if not record.get("access_token") or not record.get("refresh_token"):
                raise AIProviderUnavailableError("ChatGPT is signed out. Run horizon-chatgpt login.")
            if PLAN_SCOPE not in record.get("scopes", []):
                raise AIProviderUnavailableError("ChatGPT plan usage is not enabled. Run horizon-chatgpt login --enable-plan.")
            if record.get("expires_at", 0) > time.time() + 60:
                return record["access_token"]
            with self._http() as client:
                response = client.post(TOKEN_URL, data={
                    "grant_type": "refresh_token", "client_id": record["client_id"],
                    "refresh_token": record["refresh_token"], "resource": RESOURCE,
                })
                if response.status_code != 200:
                    try:
                        code = response.json().get("error")
                    except (ValueError, AttributeError):
                        code = None
                    if isinstance(code, str) and code in _INVALID_REFRESH:
                        for field in _TOKEN_FIELDS:
                            record.pop(field, None)
                        _atomic_json(self.credentials_path, state)
                        raise AIProviderUnavailableError("ChatGPT session expired or was revoked. Run horizon-chatgpt login.")
                    if code == "invalid_client":
                        raise AIProviderUnavailableError("Invalid ChatGPT client registration; reconnect the saved account.")
                    raise RuntimeError(f"ChatGPT token refresh failed (HTTP {response.status_code}); credentials retained.")
                data = _json_object(response)
                if data.get("id_token"):
                    identity = self._identity(client, data["id_token"], record["client_id"])
                    if identity["subject"] != record["subject"] or identity["issuer"] != record["issuer"]:
                        raise AIProviderUnavailableError("ChatGPT refresh identity mismatch; credentials retained.")
                updated = self._token_update(data, record)
            state["accounts"][record["client_id"]] = updated
            _atomic_json(self.credentials_path, state)
            if PLAN_SCOPE not in updated["scopes"]:
                raise AIProviderUnavailableError("ChatGPT plan permission was removed. Run horizon-chatgpt login --enable-plan.")
            return updated["access_token"]

    def models(self, account: str | None = None) -> list[dict[str, str]]:
        token = self.access_token(account)
        with self._http() as client:
            response = client.get(f"{RESOURCE}/models", headers={"Authorization": f"Bearer {token}"})
            if response.status_code != 200:
                try:
                    body = response.json()
                except ValueError:
                    body = {}
                raise api_error(body, response.status_code, response.headers.get("x-request-id"))
            data = _json_object(response)
        catalog = data.get("models")
        if not isinstance(catalog, list):
            raise RuntimeError("Invalid ChatGPT model catalog.")
        return [
            {"slug": item["slug"], "display_name": item.get("display_name") or item["slug"]}
            for item in catalog
            if isinstance(item, dict) and item.get("visibility") == "list"
            and isinstance(item.get("slug"), str) and item["slug"]
        ]

    def sign_out(self, account: str | None = None) -> bool:
        """Return whether remote revocation was confirmed; always clear local tokens."""
        with self._locked() as state:
            record = self._account(state, account)
            confirmed = not record.get("refresh_token")
            try:
                if not confirmed:
                    with self._http() as client:
                        endpoint = self._auth_endpoint(self._discovery(client), "revocation_endpoint")
                        for attempt in range(3):
                            try:
                                response = client.post(endpoint, data={
                                    "token": record["refresh_token"], "token_type_hint": "refresh_token",
                                    "client_id": record["client_id"],
                                })
                                confirmed = response.status_code == 200
                                if response.status_code < 500:
                                    break
                            except httpx.HTTPError:
                                pass
                            if attempt < 2:
                                time.sleep(0.25 * 2 ** attempt)
            except (RuntimeError, ValueError):
                confirmed = False
            finally:
                for field in _TOKEN_FIELDS:
                    record.pop(field, None)
                _atomic_json(self.credentials_path, state)
            return confirmed
