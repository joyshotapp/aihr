# UniHR Data Deletion SOP

Last Updated: 2026-03-23

## 1. Purpose

This SOP defines how UniHR executes deletion requests for:

- a single document;
- a user account;
- a full tenant offboarding or purge request.

## 2. Systems in Scope

- PostgreSQL application database
- Cloudflare R2 object storage
- Pinecone vector index
- Redis cache / queue state
- Audit and usage records
- Backups and monitoring artifacts

## 3. Trigger Types

- Customer self-service deletion in product
- Customer support or legal deletion request
- Contract termination / tenant offboarding
- Security or compliance-directed purge

## 4. Roles and Approvals

- Request owner: Customer owner/admin or authorized internal operator
- Executor: Engineering or Operations
- Reviewer: Security / Operations lead for tenant purge requests
- Evidence owner: Operations

## 5. Single Document Deletion

Execution steps:

1. Validate tenant ownership and request authorization.
2. Delete document metadata and chunks from PostgreSQL.
3. Delete source object from R2 using the stored object key.
4. Delete corresponding vectors from Pinecone namespace for the tenant.
5. Invalidate related caches or retrieval artifacts if present.
6. Record the deletion action in audit logs or operations log.

Verification:

- PostgreSQL document and chunk records are absent.
- R2 object no longer exists.
- Pinecone vectors for the document are absent.
- Document no longer appears in retrieval or UI listings.

## 6. User Deletion or Deactivation

Default behavior:

- suspend access first when legal retention or audit continuity is required;
- permanently delete only when contractually and legally permitted.

Execution steps:

1. Confirm requester authority and target identity.
2. Revoke active sessions, refresh tokens, invitations, and SSO access where applicable.
3. Deactivate or delete the user record in PostgreSQL.
4. Preserve audit trails unless prohibited by law.
5. Confirm that the user can no longer authenticate.

## 7. Tenant Offboarding / Full Purge

Execution steps:

1. Confirm signed offboarding or deletion authorization.
2. Export customer data if contract or request requires return before deletion.
3. Freeze tenant access to prevent new uploads or modifications.
4. Delete tenant-scoped application data from PostgreSQL.
5. Delete tenant-scoped objects from R2.
6. Delete tenant namespace data from Pinecone.
7. Remove tenant-scoped Redis cache keys and queue artifacts where present.
8. Revoke SSO configs, domains, invitations, and API credentials for the tenant.
9. Preserve only records that must be retained for legal, financial, or security reasons.
10. Record completion evidence and final approver sign-off.

## 8. Backup Handling

- Backups are not edited in place.
- Deleted data may remain in encrypted backups until backup expiration.
- Backup retention period must be disclosed to customers in contract or policy materials.
- Restores from backup must not reintroduce deleted tenants into live production systems without explicit authorization and re-deletion review.

## 9. Evidence Required

For each deletion request, retain:

- request ticket or authorization reference;
- executor and reviewer names;
- execution timestamp;
- affected tenant / user / document identifiers;
- verification evidence for DB, object storage, vector store, and access revocation;
- exception notes for retained data.

## 10. Standard Verification Checklist

- PostgreSQL rows removed or appropriately deactivated
- R2 object removal confirmed
- Pinecone namespace or vectors removed
- Redis cache/session cleanup completed
- User access revoked
- Audit entry or operations log recorded
- Customer notified of completion when required

## 11. Exceptions

Deletion may be delayed or partially limited when:

- law requires preservation of financial, employment, tax, or security records;
- active litigation hold or regulatory inquiry exists;
- backup media retention period has not yet expired.

All exceptions must be documented and approved.

## 12. Operational Notes for UniHR

- RLS and tenant-scoped CRUD controls reduce cross-tenant deletion risk but do not replace explicit verification.
- Purge jobs should be executed with privileged operational context and audited.
- Large tenant deletions should be performed during a controlled maintenance window with rollback considerations for platform stability, but not to restore deleted customer data without approval.