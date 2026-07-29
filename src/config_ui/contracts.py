"""Browser-facing request contracts for configuration editing."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CandidateRequest(BaseModel):
    """A complete raw configuration candidate used only for validation."""

    config: dict[str, Any]


class PatchRequest(BaseModel):
    """A revision-bound JSON Patch preview or save request."""

    revision: str | None = None
    patch: list[dict[str, Any]] = Field(default_factory=list)
    acknowledge_warnings: bool = False


class RestoreRequest(BaseModel):
    """An explicitly confirmed, revision-bound backup restore request."""

    revision: str
    confirm: bool = False
    acknowledge_warnings: bool = False
