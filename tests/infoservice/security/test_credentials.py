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


def test_cipher_rejects_an_invalid_fernet_key_without_echoing_it():
    invalid_key = "not-a-fernet-key"

    with pytest.raises(ValueError) as exc:
        CredentialCipher(invalid_key)

    assert invalid_key not in str(exc.value)
