"""add email_verified fields to users

Revision ID: t11_1
Revises: t10_1
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa


revision = "t11_1"
down_revision = "t10_1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    # Backfill: existing users are considered verified (they were created via invite)
    op.execute("UPDATE users SET email_verified = true, email_verified_at = created_at")


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email_verified")
