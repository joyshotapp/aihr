"""add agreed_to_terms and agreed_at to users

Revision ID: t10_1
Revises: t9_1_billing_records
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa

revision = "t10_1"
down_revision = "t9_1_billing_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("agreed_to_terms", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("agreed_at", sa.DateTime(timezone=True), nullable=True))
    # Existing users are treated as having consented (they already use the service)
    op.execute("UPDATE users SET agreed_to_terms = true, agreed_at = created_at WHERE agreed_to_terms = false")


def downgrade() -> None:
    op.drop_column("users", "agreed_at")
    op.drop_column("users", "agreed_to_terms")
