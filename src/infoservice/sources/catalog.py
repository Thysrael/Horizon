"""The allow-listed source boundary for InfoService JSONB configs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from pydantic import BaseModel, ValidationError

from src.infoservice.settings import Settings

from .schemas import (
    GDELTInput,
    GitHubInput,
    GoogleNewsInput,
    HackerNewsInput,
    OpenBBInput,
    OSSInsightInput,
    RSSInput,
    RedditInput,
    StrictSourceInput,
    TelegramInput,
    TwitterInput,
)


class SourceValidationError(ValueError):
    """Raised for invalid or unavailable user-controlled source configs."""


Stability = Literal["stable", "beta", "optional"]


@dataclass(frozen=True)
class SourceCapability:
    type: str
    label: str
    stability: Stability
    input_fields: tuple[str, ...]
    model_factory: Callable[[StrictSourceInput], BaseModel]
    schema: type[StrictSourceInput]
    enabled: Callable[[Settings], bool] = lambda settings: True


def _factory(model: StrictSourceInput) -> BaseModel:
    return model.to_horizon()  # type: ignore[no-any-return]


class SourceCatalog:
    _CAPABILITIES: tuple[SourceCapability, ...] = (
        SourceCapability("rss", "RSS-лента", "stable", tuple(RSSInput.model_fields), _factory, RSSInput),
        SourceCapability("telegram", "Telegram-канал", "stable", tuple(TelegramInput.model_fields), _factory, TelegramInput),
        SourceCapability("hackernews", "Hacker News", "stable", tuple(HackerNewsInput.model_fields), _factory, HackerNewsInput),
        SourceCapability("github", "GitHub", "stable", tuple(GitHubInput.model_fields), _factory, GitHubInput),
        SourceCapability("reddit", "Reddit", "beta", tuple(RedditInput.model_fields), _factory, RedditInput),
        SourceCapability("google_news", "Google Новости", "beta", tuple(GoogleNewsInput.model_fields), _factory, GoogleNewsInput),
        SourceCapability("gdelt", "GDELT", "beta", tuple(GDELTInput.model_fields), _factory, GDELTInput),
        SourceCapability("ossinsight", "OSS Insight", "beta", tuple(OSSInsightInput.model_fields), _factory, OSSInsightInput),
        SourceCapability("twitter", "X (Twitter)", "optional", tuple(TwitterInput.model_fields), _factory, TwitterInput, lambda settings: settings.enable_twitter),
        SourceCapability("openbb", "OpenBB", "optional", tuple(OpenBBInput.model_fields), _factory, OpenBBInput, lambda settings: settings.enable_openbb),
    )

    @classmethod
    def available(cls, settings: Settings) -> list[SourceCapability]:
        return [capability for capability in cls._CAPABILITIES if capability.enabled(settings)]

    @classmethod
    def validate(cls, source_type: str, raw: dict, settings: Settings) -> BaseModel:
        capability = next((item for item in cls.available(settings) if item.type == source_type), None)
        if capability is None:
            raise SourceValidationError("Источник недоступен")
        try:
            parsed = capability.schema.model_validate(raw)
            return capability.model_factory(parsed)
        except (ValidationError, ValueError) as exc:
            raise SourceValidationError("Некорректная конфигурация источника") from exc
