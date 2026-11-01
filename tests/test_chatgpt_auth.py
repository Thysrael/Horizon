"""Offline OAuth integration: real loopback callbacks, JWT signatures, and storage."""

from concurrent.futures import ThreadPoolExecutor
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlsplit

from cryptography.hazmat.primitives.asymmetric import rsa
import httpx
import jwt
import pytest

from src.ai.chatgpt_auth import ChatGPTAuth, DISCOVERY_URL, ISSUER, PLAN_SCOPE, RESOURCE, TOKEN_URL
from src.ai.errors import AIProviderUnavailableError


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


class OAuthServer:
    def __init__(self, key):
        self.key = key
        self.signing_key = key
        self.pending = {}
        self.authorizations = []
        self.requests = []
        self.refreshes = 0
        self.refresh_error = None
        self.exchange_error = None
        self.revoke_status = 200
        self.scopes = f"openid email offline_access {PLAN_SCOPE}"
        self.claim_overrides = {}
        self.subject = "user-one"
        self.new_id = "oaiapp_one"
        self.callback_override = {}
        self.bad_state_first = False

    def browser(self, url):
        params = {key: values[0] for key, values in parse_qs(urlsplit(url).query).items()}
        self.pending = params
        self.authorizations.append(params)
        client_id = self.new_id if params["client_id"] == "dynamic_agent_client" else params["client_id"]
        callback = {"state": params["state"], "code": "authorization-secret", "client_id": client_id}
        callback.update(self.callback_override)
        if self.bad_state_first:
            response = httpx.get(
                params["redirect_uri"], params={**callback, "state": "unrelated-attempt"}, trust_env=False,
            )
            assert response.status_code == 400
        response = httpx.get(params["redirect_uri"], params=callback, trust_env=False)
        assert response.status_code == 200
        return True

    def handle(self, request):
        form = {key: value[0] for key, value in parse_qs(request.content.decode()).items()}
        self.requests.append((request, form))
        if str(request.url) == DISCOVERY_URL:
            return httpx.Response(200, json={
                "issuer": ISSUER, "jwks_uri": f"{ISSUER}/.well-known/jwks.json",
                "revocation_endpoint": f"{ISSUER}/api/accounts/oauth/revoke",
            })
        if request.url.path.endswith("jwks.json"):
            key = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key()))
            return httpx.Response(200, json={"keys": [{**key, "kid": "test-key", "alg": "RS256"}]})
        if request.url.path.endswith("/revoke"):
            return httpx.Response(self.revoke_status)
        if request.url.path == "/v1/models":
            assert request.headers["Authorization"].startswith("Bearer access-secret")
            return httpx.Response(200, json={"models": [
                {"slug": "plan-b", "display_name": "Model B", "visibility": "list"},
                {"slug": "hidden", "display_name": "Hidden", "visibility": "hide"},
                {"slug": "plan-a", "display_name": "Model A", "visibility": "list"},
            ]})
        assert str(request.url) == TOKEN_URL
        assert form["client_id"] != "dynamic_agent_client"
        assert form["resource"] == RESOURCE
        if form["grant_type"] == "refresh_token":
            self.refreshes += 1
            time.sleep(0.02)  # Make competing refreshes overlap if locking is broken.
            if self.refresh_error:
                status, code = self.refresh_error
                return httpx.Response(status, json={"error": code, "error_description": "refresh-secret"})
            assert form["refresh_token"] == "refresh-secret"
            assert "scope" not in form
            return httpx.Response(200, json={
                "access_token": "access-secret-refreshed", "refresh_token": "refresh-secret-rotated",
                "token_type": "Bearer", "expires_in": 3600,
            })
        if self.exchange_error:
            return httpx.Response(400, json={"error": self.exchange_error})
        assert form["redirect_uri"] == self.pending["redirect_uri"]
        challenge = base64.urlsafe_b64encode(hashlib.sha256(form["code_verifier"].encode()).digest()).rstrip(b"=").decode()
        assert challenge == self.pending["code_challenge"]
        claims = {
            "iss": ISSUER, "aud": form["client_id"], "sub": self.subject,
            "email": "reader@example.com", "exp": int(time.time()) + 3600,
            "nonce": self.pending["nonce"], **self.claim_overrides,
        }
        return httpx.Response(200, json={
            "access_token": "access-secret", "refresh_token": "refresh-secret",
            "id_token": jwt.encode(claims, self.signing_key, algorithm="RS256", headers={"kid": "test-key"}),
            "scope": self.scopes, "token_type": "Bearer", "expires_in": 3600,
        })


@pytest.fixture
def oauth(tmp_path, signing_key):
    server = OAuthServer(signing_key)
    with httpx.Client(transport=httpx.MockTransport(server.handle)) as client:
        auth = ChatGPTAuth(tmp_path / "auth", http_client=client)
        yield auth, server


