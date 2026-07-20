"""initial InfoService schema."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260720_01"
down_revision = None
branch_labels = None
depends_on = None

credential_source = postgresql.ENUM("user", "platform", name="credential_source", create_type=False)
credential_status = postgresql.ENUM("unknown", "valid", "invalid", name="credential_status", create_type=False)
schedule_kind = postgresql.ENUM("daily", "weekdays", "weekly", "cron", name="schedule_kind", create_type=False)
run_trigger = postgresql.ENUM("scheduled", "manual", name="run_trigger", create_type=False)
run_status = postgresql.ENUM("queued", "running", "succeeded", "partial", "failed", name="run_status", create_type=False)
source_run_status = postgresql.ENUM("succeeded", "failed", name="source_run_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in (credential_source, credential_status, schedule_kind, run_trigger, run_status, source_run_status):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("language", sa.String(16), server_default="en", nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("telegram_user_id", name="uq_users_telegram_user_id"),
        sa.UniqueConstraint("chat_id", name="uq_users_chat_id"),
    )
    op.create_table(
        "llm_credentials",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("credential_source", credential_source, nullable=False),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("base_url", sa.String(2048)),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("key_mask", sa.String(255), nullable=False),
        sa.Column("validation_status", credential_status, nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_llm_credentials_user_provider"),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("language", sa.String(16), server_default="en", nullable=False),
        sa.Column("lookback_hours", sa.Integer(), server_default="24", nullable=False),
        sa.Column("ai_score_threshold", sa.Float(), server_default="7", nullable=False),
        sa.Column("max_items", sa.Integer(), server_default="10", nullable=False),
        sa.Column("categories", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("exclusions", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("custom_instruction", sa.Text()),
        sa.Column("schedule_kind", schedule_kind, nullable=False),
        sa.Column("schedule_value", sa.String(128), nullable=False),
        sa.Column("timezone", sa.String(64)),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("ai_score_threshold >= 0 AND ai_score_threshold <= 10", name="ck_reports_ai_score_threshold"),
        sa.CheckConstraint("max_items >= 1 AND max_items <= 30", name="ck_reports_max_items"),
    )
    op.create_index("ix_reports_user_id", "reports", ["user_id"])
    op.create_index("ix_reports_enabled_next_run_at", "reports", ["enabled", "next_run_at"])
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("report_id", sa.Uuid(), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_sources_report_id", "sources", ["report_id"])
    op.create_table(
        "report_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("report_id", sa.Uuid(), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger", run_trigger, nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", run_status, server_default="queued", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("items_seen", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_selected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("result_markdown", sa.Text()),
        sa.Column("error_summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("report_id", "scheduled_for", name="uq_report_runs_schedule"),
    )
    op.create_index("ix_report_runs_status_created_at", "report_runs", ["status", "created_at"])
    op.create_table(
        "source_run_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("report_run_id", sa.Uuid(), sa.ForeignKey("report_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", source_run_status, nullable=False),
        sa.Column("items_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    for table_name in ("source_run_results", "report_runs", "sources", "reports", "llm_credentials", "users"):
        op.drop_table(table_name)
    bind = op.get_bind()
    for enum_type in (source_run_status, run_status, run_trigger, schedule_kind, credential_status, credential_source):
        enum_type.drop(bind, checkfirst=True)
