"""Persist provider credentials, incoming jobs and uncertain send attempts."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import DATETIME, MEDIUMTEXT

revision = "0007_platform_delivery"
down_revision = "0006_order_idempotency_response"
branch_labels = depends_on = None


def upgrade():
    if not op.get_context().as_sql:
        duplicates = op.get_bind().execute(sa.text(
            "SELECT platform FROM platform_connections GROUP BY platform HAVING COUNT(*) > 1"
        )).first()
        if duplicates:
            raise RuntimeError("V1 permits one connection per platform. Resolve existing duplicate connections first.")
    op.create_unique_constraint("uq_platform_single", "platform_connections", ["platform"])
    op.add_column("platform_connections", sa.Column("last_error_code", sa.String(100)))
    op.alter_column("webhook_receipts", "raw_payload", existing_type=sa.Text(), type_=MEDIUMTEXT(), existing_nullable=False)
    op.add_column("webhook_outbox", sa.Column("receipt_id", sa.String(36)))
    op.create_foreign_key("fk_webhook_job_receipt", "webhook_outbox", "webhook_receipts", ["receipt_id"], ["id"])
    op.create_unique_constraint("uq_webhook_job_receipt", "webhook_outbox", ["receipt_id"])
    op.create_table("platform_dispatches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("message_id", sa.String(36), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("result", sa.JSON()),
        sa.Column("created_at", DATETIME(fsp=6), nullable=False), mysql_engine="InnoDB")


def downgrade():
    if op.get_bind().execute(sa.text(
        "SELECT COUNT(*) FROM webhook_receipts WHERE OCTET_LENGTH(raw_payload) > 65535"
    )).scalar():
        raise RuntimeError("Webhook payloads exceed the previous TEXT limit")
    op.drop_table("platform_dispatches")
    op.drop_constraint("fk_webhook_job_receipt", "webhook_outbox", type_="foreignkey")
    op.drop_constraint("uq_webhook_job_receipt", "webhook_outbox", type_="unique")
    op.drop_column("webhook_outbox", "receipt_id")
    op.alter_column("webhook_receipts", "raw_payload", existing_type=MEDIUMTEXT(), type_=sa.Text(), existing_nullable=False)
    op.drop_column("platform_connections", "last_error_code")
    op.drop_constraint("uq_platform_single", "platform_connections", type_="unique")
