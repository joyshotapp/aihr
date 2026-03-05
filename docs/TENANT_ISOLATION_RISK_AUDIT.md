# Tenant Isolation Risk Audit (P0)

Date: 2026-03-06

## Scope
- `app/api/v1/endpoints/chat.py`
- `app/api/v1/endpoints/documents.py`
- `app/crud/crud_chat.py`
- `app/crud/crud_document.py`
- `app/services/kb_retrieval.py`

## High-risk Patterns Found
1. ID-only lookup followed by application-layer ownership checks.
2. Metadata lookup in retrieval path without tenant condition.
3. Feedback message validation accepted cross-tenant/cross-user message IDs.

## Remediation Applied
1. Added tenant+user scoped CRUD accessors in chat module:
   - `get_conversation_for_user`
   - `get_message_by_id_for_user`
   - `delete_conversation_for_user`
2. Updated chat endpoints to use scoped CRUD accessors directly.
3. Added tenant-scoped document CRUD accessors:
   - `get_for_tenant`
   - `get_chunks_for_tenant`
   - `delete_for_tenant`
4. Updated document endpoints to use tenant-scoped accessors for non-superuser flow.
5. Added tenant filters for document metadata resolution in `kb_retrieval` (semantic and BM25 path).

## Residual Risk
- Database-level RLS is still not enabled; current controls are application-layer + query-layer defense-in-depth.
- Superuser flow still allows cross-tenant access by design.

## Next Recommended Step
- Implement PostgreSQL RLS for `documents`, `document_chunks`, `conversations`, `messages`, `chat_feedback`, `retrieval_traces`.
