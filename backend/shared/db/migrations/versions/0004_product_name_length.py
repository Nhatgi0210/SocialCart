"""Align product names and historical snapshots with the 200-character contract."""
import sqlalchemy as sa
from alembic import op

revision = "0004_product_name_length"
down_revision = "0003_contract_fields"
branch_labels = None
depends_on = None

COLUMNS = (("products", "name"), ("order_items", "product_name_snapshot"))


def upgrade():
    for table, column in COLUMNS:
        op.alter_column(table, column, existing_type=sa.String(100), type_=sa.String(200), existing_nullable=False)


def downgrade():
    for table, column in COLUMNS:
        count = op.get_bind().execute(sa.text(f"SELECT COUNT(*) FROM {table} WHERE CHAR_LENGTH({column}) > 100")).scalar()
        if count:
            raise RuntimeError(f"Cannot downgrade: {table}.{column} contains names longer than 100 characters")
    for table, column in COLUMNS:
        op.alter_column(table, column, existing_type=sa.String(200), type_=sa.String(100), existing_nullable=False)
