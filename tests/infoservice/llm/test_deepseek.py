import httpx
import pytest
import respx

from src.infoservice.llm.deepseek import (
    CredentialVerificationUnavailable,
    DeepSeekVerifier,
    InvalidCredential,
)


@respx.mock
def test_verify_sends_only_bearer_authorization_and_returns_model_ids():
    route = respx.get("https://api.deepseek.com/models").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "deepseek-chat"}, {"id": "deepseek-reasoner"}]})
    )

    credential = DeepSeekVerifier().verify("sk-user-secret")

    assert credential.model_ids == ("deepseek-chat", "deepseek-reasoner")
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer sk-user-secret"
    assert request.content == b""
    assert "Content-Type" not in request.headers


@pytest.mark.parametrize("status_code", [401, 403])
@respx.mock
def test_verify_maps_auth_failures_without_leaking_key(status_code):
    key = "sk-user-secret"
    respx.get("https://api.deepseek.com/models").mock(return_value=httpx.Response(status_code, text="provider response"))

    with pytest.raises(InvalidCredential) as exc:
        DeepSeekVerifier().verify(key)

    assert key not in str(exc.value)
    assert "provider response" not in str(exc.value)


@respx.mock
def test_verify_maps_server_failures_without_exposing_response_body():
    respx.get("https://api.deepseek.com/models").mock(return_value=httpx.Response(503, text="provider response"))

    with pytest.raises(CredentialVerificationUnavailable) as exc:
        DeepSeekVerifier().verify("sk-user-secret")

    assert "provider response" not in str(exc.value)
