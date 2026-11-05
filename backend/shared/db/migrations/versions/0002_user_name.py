"""Persist the seller name required by the existing auth contract."""
from alembic import op
import sqlalchemy as sa

revision = "0002_user_name"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("name", sa.String(100), nullable=True))
    op.execute(sa.text("UPDATE users SET name = 'Chủ shop' WHERE name IS NULL"))
    op.alter_column("users", "name", existing_type=sa.String(100), nullable=False)


def downgrade():
    op.drop_column("users", "name")