def sign_in(auth, server, **kwargs):
    return auth.sign_in(open_browser=server.browser, timeout=2, **kwargs)


def expire(auth):
    with auth._locked() as state:
        state["accounts"][state["active"]]["expires_at"] = time.time() - 1
        # Tests seed expiry without making any real token invalidation request.
        from src.ai.chatgpt_auth import _atomic_json
        _atomic_json(auth.credentials_path, state)


def test_sign_in_pkce_identity_permissions_and_private_storage(oauth):
    auth, server = oauth
    server.bad_state_first = True
    status = sign_in(auth, server)
    assert status["plan_usage"] is True
    assert auth.access_token() == "access-secret"
    assert "secret" not in json.dumps(status)
    params = server.authorizations[0]
    assert params["client_id"] == "dynamic_agent_client"
    assert params["agent_name_hint"] == "Horizon"
    assert params["ext_agent_host_id"].startswith("urn:uuid:")
    assert urlsplit(params["redirect_uri"]).hostname == "127.0.0.1"
    assert PLAN_SCOPE in params["scope"].split()
    if os.name != "nt":
        assert auth.credentials_path.stat().st_mode & 0o777 == 0o600
        assert auth.host_path.stat().st_mode & 0o777 == 0o600


def test_reconnect_reuses_registration_host_and_fresh_oauth_state(oauth):
    auth, server = oauth
    sign_in(auth, server)
    sign_in(auth, server)
    first, second = server.authorizations
    assert second["client_id"] == "oaiapp_one"
    assert "agent_name_hint" not in second
    assert "prompt" not in second
    assert first["ext_agent_host_id"] == second["ext_agent_host_id"]
    for key in ("state", "nonce", "code_challenge"):
        assert first[key] != second[key]


@pytest.mark.parametrize("overrides", [
    {"aud": "different-client"}, {"iss": "https://wrong.example"},
    {"nonce": "different-attempt"}, {"exp": 1}, {"sub": ""},
    {"aud": ["oaiapp_one", "another-client"]}, {"azp": "another-client"},
])
def test_invalid_id_token_never_activates_registration(oauth, overrides):
    auth, server = oauth
    server.claim_overrides = overrides
    with pytest.raises(AIProviderUnavailableError, match="ID-token validation"):
        sign_in(auth, server)
    assert auth.status()["connected"] is False
    assert "access-secret" not in auth.credentials_path.read_text()


def test_invalid_signature_rejected(oauth):
    auth, server = oauth
    server.signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(AIProviderUnavailableError, match="ID-token validation"):
        sign_in(auth, server)
    assert auth.status()["connected"] is False


def test_identity_change_does_not_replace_saved_credentials(oauth):
    auth, server = oauth
    sign_in(auth, server)
    before = auth.credentials_path.read_text()
    server.subject = "another-user"
    with pytest.raises(AIProviderUnavailableError, match="identity changed"):
        sign_in(auth, server)
    assert auth.credentials_path.read_text() == before


def test_callback_client_id_change_is_rejected_before_exchange(oauth):
    auth, server = oauth
    sign_in(auth, server)
    requests = len(server.requests)
    server.callback_override = {"client_id": "oaiapp_attacker"}
    with pytest.raises(AIProviderUnavailableError, match="registration callback"):
        sign_in(auth, server)
    assert len(server.requests) == requests
    assert auth.status()["client_id"] == "oaiapp_one"


def test_decline_does_not_exchange_code_or_erase_current_account(oauth):
    auth, server = oauth
    sign_in(auth, server)
    before = auth.credentials_path.read_text()
    requests = len(server.requests)
    server.callback_override = {"error": "access_denied"}
    with pytest.raises(AIProviderUnavailableError, match="declined"):
        sign_in(auth, server)
    assert len(server.requests) == requests
    assert auth.credentials_path.read_text() == before


def test_failed_code_exchange_retains_registration_for_reconnect(oauth):
    auth, server = oauth
    server.exchange_error = "invalid_grant"
    with pytest.raises(AIProviderUnavailableError, match="--account oaiapp_one"):
        sign_in(auth, server)
    assert auth.accounts()[0]["client_id"] == "oaiapp_one"
    assert auth.status()["connected"] is False
    server.exchange_error = None
    sign_in(auth, server, account="oaiapp_one")
    assert server.authorizations[-1]["client_id"] == "oaiapp_one"


def test_identity_login_without_plan_permission_cannot_infer(oauth):
    auth, server = oauth
    server.scopes = "openid email offline_access"
    status = sign_in(auth, server)
    assert status["connected"] and not status["plan_usage"]
    with pytest.raises(AIProviderUnavailableError, match="--enable-plan"):
        auth.access_token()
    server.scopes += f" {PLAN_SCOPE}"
    sign_in(auth, server, enable_plan=True)
    assert server.authorizations[-1]["prompt"] == "consent"
    assert auth.status()["plan_usage"]


