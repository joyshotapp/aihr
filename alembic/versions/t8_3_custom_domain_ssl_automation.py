"""custom_domain_ssl_automation

Revision ID: t8_3_custom_domain_ssl_automation
"""
from alembic import op
import sqlalchemy as sa


revision = "t8_3_custom_domain_ssl_automation"
down_revision = ("t8_2_audit_immutable", "t4_19_multi_region")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customdomain", sa.Column("ssl_status", sa.String(length=32), nullable=True))
    op.add_column("customdomain", sa.Column("ssl_last_error", sa.String(length=500), nullable=True))
    op.add_column("customdomain", sa.Column("ssl_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("customdomain", sa.Column("ssl_provisioned_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        """
        UPDATE customdomain
        SET ssl_status = CASE
            WHEN verified = true AND ssl_provisioned = true THEN 'provisioned'
            WHEN verified = true THEN 'ready'
            ELSE 'pending_dns'
        END,
            ssl_provisioned_at = CASE
            WHEN ssl_provisioned = true THEN COALESCE(verified_at, created_at)
            ELSE NULL
        END
        """
    )

    op.alter_column("customdomain", "ssl_status", nullable=False, server_default="pending_dns")


def downgrade() -> None:
    op.drop_column("customdomain", "ssl_provisioned_at")
    op.drop_column("customdomain", "ssl_requested_at")
    op.drop_column("customdomain", "ssl_last_error")
    op.drop_column("customdomain", "ssl_status")