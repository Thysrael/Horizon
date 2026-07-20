"""add durable run claim metadata."""

from alembic import op
import sqlalchemy as sa


revision = "20260720_02"
down_revision = "20260720_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("report_runs", sa.Column("worker_id", sa.String(255)))
    op.add_column("report_runs", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("report_runs", "attempt_count")
    op.drop_column("report_runs", "worker_id")
