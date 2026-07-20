"""Authenticated encryption and safe display helpers for API credentials."""

from __future__ import annotations

import re

from cryptography.fernet import Fernet


SECRET_PREFIXES = (
    "sk-",
    "sk_",
    "AIza",
    "xai-",
    "gsk_",
    "hf_",
)
_API_KEY_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9_-])(?:{'|'.join(map(re.escape, SECRET_PREFIXES))})[A-Za-z0-9_-]+"
)


def validate_fernet_key(encryption_key: str) -> str:
    """Return a valid Fernet key without ever including its value in errors."""
    try:
        Fernet(encryption_key.encode("ascii"))
    except (UnicodeEncodeError, ValueError) as exc:
        raise ValueError("APP_ENCRYPTION_KEY must be a valid Fernet key") from exc
    return encryption_key


class CredentialCipher:
    """Encrypt credentials using the application's Fernet key."""

    def __init__(self, encryption_key: str) -> None:
        self._fernet = Fernet(validate_fernet_key(encryption_key).encode("ascii"))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str) -> str:
        return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")

    @staticmethod
    def mask(value: str) -> str:
        if len(value) <= 4:
            return "…"
        return f"{value[:3]}…{value[-4:]}"

    def redact(self, value: str) -> str:
        return _API_KEY_PATTERN.sub(lambda match: self.mask(match.group(0)), value)
