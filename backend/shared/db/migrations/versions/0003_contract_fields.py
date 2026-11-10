"""Persist fields already required by the public/internal contracts."""
from alembic import op
import sqlalchemy as sa

revision = "0003_contract_fields"
down_revision = "0002_user_name"
branch_labels = depends_on = None


def upgrade():
    if not op.get_context().as_sql:
        invalid = op.get_bind().execute(sa.text(
            "SELECT COUNT(*) FROM orders o LEFT JOIN conversations c ON c.id=o.conversation_id "
            "WHERE o.total_amount < 1 OR (o.conversation_id IS NOT NULL AND "
            "(c.id IS NULL OR c.customer_id <> o.customer_id))"
        )).scalar()
        if invalid:
            raise RuntimeError("Existing orders violate total/customer constraints; repair data before upgrade")
    op.create_unique_constraint("uq_conversation_customer", "conversations", ["id", "customer_id"])
    op.create_foreign_key("fk_order_conversation_customer", "orders", "conversations", ["conversation_id", "customer_id"], ["id", "customer_id"])
    op.drop_constraint("ck_order_total_nonneg", "orders", type_="check")
    op.create_check_constraint("ck_order_total_nonneg", "orders", "total_amount >= 1")
    op.add_column("conversations", sa.Column("ai_context", sa.JSON(), nullable=True))
    op.add_column("messages", sa.Column("error_code", sa.String(100), nullable=True))
    op.add_column("messages", sa.Column("delivery_unknown", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("variants", sa.Column("low_stock_threshold", sa.Integer(), nullable=False, server_default="0"))
    op.create_check_constraint("ck_variant_threshold_nonneg", "variants", "low_stock_threshold >= 0")
    op.alter_column("ai_faqs", "question", existing_type=sa.String(500), type_=sa.String(1000), existing_nullable=False)
    op.add_column("ai_faqs", sa.Column("trigger_keywords", sa.JSON(), nullable=True))
    op.execute(sa.text("UPDATE ai_faqs SET trigger_keywords = JSON_ARRAY() WHERE trigger_keywords IS NULL"))
    op.alter_column("ai_faqs", "trigger_keywords", existing_type=sa.JSON(), nullable=False)


def downgrade():
    # Refuse lossy rollback if a question no longer fits the previous schema.
    if op.get_bind().execute(sa.text("SELECT COUNT(*) FROM ai_faqs WHERE CHAR_LENGTH(question) > 500")).scalar():
        raise RuntimeError("FAQ questions exceed 500 characters; shorten them before downgrade")
    op.drop_column("ai_faqs", "trigger_keywords")
    op.alter_column("ai_faqs", "question", existing_type=sa.String(1000), type_=sa.String(500), existing_nullable=False)
    op.drop_constraint("ck_variant_threshold_nonneg", "variants", type_="check")
    op.drop_column("variants", "low_stock_threshold")
    op.drop_column("messages", "delivery_unknown")
    op.drop_column("messages", "error_code")
    op.drop_column("conversations", "ai_context")
    op.drop_constraint("fk_order_conversation_customer", "orders", type_="foreignkey")
    op.drop_constraint("uq_conversation_customer", "conversations", type_="unique")
    op.drop_constraint("ck_order_total_nonneg", "orders", type_="check")
    op.create_check_constraint("ck_order_total_nonneg", "orders", "total_amount >= 0")
