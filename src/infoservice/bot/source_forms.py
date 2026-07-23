"""Pure parsing and presentation helpers for stable Telegram source forms."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import re
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urlsplit

import feedparser
import httpx

from src.infoservice.settings import Settings
from src.infoservice.sources.catalog import SourceCatalog, SourceValidationError
from src.url_security import UnsafeURLError, safe_request, validate_http_url


STABLE_SOURCE_TYPES = ("rss", "telegram", "github", "hackernews")
_TELEGRAM_USERNAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_]{4,31}$")
_GITHUB_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
DEFAULTS: Mapping[str, Mapping[str, Any]] = MappingProxyType(
    {
        "rss": MappingProxyType({"enabled": True}),
        "telegram": MappingProxyType({"enabled": True, "fetch_limit": 20}),
        "github": MappingProxyType({"enabled": True}),
        "hackernews": MappingProxyType(
            {
                "enabled": True,
                "fetch_top_stories": 30,
                "min_score": 100,
            }
        ),
    }
)


def _require_stable_source_type(source_type: str) -> None:
    if source_type not in STABLE_SOURCE_TYPES:
        raise ValueError("unsupported stable source type")


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_json_value(nested) for key, nested in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(nested) for nested in value)
    return value


def _storage_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _storage_json_value(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_storage_json_value(nested) for nested in value]
    return value


class SourceFieldError(ValueError):
    """An input error that can be displayed next to a particular form field."""

    def __init__(self, field: str, reason: str, example: str) -> None:
        super().__init__(reason)
        self.field = field
        self.reason = reason
        self.example = example


@dataclass(frozen=True, slots=True)
class SourceDraft:
    """JSON-serializable in-progress source configuration."""

    report_id: str | None
    source_type: str
    source_id: str | None = None
    mode: str = "create"
    enabled: bool = True
    values: Mapping[str, Any] = field(default_factory=dict)
    current_field: str | None = None
    screen: str = "primary"
    history: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _freeze_json_value(self.values))

    @classmethod
    def new(cls, report_id: str, source_type: str) -> SourceDraft:
        _require_stable_source_type(source_type)
        return cls(
            report_id=report_id,
            source_type=source_type,
            values=dict(DEFAULTS[source_type]),
        )

    @classmethod
    def edit(
        cls,
        source_id: str,
        source_type: str,
        values: Mapping[str, Any],
        enabled: bool,
    ) -> SourceDraft:
        _require_stable_source_type(source_type)
        return cls(
            report_id=None,
            source_id=source_id,
            source_type=source_type,
            mode="edit",
            enabled=enabled,
            values=dict(values),
            screen="edit_fields",
            history=("source_card",),
        )

    def with_values(self, **values: Any) -> SourceDraft:
        return replace(self, values={**self.values, **values})

    def to_storage(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "mode": self.mode,
            "enabled": self.enabled,
            "values": _storage_json_value(self.values),
            "current_field": self.current_field,
            "screen": self.screen,
            "history": list(self.history),
        }

    @classmethod
    def from_storage(cls, raw: Mapping[str, Any]) -> SourceDraft:
        return cls(
            report_id=raw.get("report_id"),
            source_type=str(raw["source_type"]),
            source_id=raw.get("source_id"),
            mode=str(raw.get("mode", "create")),
            enabled=bool(raw.get("enabled", True)),
            values=dict(raw.get("values", {})),
            current_field=raw.get("current_field"),
            screen=str(raw.get("screen", "primary")),
            history=tuple(raw.get("history", ())),
        )


def _telegram_channel(text: str) -> str:
    value = text.strip()
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "t.me",
            "www.t.me",
            "telegram.me",
            "www.telegram.me",
        }:
            raise SourceFieldError("channel", "Нужна публичная ссылка t.me.", "@durov")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 1 or parts[0].startswith("+"):
            raise SourceFieldError(
                "channel", "Приватные ссылки не поддерживаются.", "@durov"
            )
        value = parts[0]
    value = value.removeprefix("@")
    if not _TELEGRAM_USERNAME.fullmatch(value):
        raise SourceFieldError(
            "channel",
            "Username должен содержать 5–32 буквы, цифры или подчёркивания.",
            "@durov",
        )
    return value


def _github_target(text: str, kind: str) -> dict[str, str]:
    value = text.strip().rstrip("/")
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "github.com",
            "www.github.com",
        }:
            raise SourceFieldError("target", "Нужна ссылка github.com.", "pallets/flask")
        value = parsed.path.strip("/")
    parts = value.split("/")
    if (
        kind == "repo_releases"
        and len(parts) == 2
        and all(_GITHUB_NAME.fullmatch(part) for part in parts)
    ):
        return {"type": kind, "owner": parts[0], "repo": parts[1]}
    if (
        kind == "user_events"
        and len(parts) == 1
        and _GITHUB_NAME.fullmatch(parts[0].removeprefix("@"))
    ):
        return {"type": kind, "username": parts[0].removeprefix("@")}
    example = "pallets/flask" if kind == "repo_releases" else "octocat"
    raise SourceFieldError(
        "target", "Цель GitHub не соответствует выбранному типу.", example
    )


def parse_primary(
    source_type: str,
    text: str,
    github_kind: str | None = None,
) -> dict[str, Any]:
    """Parse a source's primary target into a strict-schema-ready config fragment."""
    value = text.strip()
    try:
        if source_type == "rss":
            validate_http_url(value)
            hostname = urlsplit(value).hostname or "RSS"
            return {"url": value, "name": hostname}
        if source_type == "telegram":
            return {"channel": _telegram_channel(value)}
        if source_type == "github":
            if github_kind not in {"repo_releases", "user_events"}:
                raise SourceFieldError(
                    "type", "Сначала выберите тип GitHub-источника.", "Релизы"
                )
            return _github_target(value, github_kind)
        if source_type == "hackernews":
            return {}
    except UnsafeURLError as exc:
        raise SourceFieldError(
            "url", "Нужна безопасная ссылка HTTP(S).", "https://example.com/feed.xml"
        ) from exc
    raise SourceFieldError("source_type", "Этот тип пока не поддерживается.", "RSS")


