"""add per-run lease heartbeats for stale recovery."""

from alembic import op
import sqlalchemy as sa


revision = "20260721_04"
down_revision = "20260720_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("report_runs", sa.Column("heartbeat_at", sa.DateTime(timezone=True)))
    op.create_index("ix_report_runs_status_heartbeat_at", "report_runs", ["status", "heartbeat_at"])


def downgrade() -> None:
    op.drop_index("ix_report_runs_status_heartbeat_at", table_name="report_runs")
    op.drop_column("report_runs", "heartbeat_at")