def test_rotating_refresh_is_serialized_across_auth_instances(oauth):
    auth, server = oauth
    sign_in(auth, server)
    expire(auth)
    start = threading.Barrier(6)

    def access():
        start.wait()
        return ChatGPTAuth(auth.directory, http_client=auth.http_client).access_token()

    with ThreadPoolExecutor(max_workers=6) as pool:
        tokens = list(pool.map(lambda _: access(), range(6)))
    assert tokens == ["access-secret-refreshed"] * 6
    assert server.refreshes == 1
    state = json.loads(auth.credentials_path.read_text())
    record = state["accounts"]["oaiapp_one"]
    assert record["refresh_token"] == "refresh-secret-rotated"
    assert PLAN_SCOPE in record["scopes"]
    assert record["expires_at"] > time.time() + 3000


def test_temporary_refresh_failure_preserves_tokens_without_echoing_response(oauth):
    auth, server = oauth
    sign_in(auth, server)
    expire(auth)
    before = auth.credentials_path.read_text()
    server.refresh_error = (503, "temporary_failure")
    with pytest.raises(RuntimeError, match="HTTP 503") as error:
        auth.access_token()
    assert "refresh-secret" not in str(error.value)
    assert auth.credentials_path.read_text() == before


def test_revoked_refresh_clears_tokens_but_keeps_identity_and_registration(oauth):
    auth, server = oauth
    sign_in(auth, server)
    expire(auth)
    server.refresh_error = (400, "invalid_grant")
    with pytest.raises(AIProviderUnavailableError, match="expired or was revoked"):
        auth.access_token()
    record = json.loads(auth.credentials_path.read_text())["accounts"]["oaiapp_one"]
    assert record["subject"] == "user-one"
    assert record["client_id"] == "oaiapp_one"
    assert all(name not in record for name in ("access_token", "refresh_token", "id_token"))


def test_account_switch_keeps_registrations_separate_and_models_ordered(oauth):
    auth, server = oauth
    sign_in(auth, server)
    server.new_id, server.subject = "oaiapp_two", "user-two"
    sign_in(auth, server, new_account=True)
    assert auth.status()["client_id"] == "oaiapp_two"
    auth.select("oaiapp_one")
    assert auth.status()["client_id"] == "oaiapp_one"
    assert len(auth.accounts()) == 2
    assert [entry["slug"] for entry in auth.models()] == ["plan-b", "plan-a"]


@pytest.mark.parametrize("revoked", [True, False])
def test_logout_revokes_session_and_retains_registration(oauth, revoked, monkeypatch):
    auth, server = oauth
    sign_in(auth, server)
    host = auth.host_path.read_text()
    server.revoke_status = 200 if revoked else 503
    monkeypatch.setattr("src.ai.chatgpt_auth.time.sleep", lambda _: None)
    assert auth.sign_out() is revoked
    assert not auth.status()["connected"]
    assert "secret" not in auth.credentials_path.read_text()
    assert auth.status()["client_id"] == "oaiapp_one"
    assert auth.host_path.read_text() == host
    requests = [form for req, form in server.requests if req.url.path.endswith("/revoke")]
    assert len(requests) == (1 if revoked else 3)
    assert requests[0] == {"token": "refresh-secret", "token_type_hint": "refresh_token", "client_id": "oaiapp_one"}


def test_cli_status_never_prints_tokens(oauth, monkeypatch, capsys):
    from src.setup import chatgpt
    auth, server = oauth
    sign_in(auth, server)
    monkeypatch.setattr(chatgpt, "ChatGPTAuth", lambda: auth)
    monkeypatch.setattr("sys.argv", ["horizon-chatgpt", "status"])
    chatgpt.main()
    output = capsys.readouterr().out
    assert "secret" not in output
    assert '"plan_usage": true' in output
    assert "https://chatgpt.com/settings/usage" in output


def test_vm_initialization_keeps_distinct_host_identity_during_credential_transfer(oauth, tmp_path):
    auth, server = oauth
    sign_in(auth, server)
    vm = ChatGPTAuth(tmp_path / "vm", http_client=auth.http_client)
    identity = vm.initialize()
    assert identity["ext_agent_host_id"] != server.authorizations[0]["ext_agent_host_id"]
    vm.credentials_path.write_bytes(auth.credentials_path.read_bytes())
    assert vm.access_token() == "access-secret"
    assert vm.initialize() == identity