def apply_field(draft: SourceDraft, field_name: str, text: str) -> SourceDraft:
    """Return a copy of *draft* with one validated, editable field applied."""
    value = text.strip()
    try:
        if field_name == "category":
            if value != "-" and len(value) > 255:
                raise ValueError
            parsed: Any = None if value == "-" else value
        elif field_name == "name":
            if not value or len(value) > 255:
                raise ValueError
            parsed = value
        elif field_name == "fetch_limit":
            parsed = int(value)
            if parsed not in {10, 20, 50}:
                raise ValueError
        elif field_name == "fetch_top_stories":
            parsed = int(value)
            if not 1 <= parsed <= 500:
                raise ValueError
        elif field_name == "min_score":
            parsed = int(value)
            if not 0 <= parsed <= 100_000:
                raise ValueError
        else:
            raise SourceFieldError(
                field_name, "Поле нельзя изменить.", "Выберите поле кнопкой"
            )
    except ValueError as exc:
        examples = {
            "category": "Технологии",
            "name": "Python Blog",
            "fetch_limit": "20",
            "fetch_top_stories": "30",
            "min_score": "100",
        }
        raise SourceFieldError(
            field_name, "Значение вне допустимого диапазона.", examples[field_name]
        ) from exc
    return draft.with_values(**{field_name: parsed})


async def resolve_rss_name(url: str, client: httpx.AsyncClient | None = None) -> str:
    """Discover an RSS title through the existing SSRF-safe request path."""
    fallback = urlsplit(url).hostname or "RSS"
    owns_client = client is None
    active_client = client or httpx.AsyncClient(timeout=10)
    try:
        response = await safe_request(active_client, "GET", url, max_redirects=5)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        title = str(parsed.feed.get("title", "")).strip()
        return title[:255] or fallback
    except (httpx.HTTPError, UnsafeURLError, ValueError):
        return fallback
    finally:
        if owns_client:
            await active_client.aclose()


def validated_config(draft: SourceDraft, settings: Settings) -> dict[str, Any]:
    """Run the unchanged source catalog validation for a completed draft."""
    _require_stable_source_type(draft.source_type)
    try:
        result = SourceCatalog.validate(
            draft.source_type, _storage_json_value(draft.values), settings
        )
    except SourceValidationError as exc:
        raise SourceFieldError(
            draft.current_field or "config",
            "Проверьте введённые значения.",
            "Вернитесь к полю и повторите ввод",
        ) from exc
    return result.model_dump(mode="json", exclude_none=True)


def format_source_card(
    source_type: str,
    config: Mapping[str, Any],
    enabled: bool = True,
) -> str:
    """Render a concise Russian source summary without exposing storage JSON."""
    status = "включён" if enabled else "приостановлен"
    category = config.get("category") or "без категории"
    if source_type == "rss":
        details = f"Название: {config['name']}\nАдрес: {config['url']}"
        title = "RSS / Atom"
    elif source_type == "telegram":
        details = (
            f"Канал: @{config['channel']}\n"
            f"Проверять сообщений: {config.get('fetch_limit', 20)}"
        )
        title = "Telegram-канал"
    elif source_type == "github":
        if config["type"] == "repo_releases":
            target = f"{config['owner']}/{config['repo']}"
            mode = "релизы репозитория"
        else:
            target = f"@{config['username']}"
            mode = "события пользователя"
        details = f"Режим: {mode}\nЦель: {target}"
        title = "GitHub"
    elif source_type == "hackernews":
        details = (
            f"Проверять публикаций: {config.get('fetch_top_stories', 30)}\n"
            f"Минимальный рейтинг: {config.get('min_score', 100)}"
        )
        title = "Hacker News"
    else:
        return f"Источник: {source_type}\nСостояние: {status}"
    return f"{title}\n{details}\nКатегория: {category}\nСостояние: {status}"
