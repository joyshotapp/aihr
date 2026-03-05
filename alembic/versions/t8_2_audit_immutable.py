"""audit_immutable – 不可竄改稽核事件（第 18 項）

加入：
  - auditlogs.content_hash  VARCHAR(64)  — 欄位正規化 SHA-256
  - auditlogs.expires_at    TIMESTAMPTZ  — 留存到期時間（預設 created_at + 7 年）
  - DB TRIGGER prevent_audit_modification — BEFORE UPDATE / DELETE 直接 RAISE

Revision ID: t8_2_audit_immutable
Revises: t8_1_tenant_rls
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "t8_2_audit_immutable"
down_revision = "t8_1_tenant_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── 1. 新增欄位 ───
    op.add_column(
        "auditlogs",
        sa.Column(
            "content_hash",
            sa.String(64),
            nullable=True,
            comment="SHA-256 of (tenant_id|actor_user_id|action|target_type|target_id|created_at)"
        ),
    )
    op.add_column(
        "auditlogs",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="留存期限（到期後可由系統清除，到期前禁止刪除）"
        ),
    )
    op.create_index("ix_auditlogs_expires_at", "auditlogs", ["expires_at"])

    # ─── 2. 回填現有資料的 expires_at（created_at + 7 年）───
    op.execute("""
        UPDATE auditlogs
        SET expires_at = created_at + INTERVAL '7 years'
        WHERE expires_at IS NULL
    """)

    # ─── 3. 建立防竄改 trigger function ───
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                -- 未到期的記錄禁止刪除
                IF OLD.expires_at IS NULL OR OLD.expires_at > now() THEN
                    RAISE EXCEPTION
                        'auditlogs: record % cannot be deleted before expiry (expires_at=%)',
                        OLD.id, OLD.expires_at;
                END IF;
                RETURN OLD;  -- 允許刪除已到期記錄
            ELSIF TG_OP = 'UPDATE' THEN
                -- 任何更新都禁止
                RAISE EXCEPTION
                    'auditlogs: record % is immutable and cannot be updated',
                    OLD.id;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ─── 4. 附加 trigger ───
    op.execute("""
        DROP TRIGGER IF EXISTS audit_immutable ON auditlogs;
        CREATE TRIGGER audit_immutable
        BEFORE UPDATE OR DELETE ON auditlogs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_immutable ON auditlogs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_modification();")
    op.drop_index("ix_auditlogs_expires_at", table_name="auditlogs")
    op.drop_column("auditlogs", "expires_at")
    op.drop_column("auditlogs", "content_hash")
