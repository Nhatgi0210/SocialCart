"""Allow the cached response to include large order snapshots."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import MEDIUMTEXT

revision = "0006_order_idempotency_response"
down_revision = "0005_realtime_outbox"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("request_idempotency", "response_body", existing_type=sa.Text(),
                    type_=MEDIUMTEXT(), existing_nullable=True)


def downgrade():
    if op.get_bind().execute(sa.text(
        "SELECT COUNT(*) FROM request_idempotency WHERE OCTET_LENGTH(response_body) > 65535"
    )).scalar():
        raise RuntimeError("Cached idempotency responses exceed the TEXT limit")
    op.alter_column("request_idempotency", "response_body", existing_type=MEDIUMTEXT(),
                    type_=sa.Text(), existing_nullable=True)
