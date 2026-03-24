"""admin_totp_mfa

Revision ID: t8_4_admin_totp_mfa
"""
from alembic import op
import sqlalchemy as sa


revision = "t8_4_admin_totp_mfa"
down_revision = "t8_3_custom_domain_ssl_automation"
branch_labels = None
depends_on = None


def _user_table_name() -> str:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("users"):
        return "users"
    if inspector.has_table("user"):
        return "user"
    return "users"


def upgrade() -> None:
    table_name = _user_table_name()
    op.add_column(table_name, sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column(table_name, sa.Column("mfa_secret", sa.String(length=64), nullable=True))
    op.add_column(table_name, sa.Column("mfa_enabled_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    table_name = _user_table_name()
    op.drop_column(table_name, "mfa_enabled_at")
    op.drop_column(table_name, "mfa_secret")
    op.drop_column(table_name, "mfa_enabled")