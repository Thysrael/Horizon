"""Safe DeepSeek credential verification."""

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True, slots=True)
class VerifiedCredential:
    model_ids: tuple[str, ...]


class InvalidCredential(Exception):
    """The provider rejected the supplied credential."""


class CredentialVerificationUnavailable(Exception):
    """The provider could not be reached safely to verify a credential."""


class DeepSeekVerifier:
    """Verify a DeepSeek API key without persisting or logging it."""

    _MODELS_URL = "https://api.deepseek.com/models"

    def verify(self, api_key: str) -> VerifiedCredential:
        try:
            with httpx.Client(timeout=10.0, headers={"Authorization": f"Bearer {api_key}"}) as client:
                response = client.get(self._MODELS_URL)
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise CredentialVerificationUnavailable("Credential verification is temporarily unavailable") from exc

        if response.status_code in {401, 403}:
            raise InvalidCredential("The API key was rejected")
        if response.status_code == 429 or response.status_code >= 500:
            raise CredentialVerificationUnavailable("Credential verification is temporarily unavailable")
        if response.is_error:
            raise CredentialVerificationUnavailable("Credential verification is temporarily unavailable")

        try:
            data = response.json().get("data", [])
            model_ids = tuple(model["id"] for model in data if isinstance(model.get("id"), str))
        except (AttributeError, TypeError, ValueError):
            raise CredentialVerificationUnavailable("Credential verification is temporarily unavailable") from None
        return VerifiedCredential(model_ids=model_ids)
