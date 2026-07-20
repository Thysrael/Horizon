from cryptography.fernet import Fernet
import pytest

from src.infoservice.security.credentials import CredentialCipher


@pytest.fixture
def cipher():
    return CredentialCipher(Fernet.generate_key().decode())


def test_cipher_round_trip_without_plaintext(cipher):
    token = cipher.encrypt("sk-secret-value")

    assert "sk-secret-value" not in token
    assert cipher.decrypt(token) == "sk-secret-value"


def test_cipher_masks_and_redacts_a_key(cipher):
    assert cipher.mask("sk-secret-value") == "sk-…alue"
    assert cipher.redact("request failed: sk-secret-value") == "request failed: sk-…alue"


@pytest.mark.parametrize(
    "secret",
    (
        "sk-secret-value",
        "sk_secret_value",
        "AIzaSecretValue",
        "xai-secret-value",
        "gsk_secret_value",
        "hf_secret_value",
    ),
)
def test_cipher_redacts_all_supported_secret_prefixes(cipher, secret):
    message = f"request failed: {secret}"

    redacted = cipher.redact(message)

    assert redacted == f"request failed: {cipher.mask(secret)}"
    assert secret not in redacted


def test_cipher_rejects_an_invalid_fernet_key_without_echoing_it():
    invalid_key = "not-a-fernet-key"

    with pytest.raises(ValueError) as exc:
        CredentialCipher(invalid_key)

    assert invalid_key not in str(exc.value)
