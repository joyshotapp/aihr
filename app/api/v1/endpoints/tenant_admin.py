"""
租戶自助管理後台 API（T3-2）
各租戶 Owner/Admin 可自行管理公司設定、用戶、查看用量摘要
"""

from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr

from app.api import deps
from app.api.deps_permissions import require_admin
from app.models.user import User
from app.models.tenant import Tenant
from app.models.document import Document
from app.models.audit import UsageRecord
from app.models.chat import Conversation
from app.models.sso_config import TenantSSOConfig
from app.crud import crud_tenant, crud_user
from app.schemas.tenant import QuotaStatus

router = APIRouter()


# ═══════════════════════════════════════════
#  Response Schemas
# ═══════════════════════════════════════════


class CompanyProfile(BaseModel):
    id: str
    name: str
    plan: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    user_count: int = 0
    document_count: int = 0
    conversation_count: int = 0


class CompanyUserInfo(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class InviteUserRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "employee"


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None  # active / suspended


import re as _re
from pydantic import field_validator

_HEX_COLOR_RE = _re.compile(r"^#[0-9a-fA-F]{6}$")
_SAFE_URL_RE = _re.compile(r"^https?://")


class BrandingSettings(BaseModel):
    brand_name: Optional[str] = None
    brand_logo_url: Optional[str] = None
    brand_primary_color: Optional[str] = None
    brand_secondary_color: Optional[str] = None
    brand_favicon_url: Optional[str] = None

    @field_validator("brand_primary_color", "brand_secondary_color", mode="before")
    @classmethod
    def validate_hex_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not _HEX_COLOR_RE.match(v):
            raise ValueError("色碼格式須為 #RRGGBB（如 #3b82f6）")
        return v

    @field_validator("brand_logo_url", "brand_favicon_url", mode="before")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not _SAFE_URL_RE.match(v):
            raise ValueError("URL 須以 https:// 或 http:// 開頭")
        if len(v) > 500:
            raise ValueError("URL 長度不可超過 500 字元")
        return v


class BrandingPublic(BaseModel):
    """Public branding info (no auth required — used by login page)."""

    brand_name: Optional[str] = None
    brand_logo_url: Optional[str] = None
    brand_primary_color: Optional[str] = None
    brand_secondary_color: Optional[str] = None
    brand_favicon_url: Optional[str] = None
    tenant_name: str = ""


class CompanyDashboard(BaseModel):
    company_name: str
    plan: Optional[str] = None
    user_count: int = 0
    document_count: int = 0
    conversation_count: int = 0
    monthly_queries: int = 0
    monthly_tokens: int = 0
    monthly_cost: float = 0.0
    quota_status: Optional[QuotaStatus] = None


class OnboardingStep(BaseModel):
    key: str
    title: str
    completed: bool
    description: str


class OnboardingStatus(BaseModel):
    tenant_id: str
    tenant_name: str
    progress_percent: int
    completed_steps: int
    total_steps: int
    next_step: Optional[str] = None
    steps: List[OnboardingStep]


# ═══════════════════════════════════════════
#  Company Dashboard
# ═══════════════════════════════════════════


@router.get("/dashboard", response_model=CompanyDashboard)
def company_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """
    公司儀表板 — Owner/Admin 查看公司概況與配額狀態
    """
    tid = current_user.tenant_id
    tenant = crud_tenant.get(db, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_count = db.query(func.count(User.id)).filter(User.tenant_id == tid).scalar() or 0
    doc_count = db.query(func.count(Document.id)).filter(Document.tenant_id == tid).scalar() or 0
    conv_count = db.query(func.count(Conversation.id)).filter(Conversation.tenant_id == tid).scalar() or 0

    # 月度使用量
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly = (
        db.query(
            func.count(UsageRecord.id).label("queries"),
            func.coalesce(func.sum(UsageRecord.input_tokens + UsageRecord.output_tokens), 0).label("tokens"),
            func.coalesce(func.sum(UsageRecord.estimated_cost_usd), 0).label("cost"),
        )
        .filter(
            UsageRecord.tenant_id == tid,
            UsageRecord.created_at >= month_start,
        )
        .first()
    )

    quota_data = crud_tenant.get_quota_status(db, tid)
    quota = QuotaStatus(**quota_data) if quota_data else None

    return CompanyDashboard(
        company_name=tenant.name,
        plan=tenant.plan,
        user_count=user_count,
        document_count=doc_count,
        conversation_count=conv_count,
        monthly_queries=monthly.queries or 0,
        monthly_tokens=int(monthly.tokens or 0),
        monthly_cost=float(monthly.cost or 0),
        quota_status=quota,
    )


@router.get("/onboarding", response_model=OnboardingStatus)
def get_onboarding_status(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """Return tenant onboarding progress for a frontend setup wizard."""
    tid = current_user.tenant_id
    tenant = crud_tenant.get(db, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_count = db.query(func.count(User.id)).filter(User.tenant_id == tid).scalar() or 0
    doc_count = db.query(func.count(Document.id)).filter(Document.tenant_id == tid).scalar() or 0
    sso_enabled = (
        db.query(func.count(TenantSSOConfig.id))
        .filter(TenantSSOConfig.tenant_id == tid, TenantSSOConfig.enabled)
        .scalar()
        or 0
    ) > 0
    branding_done = any(
        [
            tenant.brand_name,
            tenant.brand_logo_url,
            tenant.brand_primary_color,
            tenant.brand_secondary_color,
            tenant.brand_favicon_url,
        ]
    )

    steps = [
        OnboardingStep(
            key="company_profile",
            title="確認公司資料",
            completed=bool(tenant.name and tenant.name.strip()),
            description="確認租戶名稱與基本公司資料。",
        ),
        OnboardingStep(
            key="invite_team",
            title="邀請團隊成員",
            completed=user_count > 1,
            description="邀請至少一位同事加入租戶。",
        ),
        OnboardingStep(
            key="upload_documents",
            title="上傳第一批文件",
            completed=doc_count > 0,
            description="上傳內規或 HR 文件建立知識庫。",
        ),
        OnboardingStep(
            key="configure_branding",
            title="設定品牌樣式",
            completed=branding_done,
            description="設定品牌名稱、Logo 或主色系。",
        ),
        OnboardingStep(
            key="configure_sso",
            title="啟用 SSO",
            completed=sso_enabled,
            description="設定 Google 或 Microsoft SSO。",
        ),
    ]

    completed_steps = sum(1 for step in steps if step.completed)
    total_steps = len(steps)
    progress_percent = int((completed_steps / total_steps) * 100) if total_steps else 0
    next_step = next((step.key for step in steps if not step.completed), None)

    return OnboardingStatus(
        tenant_id=str(tenant.id),
        tenant_name=tenant.name,
        progress_percent=progress_percent,
        completed_steps=completed_steps,
        total_steps=total_steps,
        next_step=next_step,
        steps=steps,
    )


# ═══════════════════════════════════════════
#  Company Settings
# ═══════════════════════════════════════════


@router.get("/profile", response_model=CompanyProfile)
def get_company_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """查看公司資訊"""
    tid = current_user.tenant_id
    tenant = crud_tenant.get(db, tid)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_count = db.query(func.count(User.id)).filter(User.tenant_id == tid).scalar() or 0
    doc_count = db.query(func.count(Document.id)).filter(Document.tenant_id == tid).scalar() or 0
    conv_count = db.query(func.count(Conversation.id)).filter(Conversation.tenant_id == tid).scalar() or 0

    return CompanyProfile(
        id=str(tenant.id),
        name=tenant.name,
        plan=tenant.plan,
        status=tenant.status,
        created_at=tenant.created_at,
        user_count=user_count,
        document_count=doc_count,
        conversation_count=conv_count,
    )


@router.get("/quota", response_model=QuotaStatus)
def get_company_quota(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """查看公司配額狀態"""
    status_data = crud_tenant.get_quota_status(db, current_user.tenant_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return QuotaStatus(**status_data)


# ═══════════════════════════════════════════
#  User Management (Self-service)
# ═══════════════════════════════════════════


@router.get("/users", response_model=List[CompanyUserInfo])
def list_company_users(
    role: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """列出公司所有使用者"""
    q = db.query(User).filter(User.tenant_id == current_user.tenant_id)
    if role:
        q = q.filter(User.role == role)
    if status_filter:
        q = q.filter(User.status == status_filter)
    users = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [
        CompanyUserInfo(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            status=u.status,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("/users/invite")
def invite_user(
    invite: InviteUserRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    透過 Email 邀請新使用者加入公司
    Owner/Admin 限定；收到邀請信的人透過 /auth/accept-invite 完成註冊
    """

    # 配額檢查
    quota = crud_tenant.check_quota(db, current_user.tenant_id, "user")
    if not quota.get("allowed", True):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=quota["message"],
        )

    # 不能建立 owner（只有 superuser 可以）
    if invite.role == "owner" and not current_user.is_superuser:
        if current_user.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有 Owner 可以指派 Owner 角色",
            )

    # 檢查 email
    existing = crud_user.get_by_email(db, email=invite.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="此 Email 已被使用")

    # 產生邀請 token 並寄送 email
    from app.core.security import create_invite_token
    from app.services.email_service import send_invitation_email

    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    token = create_invite_token(
        email=invite.email,
        tenant_id=str(current_user.tenant_id),
        role=invite.role,
    )
    send_invitation_email(
        to_email=invite.email,
        invite_token=token,
        tenant_name=tenant.name if tenant else "UniHR",
        inviter_name=current_user.full_name or current_user.email,
    )

    return {"msg": "邀請信已寄出", "email": invite.email}


@router.put("/users/{user_id}", response_model=CompanyUserInfo)
def update_company_user(
    user_id: UUID,
    update: UpdateUserRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """更新公司使用者角色/狀態"""

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if target.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="無法管理其他公司的使用者")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="無法修改自己的角色/狀態")

    # Admin 不能改 Owner
    if current_user.role == "admin" and target.role == "owner":
        raise HTTPException(status_code=403, detail="Admin 無法修改 Owner")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target, field, value)
    db.add(target)
    db.commit()
    db.refresh(target)

    return CompanyUserInfo(
        id=str(target.id),
        email=target.email,
        full_name=target.full_name,
        role=target.role,
        status=target.status,
        created_at=target.created_at,
    )


@router.delete("/users/{user_id}")
def deactivate_company_user(
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """停用公司使用者（軟刪除）"""

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if target.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="無法管理其他公司的使用者")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="無法停用自己")
    if current_user.role == "admin" and target.role == "owner":
        raise HTTPException(status_code=403, detail="Admin 無法停用 Owner")

    target.status = "suspended"
    db.add(target)
    db.commit()

    return {"message": f"使用者 {target.email} 已停用", "user_id": str(user_id)}


# ═══════════════════════════════════════════
#  Usage Summary (Self-service)
# ═══════════════════════════════════════════


@router.get("/usage/summary")
def company_usage_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """查看公司用量摘要"""
    from app.crud.crud_audit import get_usage_summary
    from datetime import datetime as dt

    kwargs = {"tenant_id": current_user.tenant_id}
    if start_date:
        kwargs["start_date"] = dt.fromisoformat(start_date)
    if end_date:
        kwargs["end_date"] = dt.fromisoformat(end_date)

    return get_usage_summary(db, **kwargs)


@router.get("/usage/by-user")
def company_usage_by_user(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """查看每位使用者的用量"""
    tid = current_user.tenant_id
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    rows = (
        db.query(
            User.email,
            User.full_name,
            func.count(UsageRecord.id).label("queries"),
            func.coalesce(func.sum(UsageRecord.input_tokens + UsageRecord.output_tokens), 0).label("tokens"),
            func.coalesce(func.sum(UsageRecord.estimated_cost_usd), 0).label("cost"),
        )
        .outerjoin(
            UsageRecord,
            (UsageRecord.user_id == User.id) & (UsageRecord.created_at >= month_start),
        )
        .filter(User.tenant_id == tid)
        .group_by(User.id, User.email, User.full_name)
        .order_by(func.sum(UsageRecord.estimated_cost_usd).desc().nullslast())
        .all()
    )

    return [
        {
            "email": r.email,
            "full_name": r.full_name,
            "monthly_queries": r.queries or 0,
            "monthly_tokens": int(r.tokens or 0),
            "monthly_cost": float(r.cost or 0),
        }
        for r in rows
    ]


# ═══════════════════════════════════════════
#  White-Label Branding (T4-3)
# ═══════════════════════════════════════════


@router.get("/branding", response_model=BrandingSettings)
def get_branding(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """取得公司品牌設定"""
    tenant = crud_tenant.get(db, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return BrandingSettings(
        brand_name=tenant.brand_name,
        brand_logo_url=tenant.brand_logo_url,
        brand_primary_color=tenant.brand_primary_color,
        brand_secondary_color=tenant.brand_secondary_color,
        brand_favicon_url=tenant.brand_favicon_url,
    )


@router.put("/branding", response_model=BrandingSettings)
def update_branding(
    branding: BrandingSettings,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """更新公司品牌設定（白標）"""

    # Only pro / enterprise plans can customize branding
    tenant = crud_tenant.get(db, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if tenant.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="白標功能需要 Pro 或 Enterprise 方案",
        )

    update_data = branding.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return BrandingSettings(
        brand_name=tenant.brand_name,
        brand_logo_url=tenant.brand_logo_url,
        brand_primary_color=tenant.brand_primary_color,
        brand_secondary_color=tenant.brand_secondary_color,
        brand_favicon_url=tenant.brand_favicon_url,
    )


# ═══════════════════════════════════════════
#  Quality Monitoring Dashboard (Phase 13)
# ═══════════════════════════════════════════


class DocumentQualitySummary(BaseModel):
    total_documents: int = 0
    completed: int = 0
    failed: int = 0
    avg_quality_score: Optional[float] = None
    quality_distribution: dict = {}
    low_quality_documents: list = []


class RetrievalQualitySummary(BaseModel):
    total_queries: int = 0
    avg_chunk_score: Optional[float] = None
    low_score_queries: int = 0
    score_distribution: dict = {}


class QualityDashboard(BaseModel):
    document_quality: DocumentQualitySummary
    retrieval_quality: RetrievalQualitySummary


@router.get("/quality/dashboard", response_model=QualityDashboard)
def quality_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_admin),
) -> Any:
    """租戶資料處理與檢索品質監控儀表板"""
    from datetime import timedelta
    from app.models.chat import RetrievalTrace

    tenant_id = current_user.tenant_id
    since = datetime.utcnow() - timedelta(days=days)

    # ── 1. Document Quality ──
    docs = db.query(Document).filter(Document.tenant_id == tenant_id, Document.created_at >= since).all()

    completed_docs = [d for d in docs if d.status == "completed"]
    failed_docs = [d for d in docs if d.status == "failed"]

    quality_scores = []
    quality_dist = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
    low_quality_list = []

    for d in completed_docs:
        qr = d.quality_report or {}
        score = qr.get("quality_score")
        if score is not None:
            quality_scores.append(score)
            if score >= 0.9:
                quality_dist["excellent"] += 1
            elif score >= 0.7:
                quality_dist["good"] += 1
            elif score >= 0.5:
                quality_dist["fair"] += 1
            else:
                quality_dist["poor"] += 1
                low_quality_list.append(
                    {
                        "id": str(d.id),
                        "filename": d.filename,
                        "quality_score": round(score, 3),
                        "quality_level": qr.get("quality_level", "unknown"),
                        "warnings": qr.get("warnings", []),
                    }
                )

    avg_quality = round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else None
    low_quality_list.sort(key=lambda x: x["quality_score"])
    low_quality_list = low_quality_list[:10]

    doc_summary = DocumentQualitySummary(
        total_documents=len(docs),
        completed=len(completed_docs),
        failed=len(failed_docs),
        avg_quality_score=avg_quality,
        quality_distribution=quality_dist,
        low_quality_documents=low_quality_list,
    )

    # ── 2. Retrieval Quality ──
    traces = (
        db.query(RetrievalTrace)
        .filter(
            RetrievalTrace.tenant_id == tenant_id,
            RetrievalTrace.created_at >= since,
        )
        .all()
    )

    chunk_scores_all = []
    low_score_count = 0
    score_dist = {"0.0-0.3": 0, "0.3-0.5": 0, "0.5-0.7": 0, "0.7-0.9": 0, "0.9-1.0": 0}

    for t in traces:
        sources = t.sources_json or {}
        all_sources = []
        if isinstance(sources, dict):
            for v in sources.values():
                if isinstance(v, list):
                    all_sources.extend(v)
        elif isinstance(sources, list):
            all_sources = sources

        scores = [s.get("score", 0) for s in all_sources if isinstance(s, dict) and "score" in s]
        if scores:
            avg_s = sum(scores) / len(scores)
            chunk_scores_all.append(avg_s)
            if avg_s < 0.5:
                low_score_count += 1
            if avg_s < 0.3:
                score_dist["0.0-0.3"] += 1
            elif avg_s < 0.5:
                score_dist["0.3-0.5"] += 1
            elif avg_s < 0.7:
                score_dist["0.5-0.7"] += 1
            elif avg_s < 0.9:
                score_dist["0.7-0.9"] += 1
            else:
                score_dist["0.9-1.0"] += 1

    avg_chunk = round(sum(chunk_scores_all) / len(chunk_scores_all), 3) if chunk_scores_all else None

    retrieval_summary = RetrievalQualitySummary(
        total_queries=len(traces),
        avg_chunk_score=avg_chunk,
        low_score_queries=low_score_count,
        score_distribution=score_dist,
    )

    return QualityDashboard(
        document_quality=doc_summary,
        retrieval_quality=retrieval_summary,
    )
