"""Persist realtime invalidations separately from platform send jobs."""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import DATETIME

revision = "0005_realtime_outbox"
down_revision = "0004_product_name_length"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "realtime_outbox",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", DATETIME(fsp=6), nullable=True),
        sa.Column("created_at", DATETIME(fsp=6), nullable=False),
        sa.Column("sent_at", DATETIME(fsp=6), nullable=True),
        sa.CheckConstraint("attempt_count >= 0", name="ck_realtime_attempts_nonneg"),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_realtime_outbox_pending", "realtime_outbox", ["sent_at", "next_attempt_at", "created_at"])


def downgrade():
    op.drop_table("realtime_outbox")
