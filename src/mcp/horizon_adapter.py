"""Adapter layer that reuses Horizon's native Python modules."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from ..models import Config, ContentItem, SOURCE_REGISTRY
from ..storage.manager import StorageManager, _expand_env_vars
from .errors import HorizonMcpError


VALID_SOURCES = frozenset(SOURCE_REGISTRY)
ENV_KEY_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def resolve_horizon_path(explicit: str | None = None) -> Path:
    """Resolve the workspace containing configuration, profiles, and credentials."""

    requested = explicit or os.getenv("HORIZON_PATH")
    if requested:
        path = Path(requested).expanduser().resolve()
        if path.is_dir():
            return path
        raise HorizonMcpError(
            code="HZ_INVALID_HORIZON_PATH",
            message="horizon_path must be an existing workspace directory.",
            details={"horizon_path": str(path)},
        )

    repo_root = Path(__file__).resolve().parents[2]
    cwd = Path.cwd()
    candidates = [repo_root, cwd, cwd / "Horizon", cwd.parent / "Horizon"]

    seen: set[Path] = set()
    for candidate in candidates:
        path = candidate.resolve()
        if path in seen:
            continue
        seen.add(path)
        if _is_horizon_repo(path):
            return path

    checked = ", ".join(str(p.resolve()) for p in candidates)
    raise HorizonMcpError(
        code="HZ_HORIZON_NOT_FOUND",
        message="Horizon repository was not found. Pass horizon_path or set HORIZON_PATH.",
        details={"checked": checked},
    )


def resolve_config_path(horizon_path: Path, config_path: str | None = None) -> Path:
    """Resolve config path, defaulting to <horizon>/data/config.json."""

    if not config_path:
        path = (horizon_path / "data/config.json").resolve()
    else:
        raw = Path(config_path).expanduser()
        if raw.is_absolute():
            path = raw.resolve()
        else:
            candidate = (horizon_path / raw).resolve()
            path = candidate if candidate.exists() else (Path.cwd() / raw).resolve()

    if not path.exists():
        raise HorizonMcpError(
            code="HZ_CONFIG_NOT_FOUND",
            message="Config file does not exist.",
            details={"config_path": str(path)},
        )

    return path


def load_environment(horizon_path: Path) -> None:
    """Load workspace credentials; application code comes from this installation."""
    load_dotenv(horizon_path / ".env", override=False)
    _load_mcp_secrets(horizon_path, override=False)


def load_config(config_path: Path) -> Config:
    """Load Horizon config using native pydantic model."""

    try:
        payload = _expand_env_vars(
            json.loads(config_path.read_text(encoding="utf-8"))
        )
        return Config.model_validate(payload)
    except Exception as exc:
        raise HorizonMcpError(
            code="HZ_CONFIG_INVALID",
            message="Failed to parse config file.",
            details={"config_path": str(config_path), "error": str(exc)},
        ) from exc


def make_storage(config_path: Path) -> StorageManager:
    """Build Horizon storage manager bound to config's data directory."""

    data_dir = str(config_path.parent.resolve())
    return StorageManager(data_dir=data_dir, config_path=str(config_path))


def apply_source_filter(
    config: Config, sources: list[str] | None
) -> tuple[Config, list[str], list[str]]:
    """Return filtered config and source selection diagnostics."""

    if not sources:
        enabled = get_enabled_sources(config)
        return config, enabled, []

    wanted = {s.strip().lower() for s in sources if s.strip()}
    unknown = sorted(wanted - VALID_SOURCES)
    chosen = sorted(wanted & VALID_SOURCES)

    clone = config.model_copy(deep=True)

    for source_name, definition in SOURCE_REGISTRY.items():
        if source_name in wanted:
            continue
        source_config = getattr(clone.sources, definition.config_field, None)
        if definition.config_is_list:
            setattr(clone.sources, definition.config_field, [])
        elif source_config is not None:
            source_config.enabled = False
            for item_field in definition.item_fields:
                setattr(source_config, item_field, [])

    return clone, chosen, unknown


