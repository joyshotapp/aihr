"""
T8-1 PostgreSQL Tenant RLS baseline
===================================

建立 app schema helper functions，並在核心 tenant-scoped tables 啟用 RLS policies。

注意：實際是否在應用層注入 app.tenant_id 由 settings.RLS_ENFORCEMENT_ENABLED 控制。
"""

from alembic import op


# revision identifiers
revision = "t8_1_tenant_rls"
down_revision = "t7_5_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS app")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app.current_tenant_id()
        RETURNS uuid
        LANGUAGE sql
        STABLE
        AS $$
          SELECT nullif(current_setting('app.tenant_id', true), '')::uuid
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app.is_bypass_rls()
        RETURNS boolean
        LANGUAGE sql
        STABLE
        AS $$
          SELECT current_setting('app.bypass_rls', true) = '1'
        $$;
        """
    )

    # documents
    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS p_documents_tenant_isolation ON documents")
    op.execute(
        """
        CREATE POLICY p_documents_tenant_isolation ON documents
        USING (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        """
    )

    # documentchunks
    op.execute("ALTER TABLE documentchunks ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS p_documentchunks_tenant_isolation ON documentchunks")
    op.execute(
        """
        CREATE POLICY p_documentchunks_tenant_isolation ON documentchunks
        USING (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        """
    )

    # conversations
    op.execute("ALTER TABLE conversations ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS p_conversations_tenant_isolation ON conversations")
    op.execute(
        """
        CREATE POLICY p_conversations_tenant_isolation ON conversations
        USING (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        """
    )

    # messages (透過 conversation tenant 做隔離)
    op.execute("ALTER TABLE messages ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS p_messages_tenant_isolation ON messages")
    op.execute(
        """
        CREATE POLICY p_messages_tenant_isolation ON messages
        USING (
          app.is_bypass_rls()
          OR EXISTS (
              SELECT 1
              FROM conversations c
              WHERE c.id = messages.conversation_id
                AND c.tenant_id = app.current_tenant_id()
          )
        )
        WITH CHECK (
          app.is_bypass_rls()
          OR EXISTS (
              SELECT 1
              FROM conversations c
              WHERE c.id = messages.conversation_id
                AND c.tenant_id = app.current_tenant_id()
          )
        )
        """
    )

    # retrieval traces
    op.execute("ALTER TABLE retrievaltraces ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS p_retrievaltraces_tenant_isolation ON retrievaltraces")
    op.execute(
        """
        CREATE POLICY p_retrievaltraces_tenant_isolation ON retrievaltraces
        USING (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        """
    )

    # feedback
    op.execute("ALTER TABLE chat_feedbacks ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS p_chat_feedbacks_tenant_isolation ON chat_feedbacks")
    op.execute(
        """
        CREATE POLICY p_chat_feedbacks_tenant_isolation ON chat_feedbacks
        USING (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        """
    )

    # audit + usage
    op.execute("ALTER TABLE auditlogs ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS p_auditlogs_tenant_isolation ON auditlogs")
    op.execute(
        """
        CREATE POLICY p_auditlogs_tenant_isolation ON auditlogs
        USING (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        """
    )

    op.execute("ALTER TABLE usagerecords ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS p_usagerecords_tenant_isolation ON usagerecords")
    op.execute(
        """
        CREATE POLICY p_usagerecords_tenant_isolation ON usagerecords
        USING (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        WITH CHECK (tenant_id = app.current_tenant_id() OR app.is_bypass_rls())
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS p_usagerecords_tenant_isolation ON usagerecords")
    op.execute("ALTER TABLE usagerecords DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS p_auditlogs_tenant_isolation ON auditlogs")
    op.execute("ALTER TABLE auditlogs DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS p_chat_feedbacks_tenant_isolation ON chat_feedbacks")
    op.execute("ALTER TABLE chat_feedbacks DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS p_retrievaltraces_tenant_isolation ON retrievaltraces")
    op.execute("ALTER TABLE retrievaltraces DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS p_messages_tenant_isolation ON messages")
    op.execute("ALTER TABLE messages DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS p_conversations_tenant_isolation ON conversations")
    op.execute("ALTER TABLE conversations DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS p_documentchunks_tenant_isolation ON documentchunks")
    op.execute("ALTER TABLE documentchunks DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS p_documents_tenant_isolation ON documents")
    op.execute("ALTER TABLE documents DISABLE ROW LEVEL SECURITY")

    op.execute("DROP FUNCTION IF EXISTS app.is_bypass_rls()")
    op.execute("DROP FUNCTION IF EXISTS app.current_tenant_id()")
