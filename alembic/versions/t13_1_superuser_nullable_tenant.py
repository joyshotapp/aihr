"""Allow superuser accounts to have NULL tenant_id (platform-level accounts)

Revision ID: t13_1_superuser_nullable_tenant
Revises: t12_1
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa

revision = "t13_1"
down_revision = "t12_1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the NOT NULL constraint on users.tenant_id
    # Superuser platform accounts do not belong to any tenant
    op.alter_column(
        "users",
        "tenant_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    # Re-apply NOT NULL (will fail if any NULL rows exist — remove them first)
    op.alter_column(
        "users",
        "tenant_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
