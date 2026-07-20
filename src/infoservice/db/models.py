from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SqlEnum

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StringEnum(str, Enum):
    pass


def string_enum_type(enum_class: type[StringEnum], name: str) -> SqlEnum:
    return SqlEnum(enum_class, name=name, values_callable=lambda values: [item.value for item in values])


class CredentialSource(StringEnum):
    USER = "user"
    PLATFORM = "platform"


class CredentialStatus(StringEnum):
    UNKNOWN = "unknown"
    VALID = "valid"
    INVALID = "invalid"


class ScheduleKind(StringEnum):
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"
    CRON = "cron"


class RunTrigger(StringEnum):
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class RunStatus(StringEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class SourceRunStatus(StringEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), onupdate=utcnow
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("telegram_user_id", name="uq_users_telegram_user_id"),
        UniqueConstraint("chat_id", name="uq_users_chat_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    telegram_user_id: Mapped[int] = mapped_column(nullable=False)
    chat_id: Mapped[int] = mapped_column(nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", server_default="en")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    credentials: Mapped[list[LLMCredential]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[list[Report]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)


class LLMCredential(TimestampMixin, Base):
    __tablename__ = "llm_credentials"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_llm_credentials_user_provider"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    credential_source: Mapped[CredentialSource] = mapped_column(string_enum_type(CredentialSource, "credential_source"), default=CredentialSource.USER)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(2048))
    ciphertext: Mapped[bytes] = mapped_column(nullable=False)
    key_mask: Mapped[str] = mapped_column(String(255), nullable=False)
    validation_status: Mapped[CredentialStatus] = mapped_column(string_enum_type(CredentialStatus, "credential_status"), default=CredentialStatus.UNKNOWN)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="credentials")


class Report(TimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("ai_score_threshold >= 0 AND ai_score_threshold <= 10", name="ck_reports_ai_score_threshold"),
        CheckConstraint("max_items >= 1 AND max_items <= 30", name="ck_reports_max_items"),
        Index("ix_reports_user_id", "user_id"),
        Index("ix_reports_enabled_next_run_at", "enabled", "next_run_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", server_default="en", nullable=False)
    lookback_hours: Mapped[int] = mapped_column(Integer, default=24, server_default="24", nullable=False)
    ai_score_threshold: Mapped[float] = mapped_column(default=7.0, server_default="7", nullable=False)
    max_items: Mapped[int] = mapped_column(Integer, default=10, server_default="10", nullable=False)
    categories: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)
    exclusions: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]", nullable=False)
    custom_instruction: Mapped[str | None] = mapped_column(Text)
    schedule_kind: Mapped[ScheduleKind] = mapped_column(string_enum_type(ScheduleKind, "schedule_kind"), nullable=False)
    schedule_value: Mapped[str] = mapped_column(String(128), nullable=False)
    timezone: Mapped[str | None] = mapped_column(String(64))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="reports")
    sources: Mapped[list[Source]] = relationship(back_populates="report", cascade="all, delete-orphan", passive_deletes=True)
    runs: Mapped[list[ReportRun]] = relationship(back_populates="report", cascade="all, delete-orphan", passive_deletes=True)


class Source(TimestampMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (Index("ix_sources_report_id", "report_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    report_id: Mapped[UUID] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    report: Mapped[Report] = relationship(back_populates="sources")
    run_results: Mapped[list[SourceRunResult]] = relationship(back_populates="source", cascade="all, delete-orphan", passive_deletes=True)


class ReportRun(TimestampMixin, Base):
    __tablename__ = "report_runs"
    __table_args__ = (
        UniqueConstraint("report_id", "scheduled_for", name="uq_report_runs_schedule"),
        Index("ix_report_runs_status_created_at", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    report_id: Mapped[UUID] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    trigger: Mapped[RunTrigger] = mapped_column(string_enum_type(RunTrigger, "run_trigger"), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[RunStatus] = mapped_column(string_enum_type(RunStatus, "run_status"), default=RunStatus.QUEUED, server_default="queued", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    items_seen: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    items_selected: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    result_markdown: Mapped[str | None] = mapped_column(Text)
    error_summary: Mapped[str | None] = mapped_column(Text)

    report: Mapped[Report] = relationship(back_populates="runs")
    source_results: Mapped[list[SourceRunResult]] = relationship(back_populates="report_run", cascade="all, delete-orphan", passive_deletes=True)


class SourceRunResult(TimestampMixin, Base):
    __tablename__ = "source_run_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    report_run_id: Mapped[UUID] = mapped_column(ForeignKey("report_runs.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[SourceRunStatus] = mapped_column(string_enum_type(SourceRunStatus, "source_run_status"), nullable=False)
    items_found: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text)

    report_run: Mapped[ReportRun] = relationship(back_populates="source_results")
    source: Mapped[Source] = relationship(back_populates="run_results")
