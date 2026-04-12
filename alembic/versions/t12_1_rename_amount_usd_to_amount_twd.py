"""Alembic migration: rename billing_records.amount_usd to amount_twd, currency default USD→TWD

Revision ID: t12_1_rename_amount_usd_to_amount_twd
Revises: t11_1_email_verified
Create Date: 2026-04-12
"""

from alembic import op

revision = "t12_1"
down_revision = "t11_1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("billing_records", "amount_usd", new_column_name="amount_twd")
    op.execute("ALTER TABLE billing_records ALTER COLUMN currency SET DEFAULT 'TWD'")
    # 修正既有紀錄的 currency（由 NewebPay 建立的都是 TWD）
    op.execute("UPDATE billing_records SET currency = 'TWD' WHERE currency = 'USD'")


def downgrade() -> None:
    op.execute("UPDATE billing_records SET currency = 'USD' WHERE currency = 'TWD'")
    op.execute("ALTER TABLE billing_records ALTER COLUMN currency SET DEFAULT 'USD'")
    op.alter_column("billing_records", "amount_twd", new_column_name="amount_usd")
