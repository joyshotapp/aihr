import logging
from datetime import datetime, timezone
from uuid import UUID

from app.celery_app import celery_app
from app.db.session import create_session
from app.middleware.custom_domain import invalidate_domain_cache
from app.models.custom_domain import CustomDomain
from app.models.tenant import Tenant
from app.services.custom_domain_ssl import run_ssl_provisioning

logger = logging.getLogger("unihr.custom_domain.ssl")


@celery_app.task(name="app.tasks.custom_domain_tasks.provision_custom_domain_ssl_task")
def provision_custom_domain_ssl_task(domain_id: str, tenant_id: str) -> dict:
    db = None
    try:
        db = create_session(tenant_id=tenant_id)
        record = db.query(CustomDomain).filter(
            CustomDomain.id == UUID(domain_id),
            CustomDomain.tenant_id == UUID(tenant_id),
        ).first()
        if not record:
            logger.warning("Custom domain %s not found for tenant %s", domain_id, tenant_id)
            return {"status": "missing"}

        if not record.verified:
            record.ssl_status = "pending_dns"
            record.ssl_last_error = "Domain verification is incomplete"
            db.commit()
            return {"status": "pending_dns"}

        record.ssl_status = "provisioning"
        record.ssl_last_error = None
        record.ssl_requested_at = datetime.now(timezone.utc)
        db.commit()

        result = run_ssl_provisioning(record.domain)
        if not result.success:
            record.ssl_status = "failed"
            record.ssl_last_error = result.detail
            db.commit()
            logger.error("SSL provisioning failed for %s: %s", record.domain, result.detail)
            return {"status": "failed", "detail": result.detail}

        record.ssl_provisioned = True
        record.ssl_status = "provisioned"
        record.ssl_last_error = None
        record.ssl_provisioned_at = datetime.now(timezone.utc)

        tenant = db.query(Tenant).filter(Tenant.id == UUID(tenant_id)).first()
        if tenant and record.verified:
            tenant.custom_domain = record.domain

        db.commit()
        invalidate_domain_cache(record.domain)
        logger.info("SSL provisioned for %s", record.domain)
        return {"status": "provisioned", "detail": result.detail}
    except Exception as exc:
        logger.exception("Unexpected SSL provisioning error for domain %s", domain_id)
        if db is not None:
            record = db.query(CustomDomain).filter(CustomDomain.id == UUID(domain_id)).first()
            if record:
                record.ssl_status = "failed"
                record.ssl_last_error = str(exc)[:500]
                db.commit()
        return {"status": "failed", "detail": str(exc)}
    finally:
        if db is not None:
            db.close()