# PostgreSQL RLS Rollout Plan

Date: 2026-03-06

## Goal
在現有應用層 tenant filter 之外，新增 PostgreSQL Row-Level Security 作為資料庫層硬隔離。

## Included Artifacts
- Migration: `alembic/versions/t8_1_tenant_rls.py`
- App toggle: `RLS_ENFORCEMENT_ENABLED` in `app/config.py`
- Session context injection in `app/api/deps.py`

## Scope (Phase 1 tables)
- `documents`
- `documentchunks`
- `conversations`
- `messages` (via `conversations.tenant_id`)
- `retrievaltraces`
- `chat_feedbacks`
- `auditlogs`
- `usagerecords`

## Rollout Steps
1. **Deploy code only** (do not enable toggle)
   - Keep `RLS_ENFORCEMENT_ENABLED=false`
2. **Run migration**
   - Apply `t8_1_tenant_rls`
3. **Canary enable**
   - Set `RLS_ENFORCEMENT_ENABLED=true` in staging / one canary env
4. **Verify**
   - Cross-tenant reads return empty/forbidden
   - Same-tenant access unaffected
   - Superuser flow still works (bypass flag)
5. **Full enable**
   - Turn on `RLS_ENFORCEMENT_ENABLED=true` in production

## Verification SQL
```sql
-- Current context
select current_setting('app.tenant_id', true), current_setting('app.bypass_rls', true);

-- Should only see own tenant rows when bypass=0
select count(*) from documents;
select count(*) from conversations;

-- Policy list
select schemaname, tablename, policyname, permissive, roles, cmd
from pg_policies
where tablename in (
  'documents','documentchunks','conversations','messages',
  'retrievaltraces','chat_feedbacks','auditlogs','usagerecords'
)
order by tablename, policyname;
```

## Known Risks / Notes
- If application DB role is table owner or superuser, RLS may be bypassed by PostgreSQL semantics.
- For strict enforcement, use dedicated non-owner app role in production.
- Celery/background jobs that require cross-tenant operations should explicitly set bypass context or run with privileged role.

## Rollback
1. Set `RLS_ENFORCEMENT_ENABLED=false`
2. Run Alembic downgrade for `t8_1_tenant_rls`
