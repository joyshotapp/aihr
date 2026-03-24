"""Alembic migration: add billing_records table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "t9_1_billing_records"
down_revision = "t8_4_admin_totp_mfa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "billing_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("external_id", sa.String(255), nullable=True, unique=True),
        sa.Column("amount_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("plan", sa.String(50), nullable=True),
        sa.Column("period_start", sa.DateTime, nullable=True),
        sa.Column("period_end", sa.DateTime, nullable=True),
        sa.Column("invoice_number", sa.String(100), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("billing_records")
