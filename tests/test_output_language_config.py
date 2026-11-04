import pytest
from pydantic import ValidationError

from src.models import AIConfig


@pytest.mark.parametrize("languages", [[], ["en", "en"], ["en-US", "EN_us"], ["zh", "ZH"]])
def test_empty_or_duplicate_output_languages_are_rejected(languages):
    with pytest.raises(ValidationError):
        AIConfig(provider="openai", model="synthetic-model", api_key_env="TEST_KEY", languages=languages)


def test_distinct_language_order_is_preserved():
    config = AIConfig(
        provider="openai", model="synthetic-model", api_key_env="TEST_KEY", languages=["zh", "en-US"],
    )
    assert config.languages == ["zh", "en-US"]
