"""Provider defaults name models the provider still serves."""

from src.models import AI_PROVIDER_DEFAULTS, AIProvider

# Shut down on the Gemini API: the 1.5 models on 2025-09-29, the 2.0 models on
# 2026-06-01 (https://ai.google.dev/gemini-api/docs/changelog and /deprecations).
SHUT_DOWN_GEMINI_MODELS = {
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
}


def test_gemini_default_model_is_still_served():
    model = AI_PROVIDER_DEFAULTS[AIProvider.GEMINI]["model"]
    assert model
    assert model not in SHUT_DOWN_GEMINI_MODELS