def test_wizard_signs_in_and_selects_account_model_without_key_prompt(oauth, monkeypatch):
    from src.setup import wizard
    auth, server = oauth
    original_sign_in = auth.sign_in
    monkeypatch.setattr(auth, "sign_in", lambda **kwargs: original_sign_in(open_browser=server.browser, timeout=2, **kwargs))
    monkeypatch.setattr("src.ai.chatgpt_auth.ChatGPTAuth", lambda: auth)
    monkeypatch.setattr(wizard, "load_dotenv", lambda: None)
    monkeypatch.setattr(wizard.console, "print", lambda *args, **kwargs: None)
    answers = iter(["openai-chatgpt", "plan-a", "zh"])
    prompts = []

    def answer(prompt, **kwargs):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(wizard.Prompt, "ask", answer)
    config = wizard.configure_ai()
    assert config.model == "plan-a"
    assert config.chatgpt_account == "oaiapp_one"
    assert config.api_key_env == ""
    assert not any("API key" in prompt for prompt in prompts)
    assert wizard._ai_recommendations_available(config)


def test_mcp_preflight_checks_oauth_without_requesting_an_api_key(oauth, tmp_path, monkeypatch):
    from src.mcp.service import HorizonPipelineService
    auth, server = oauth
    monkeypatch.setenv("HORIZON_CHATGPT_AUTH_DIR", str(auth.directory))
    monkeypatch.setattr("src.mcp.service.load_environment", lambda _: None)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"ai": {"provider": "openai-chatgpt", "model": "plan-a"}, "sources": {}}))
    service = HorizonPipelineService(runs_root=tmp_path / "runs")

    def validate(**kwargs):
        return asyncio.run(service.validate_config(
            horizon_path=str(Path(__file__).resolve().parents[1]), config_path=str(config_path), **kwargs,
        ))

    offline = validate(check_env=False)
    assert "auth" not in offline["ai"]
    assert not auth.directory.exists()
    missing = validate()
    assert missing["missing_env"] == []
    assert missing["ai"]["auth"]["plan_usage"] is False
    assert any("horizon-chatgpt login" in warning for warning in missing["warnings"])
    sign_in(auth, server)
    ready = validate()
    assert ready["missing_env"] == []
    assert ready["ai"]["auth"]["plan_usage"] is True
    assert "secret" not in json.dumps(ready)
    config = json.loads(config_path.read_text())
    config["ai"]["chatgpt_account"] = "unknown-account"
    config_path.write_text(json.dumps(config))
    missing = validate()
    assert not missing["ai"]["auth"]["connected"]
    assert missing["warnings"]


def test_mcp_stages_keep_the_runs_account_when_active_account_changes(oauth, tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from src.ai.enricher import EnrichmentBatchResult
    from src.mcp.service import HorizonPipelineService
    from src.models import ContentItem, SourceType

    auth, server = oauth
    sign_in(auth, server)
    monkeypatch.setattr("src.ai.chatgpt_auth.ChatGPTAuth", lambda: auth)
    monkeypatch.setattr("src.mcp.service.load_environment", lambda _: None)
    config = {"ai": {"provider": "openai-chatgpt", "model": "plan-a"}, "sources": {}}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    service = HorizonPipelineService(runs_root=tmp_path / "runs")
    selected = []

    class Orchestrator:
        def __init__(self, config, *args, **kwargs):
            selected.append(config.ai.chatgpt_account)

        async def analyze_items(self, items):
            return items

        def passes_profile_filter(self, item):
            return True

        async def enrich_items(self, items):
            return EnrichmentBatchResult(succeeded_ids=[item.id for item in items])

    monkeypatch.setattr("src.mcp.service.HorizonOrchestrator", Orchestrator)
    run_id = service.run_store.create_run()
    item = ContentItem(
        id="rss:one", source_type=SourceType.RSS, title="Article", url="https://example.com/article",
        published_at=datetime.now(timezone.utc),
    )
    service.run_store.save_items(run_id, "raw", [item.model_dump(mode="json")])
    kwargs = {"horizon_path": str(Path(__file__).resolve().parents[1]), "config_path": str(config_path)}
    asyncio.run(service.score_items(run_id, **kwargs))
    server.new_id, server.subject = "oaiapp_two", "user-two"
    sign_in(auth, server, new_account=True)
    asyncio.run(service.enrich_items(run_id, source_stage="scored", **kwargs))
    assert selected == ["oaiapp_one", "oaiapp_one"]
    assert service.run_store.load_meta(run_id)["chatgpt_account"] == "oaiapp_one"
    assert json.loads(config_path.read_text()) == config
    auth.sign_out("oaiapp_one")
    with pytest.raises(AIProviderUnavailableError):
        asyncio.run(service.enrich_items(run_id, source_stage="scored", **kwargs))
    assert auth.status()["client_id"] == "oaiapp_two"
