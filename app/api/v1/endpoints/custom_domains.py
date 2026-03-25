"""
Custom Domain Management API (T4-6)

Allows tenant Owner/Admin to:
  1. Add a custom domain
  2. Get DNS verification instructions (TXT record)
  3. Verify DNS (checks TXT record)
  4. List / delete custom domains
"""

import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.api.deps_permissions import require_admin
from app.models.custom_domain import CustomDomain
from app.models.tenant import Tenant
from app.models.user import User
from app.middleware.custom_domain import invalidate_domain_cache

router = APIRouter()
logger = logging.getLogger("unihr.custom_domain")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


# ── Schemas ──


class DomainCreate(BaseModel):
    domain: str


class DomainInfo(BaseModel):
    id: str
    domain: str
    verified: bool
    verification_token: str
    ssl_provisioned: bool
    ssl_status: str
    ssl_last_error: Optional[str] = None
    ssl_requested_at: Optional[str] = None
    ssl_provisioned_at: Optional[str] = None
    created_at: Optional[str] = None


class DomainVerifyResult(BaseModel):
    domain: str
    verified: bool
    message: str


class DomainSSLProvisionResult(BaseModel):
    domain: str
    ssl_status: str
    message: str


# ── Helpers ──


def _generate_verification_token(tenant_id: str, domain: str) -> str:
    """Generate a deterministic verification token."""
    raw = f"unihr-verify-{tenant_id}-{domain}-{uuid.uuid4().hex[:8]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _serialize_dt(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _to_domain_info(record: CustomDomain) -> DomainInfo:
    return DomainInfo(
        id=str(record.id),
        domain=record.domain,
        verified=record.verified,
        verification_token=record.verification_token,
        ssl_provisioned=record.ssl_provisioned,
        ssl_status=record.ssl_status,
        ssl_last_error=record.ssl_last_error,
        ssl_requested_at=_serialize_dt(record.ssl_requested_at),
        ssl_provisioned_at=_serialize_dt(record.ssl_provisioned_at),
        created_at=_serialize_dt(record.created_at),
    )


def _queue_ssl_provisioning(db: Session, record: CustomDomain, tenant_id: str) -> bool:
    from app.services.custom_domain_ssl import ssl_automation_enabled

    if not ssl_automation_enabled():
        return False

    from app.tasks.custom_domain_tasks import provision_custom_domain_ssl_task

    record.ssl_status = "provisioning"
    record.ssl_last_error = None
    record.ssl_requested_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    provision_custom_domain_ssl_task.delay(str(record.id), tenant_id)
    return True


# ── Endpoints ──


