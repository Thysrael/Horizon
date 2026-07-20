"""Strict, bot-facing source inputs and conversion to Horizon configs."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from src.models import (
    GDELTConfig,
    GitHubSourceConfig,
    GoogleNewsConfig,
    HackerNewsConfig,
    OSSInsightConfig,
    OpenBBConfig,
    OpenBBWatchlist,
    RSSSourceConfig,
    RedditSubredditConfig,
    RedditUserConfig,
    TelegramChannelConfig,
    TwitterConfig,
)
from src.url_security import validate_http_url


_USERNAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_]{4,31}$")
_GITHUB_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class StrictSourceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _optional_text(value: str | None) -> str | None:
    return value or None


class RSSInput(StrictSourceInput):
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    enabled: bool = True
    category: str | None = Field(default=None, max_length=255)
    content_extractor: str | None = Field(default=None, max_length=128)

    @field_validator("url")
    @classmethod
    def reject_unsafe_url_forms(cls, value: HttpUrl) -> HttpUrl:
        validate_http_url(str(value))
        return value

    @field_validator("category", "content_extractor")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> RSSSourceConfig:
        return RSSSourceConfig(**self.model_dump())


class TelegramInput(StrictSourceInput):
    channel: str = Field(min_length=5, max_length=33)
    enabled: bool = True
    fetch_limit: int = Field(default=20, ge=1, le=100)
    category: str | None = Field(default=None, max_length=255)

    @field_validator("channel")
    @classmethod
    def normalize_public_username(cls, value: str) -> str:
        username = value.removeprefix("@")
        if not _USERNAME.fullmatch(username):
            raise ValueError("channel must be a public Telegram username")
        return username

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> TelegramChannelConfig:
        return TelegramChannelConfig(**self.model_dump())


class GitHubInput(StrictSourceInput):
    type: Literal["user_events", "repo_releases"]
    username: str | None = Field(default=None, max_length=39)
    owner: str | None = Field(default=None, max_length=39)
    repo: str | None = Field(default=None, max_length=100)
    enabled: bool = True
    category: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_target(self) -> "GitHubInput":
        if self.type == "user_events" and self.username and not self.owner and not self.repo:
            return self
        if self.type == "repo_releases" and self.owner and self.repo and not self.username:
            return self
        raise ValueError("GitHub source target does not match its type")

    @field_validator("username", "owner", "repo")
    @classmethod
    def validate_github_name(cls, value: str | None) -> str | None:
        if value is not None and not _GITHUB_NAME.fullmatch(value):
            raise ValueError("invalid GitHub name")
        return value

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> GitHubSourceConfig:
        return GitHubSourceConfig(**self.model_dump())


class HackerNewsInput(StrictSourceInput):
    enabled: bool = True
    fetch_top_stories: int = Field(default=30, ge=1, le=500)
    min_score: int = Field(default=100, ge=0, le=100_000)
    category: str | None = Field(default=None, max_length=255)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> HackerNewsConfig:
        return HackerNewsConfig(**self.model_dump())


class RedditInput(StrictSourceInput):
    subreddit: str | None = Field(default=None, max_length=21)
    username: str | None = Field(default=None, max_length=20)
    enabled: bool = True
    sort: str = "hot"
    time_filter: str = "day"
    fetch_limit: int = Field(default=25, ge=1, le=100)
    min_score: int = Field(default=10, ge=0, le=100_000)
    category: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def require_one_target(self) -> "RedditInput":
        if bool(self.subreddit) == bool(self.username):
            raise ValueError("provide exactly one of subreddit or username")
        return self

    @field_validator("subreddit")
    @classmethod
    def normalize_subreddit(cls, value: str | None) -> str | None:
        if value is None:
            return None
        result = value.removeprefix("r/")
        if not re.fullmatch(r"[A-Za-z0-9_]{2,21}", result):
            raise ValueError("invalid subreddit")
        return result

    @field_validator("username")
    @classmethod
    def normalize_reddit_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        result = value.removeprefix("u/")
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,20}", result):
            raise ValueError("invalid Reddit username")
        return result

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> RedditSubredditConfig | RedditUserConfig:
        values = self.model_dump(exclude_none=True)
        if self.subreddit:
            return RedditSubredditConfig(**values)
        values.pop("min_score", None)
        values.pop("time_filter", None)
        return RedditUserConfig(**values)


class GoogleNewsInput(StrictSourceInput):
    query: str = Field(min_length=1, max_length=500)
    enabled: bool = True
    language: str = Field(default="en", min_length=2, max_length=16)
    country: str = Field(default="US", min_length=2, max_length=2)
    ceid: str | None = Field(default=None, max_length=32)
    max_results: int = Field(default=100, ge=1, le=100)
    category: str | None = Field(default=None, max_length=255)

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return value.lower()

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError("country must be an ISO country code")
        return value.upper()

    @field_validator("ceid", "category")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> GoogleNewsConfig:
        return GoogleNewsConfig(**self.model_dump())


class GDELTInput(StrictSourceInput):
    query: str = Field(min_length=1, max_length=500)
    enabled: bool = True
    mode: str = "ArtList"
    max_records: int = Field(default=75, ge=1, le=250)
    timespan: str | None = Field(default=None, max_length=32)
    language: str | None = Field(default=None, max_length=64)
    country: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=255)

    @field_validator("timespan", "language", "country", "category")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> GDELTConfig:
        return GDELTConfig(**self.model_dump())


class OSSInsightInput(StrictSourceInput):
    enabled: bool = True
    period: Literal["past_24_hours", "past_28_days"] = "past_24_hours"
    languages: list[str] = Field(default_factory=lambda: ["All", "Python", "TypeScript"], min_length=1)
    keywords: list[str] = Field(default_factory=list)
    min_stars: int = Field(default=5, ge=0)
    max_items: int = Field(default=30, ge=1, le=100)
    category: str | None = Field(default=None, max_length=255)

    @field_validator("languages", "keywords")
    @classmethod
    def normalize_string_list(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not normalized and values:
            raise ValueError("list entries must not be blank")
        return normalized

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> OSSInsightConfig:
        return OSSInsightConfig(**self.model_dump())


class TwitterInput(StrictSourceInput):
    users: list[str] = Field(min_length=1)
    enabled: bool = True
    mode: Literal["apify", "playwright"] = "apify"
    fetch_limit: int = Field(default=10, ge=1, le=100)
    category: str | None = Field(default=None, max_length=255)

    @field_validator("users")
    @classmethod
    def normalize_users(cls, values: list[str]) -> list[str]:
        users = list(dict.fromkeys(value.strip().removeprefix("@") for value in values))
        if not users or any(not _USERNAME.fullmatch(user) for user in users):
            raise ValueError("users must be public X usernames")
        return users

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> TwitterConfig:
        return TwitterConfig(**self.model_dump())


class OpenBBInput(StrictSourceInput):
    name: str = Field(min_length=1, max_length=255)
    symbols: list[str] = Field(min_length=1)
    enabled: bool = True
    provider: str = Field(default="yfinance", min_length=1, max_length=64)
    fetch_limit: int = Field(default=20, ge=1, le=100)
    category: str | None = Field(default=None, max_length=255)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, values: list[str]) -> list[str]:
        symbols = list(dict.fromkeys(value.strip().upper() for value in values if value.strip()))
        if not symbols:
            raise ValueError("symbols must not be blank")
        return symbols

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        return _optional_text(value)

    def to_horizon(self) -> OpenBBConfig:
        return OpenBBConfig(watchlists=[OpenBBWatchlist(**self.model_dump())])