def get_enabled_sources(config: Config) -> list[str]:
    """List enabled top-level source types in effective config."""

    enabled: list[str] = []
    for source_name, definition in SOURCE_REGISTRY.items():
        source_config = getattr(config.sources, definition.config_field, None)
        if definition.config_is_list:
            is_enabled = any(
                getattr(item, "enabled", True) for item in source_config or []
            )
        else:
            is_enabled = getattr(source_config, "enabled", False)
        if is_enabled:
            enabled.append(source_name)
    return enabled


def items_to_dicts(items: list[ContentItem]) -> list[dict[str, Any]]:
    """Serialize Horizon ContentItem models."""

    return [item.model_dump(mode="json") for item in items]


def dicts_to_items(payload: list[dict[str, Any]]) -> list[ContentItem]:
    """Deserialize ContentItem list."""

    return [ContentItem.model_validate(item) for item in payload]


def get_source_counts(items: list[ContentItem]) -> dict[str, int]:
    """Count items by source type."""

    counts: dict[str, int] = {}
    for item in items:
        key = item.source_type.value
        counts[key] = counts.get(key, 0) + 1
    return counts


def _is_horizon_repo(path: Path) -> bool:
    return (path / "src" / "main.py").exists() and (path / "pyproject.toml").exists()


def _load_mcp_secrets(horizon_path: Path, override: bool = False) -> None:
    """Load MCP secrets from JSON and inject string environment variables."""

    secrets_path = _resolve_secrets_path(horizon_path)
    if not secrets_path:
        return

    try:
        payload = json.loads(secrets_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HorizonMcpError(
            code="HZ_SECRETS_INVALID",
            message="Failed to parse MCP secrets file.",
            details={"secrets_path": str(secrets_path), "error": str(exc)},
        ) from exc

    if not isinstance(payload, dict):
        raise HorizonMcpError(
            code="HZ_SECRETS_INVALID",
            message="MCP secrets file must be a JSON object.",
            details={"secrets_path": str(secrets_path)},
        )

    env_payload = payload.get("env", payload)
    if not isinstance(env_payload, dict):
        raise HorizonMcpError(
            code="HZ_SECRETS_INVALID",
            message="The env field in MCP secrets must be a JSON object.",
            details={"secrets_path": str(secrets_path)},
        )

    for key, value in env_payload.items():
        if not ENV_KEY_RE.fullmatch(str(key)):
            continue
        if not isinstance(value, str):
            raise HorizonMcpError(
                code="HZ_SECRETS_INVALID",
                message=f"MCP secret {key} must be a string.",
                details={"secrets_path": str(secrets_path), "key": key},
            )
        if value.strip() == "":
            continue
        if override or not os.getenv(key):
            os.environ[key] = value


def _resolve_secrets_path(horizon_path: Path) -> Path | None:
    """Resolve secrets config path via env and common locations."""

    explicit = os.getenv("HORIZON_MCP_SECRETS_PATH")
    if explicit:
        explicit_path = Path(explicit).expanduser().resolve()
        if explicit_path.exists():
            return explicit_path
        raise HorizonMcpError(
            code="HZ_SECRETS_NOT_FOUND",
            message="HORIZON_MCP_SECRETS_PATH points to a missing file.",
            details={"secrets_path": str(explicit_path)},
        )

    cwd = Path.cwd()
    candidates = [
        cwd / ".cursor" / "mcp.secrets.json",
        cwd / ".cursor" / "mcp.secrets.local.json",
        cwd / "config" / "mcp.secrets.json",
        cwd / "config" / "mcp.secrets.local.json",
        horizon_path / "data" / "mcp.secrets.json",
        horizon_path / "data" / "mcp-secrets.json",
    ]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    return None
