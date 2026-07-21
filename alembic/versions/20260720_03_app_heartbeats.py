"""add application heartbeat rows for container health probes."""

from alembic import op
import sqlalchemy as sa


revision = "20260720_03"
down_revision = "20260720_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_heartbeats",
        sa.Column("role", sa.String(length=64), primary_key=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_heartbeats")