@router.get("/", response_model=List[DomainInfo])
def list_domains(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """列出本租戶的所有自訂域名"""
    domains = (
        db.query(CustomDomain)
        .filter(CustomDomain.tenant_id == current_user.tenant_id)
        .order_by(CustomDomain.created_at.desc())
        .all()
    )

    return [_to_domain_info(d) for d in domains]


@router.post("/", response_model=DomainInfo, status_code=201)
def add_domain(
    body: DomainCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """新增自訂域名（需 Pro / Enterprise 方案）"""

    # Plan check
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant or tenant.plan not in ("pro", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="自訂域名需要 Pro 或 Enterprise 方案",
        )

    domain = body.domain.lower().strip()
    if not domain or not DOMAIN_RE.match(domain):
        raise HTTPException(status_code=400, detail="無效的域名格式")

    # Check uniqueness
    exists = db.query(CustomDomain).filter(CustomDomain.domain == domain).first()
    if exists:
        raise HTTPException(status_code=409, detail="此域名已被使用")

    token = _generate_verification_token(str(current_user.tenant_id), domain)
    record = CustomDomain(
        tenant_id=current_user.tenant_id,
        domain=domain,
        verification_token=token,
        ssl_status="pending_dns",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    invalidate_domain_cache(domain)

    logger.info("Custom domain added: %s for tenant %s", domain, current_user.tenant_id)

    return _to_domain_info(record)


@router.post("/{domain_id}/verify", response_model=DomainVerifyResult)
def verify_domain(
    domain_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """驗證域名 DNS TXT 記錄"""
    record = (
        db.query(CustomDomain)
        .filter(
            CustomDomain.id == domain_id,
            CustomDomain.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="域名不存在")

    if record.verified:
        if record.ssl_provisioned:
            return DomainVerifyResult(domain=record.domain, verified=True, message="域名已驗證")
        return DomainVerifyResult(
            domain=record.domain,
            verified=True,
            message="域名已驗證，等待 SSL 憑證完成後即可啟用",
        )

    # Attempt DNS TXT lookup
    verified = False
    try:
        import dns.resolver

        answers = dns.resolver.resolve(f"_unihr-verify.{record.domain}", "TXT")
        for rdata in answers:
            txt_value = rdata.to_text().strip('"')
            if txt_value == record.verification_token:
                verified = True
                break
    except ImportError:
        # dnspython not installed — allow manual verification via admin
        logger.warning("dnspython not installed, skipping DNS verification for %s", record.domain)
        return DomainVerifyResult(
            domain=record.domain,
            verified=False,
            message="DNS 驗證模組未安裝，請聯繫系統管理員",
        )
    except Exception as e:
        logger.info("DNS verification failed for %s: %s", record.domain, e)

    if verified:
        record.verified = True
        record.verified_at = datetime.now(timezone.utc)
        record.ssl_status = "ready"
        record.ssl_last_error = None
        if record.ssl_provisioned:
            # Only activate custom domain after SSL is ready
            tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
            if tenant:
                tenant.custom_domain = record.domain
        db.commit()
        db.refresh(record)
        invalidate_domain_cache(record.domain)
        logger.info("Domain verified: %s", record.domain)
        if record.ssl_provisioned:
            return DomainVerifyResult(domain=record.domain, verified=True, message="域名驗證成功！")

        try:
            queued = False
            from app.config import settings

            if settings.CUSTOM_DOMAIN_SSL_AUTO_REQUEST:
                queued = _queue_ssl_provisioning(db, record, str(current_user.tenant_id))
                if queued:
                    return DomainVerifyResult(
                        domain=record.domain,
                        verified=True,
                        message="域名驗證成功，已開始申請 SSL 憑證",
                    )
        except Exception as exc:
            logger.exception("Failed to queue SSL provisioning for %s", record.domain)
            record.ssl_status = "failed"
            record.ssl_last_error = str(exc)[:500]
            db.commit()

        return DomainVerifyResult(
            domain=record.domain,
            verified=True,
            message="域名驗證成功，等待 SSL 憑證完成後即可啟用",
        )
    else:
        return DomainVerifyResult(
            domain=record.domain,
            verified=False,
            message=f"驗證失敗。請在 DNS 新增 TXT 記錄：_unihr-verify.{record.domain} → {record.verification_token}",
        )


@router.post("/{domain_id}/ssl/provision", response_model=DomainSSLProvisionResult)
def provision_domain_ssl(
    domain_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """手動重新觸發 SSL 憑證申請。"""
    record = (
        db.query(CustomDomain)
        .filter(
            CustomDomain.id == domain_id,
            CustomDomain.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="域名不存在")

    if not record.verified:
        raise HTTPException(status_code=400, detail="請先完成 DNS 驗證")

    if record.ssl_provisioned:
        return DomainSSLProvisionResult(
            domain=record.domain,
            ssl_status="provisioned",
            message="SSL 憑證已就緒",
        )

    if record.ssl_status == "provisioning":
        return DomainSSLProvisionResult(
            domain=record.domain,
            ssl_status=record.ssl_status,
            message="SSL 憑證申請進行中",
        )

    from app.services.custom_domain_ssl import ssl_automation_enabled

    if not ssl_automation_enabled():
        raise HTTPException(
            status_code=503,
            detail="尚未設定 SSL 自動化命令，請聯繫系統管理員",
        )

    try:
        _queue_ssl_provisioning(db, record, str(current_user.tenant_id))
    except Exception as exc:
        logger.exception("Failed to queue SSL provisioning for %s", record.domain)
        record.ssl_status = "failed"
        record.ssl_last_error = str(exc)[:500]
        db.commit()
        raise HTTPException(status_code=500, detail="無法啟動 SSL 申請工作") from exc

    return DomainSSLProvisionResult(
        domain=record.domain,
        ssl_status="provisioning",
        message="已重新啟動 SSL 憑證申請",
    )


@router.delete("/{domain_id}")
def delete_domain(
    domain_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """刪除自訂域名"""

    record = (
        db.query(CustomDomain)
        .filter(
            CustomDomain.id == domain_id,
            CustomDomain.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="域名不存在")

    domain_name = record.domain

    # Clear tenant custom_domain if it matches
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if tenant and tenant.custom_domain == domain_name:
        tenant.custom_domain = None

    db.delete(record)
    db.commit()
    invalidate_domain_cache(domain_name)

    logger.info("Custom domain deleted: %s", domain_name)
    return {"message": f"域名 {domain_name} 已刪除"}
