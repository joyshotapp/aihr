"""
平台管理後台 API（Superuser 專用）
提供跨租戶管理、平台統計、系統健康監控等功能
"""

from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel

from app.api import deps
from app.api.deps_permissions import require_superuser
from app.models.user import User
from app.models.tenant import Tenant
from app.models.document import Document
from app.models.audit import AuditLog, UsageRecord
from app.models.chat import Conversation
from app.models.feedback import ChatFeedback
from app.crud import crud_tenant
from app.schemas.tenant import TenantUpdate, QuotaUpdate, QuotaStatus, PLAN_QUOTAS
from app.services.quota_alerts import QuotaAlertService, QuotaAlert
from app.observability.metrics import snapshot as metrics_snapshot

router = APIRouter()


# ═══════════════════════════════════════════
#  Response Schemas
# ═══════════════════════════════════════════


class TenantSummary(BaseModel):
    id: str
    name: str
    plan: Optional[str]
    status: Optional[str]
    created_at: Optional[datetime]
    user_count: int = 0
    document_count: int = 0
    total_actions: int = 0
    total_cost: float = 0.0


class PlatformDashboard(BaseModel):
    total_tenants: int
    active_tenants: int
    total_users: int
    active_users: int
    total_documents: int
    total_conversations: int
    total_actions: int
    total_cost: float
    # 近 7 天趨勢
    daily_actions: list  # [{date, count, cost}]
    top_tenants: list  # [{name, actions, cost}]


class TenantDetailStats(BaseModel):
    tenant_id: str
    tenant_name: str
    plan: Optional[str]
    status: Optional[str]
    created_at: Optional[datetime]
    user_count: int
    document_count: int
    conversation_count: int
    total_input_tokens: int
    total_output_tokens: int
    total_pinecone_queries: int
    total_embedding_calls: int
    total_cost: float
    total_actions: int
    recent_actions: list  # last 10 audit logs
    users: list  # user list


class AdminUserInfo(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: Optional[str]
    status: Optional[str]
    tenant_id: str
    tenant_name: Optional[str]
    department_name: Optional[str]
    created_at: Optional[datetime]


class SystemHealth(BaseModel):
    status: str  # healthy / degraded
    database: str
    redis: str
    uptime_seconds: float
    python_version: str
    active_connections: int
    api_metrics: dict[str, Any]
    backend_api_metrics: dict[str, Any]
    observability: dict[str, Any]
    task_summary: dict[str, Any]


class LLMQualitySummary(BaseModel):
    tenant_id: Optional[str] = None
    window_days: int
    trace_count: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    positive_feedback: int = 0
    negative_feedback: int = 0
    positive_feedback_rate: Optional[float] = None
    langfuse_enabled: bool = False
    source: str = "unavailable"


def _count_task_items(items_by_worker: Any) -> int:
    if not isinstance(items_by_worker, dict):
        return 0
    total = 0
    for items in items_by_worker.values():
        if isinstance(items, list):
            total += len(items)
    return total


def _get_celery_task_snapshot() -> dict[str, Any]:
    from app.celery_app import celery_app
    from app.core.redis_client import get_redis_client

    try:
        inspect = celery_app.control.inspect(timeout=3)
        ping = inspect.ping() if inspect else None
        active = inspect.active() if inspect else None
        reserved = inspect.reserved() if inspect else None
        scheduled = inspect.scheduled() if inspect else None
    except Exception as exc:
        return {
            "workers_online": 0,
            "worker_names": [],
            "ping_ok": False,
            "active_tasks": 0,
            "reserved_tasks": 0,
            "scheduled_tasks": 0,
            "queue_depth": {},
            "error": str(exc),
        }

    redis_client = get_redis_client()
    queue_depth: dict[str, int] = {}
    if redis_client is not None:
        for queue_name in ("celery", "bulk"):
            try:
                queue_depth[queue_name] = int(redis_client.llen(queue_name))
            except Exception:
                queue_depth[queue_name] = -1

    worker_names = sorted((ping or {}).keys()) if isinstance(ping, dict) else []
    return {
        "workers_online": len(worker_names),
        "worker_names": worker_names,
        "ping_ok": bool(worker_names),
        "active_tasks": _count_task_items(active),
        "reserved_tasks": _count_task_items(reserved),
        "scheduled_tasks": _count_task_items(scheduled),
        "queue_depth": queue_depth,
    }


async def _fetch_backend_observability() -> dict[str, Any]:
    from app.config import settings
    import httpx

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.BACKEND_INTERNAL_URL.rstrip('/')}/internal/observability/summary")
            response.raise_for_status()
            return response.json()
    except Exception:
        return {
            "service": "backend-api",
            "api_metrics": metrics_snapshot("backend-api"),
            "sentry_enabled": False,
            "langfuse_enabled": False,
        }


# ═══════════════════════════════════════════
#  Platform Dashboard
# ═══════════════════════════════════════════


@router.get("/dashboard", response_model=PlatformDashboard)
def platform_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """平台總覽儀表板"""

    # Basic counts
    total_tenants = db.query(func.count(Tenant.id)).scalar() or 0
    active_tenants = db.query(func.count(Tenant.id)).filter(Tenant.status == "active").scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.status == "active").scalar() or 0
    total_documents = db.query(func.count(Document.id)).scalar() or 0
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0

    # Usage aggregates
    usage_agg = db.query(
        func.count(UsageRecord.id).label("total_actions"),
        func.coalesce(func.sum(UsageRecord.estimated_cost_usd), 0).label("total_cost"),
    ).first()
    total_actions = usage_agg.total_actions or 0
    total_cost = float(usage_agg.total_cost or 0)

    # Daily actions for last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_rows = (
        db.query(
            func.date(UsageRecord.created_at).label("date"),
            func.count(UsageRecord.id).label("count"),
            func.coalesce(func.sum(UsageRecord.estimated_cost_usd), 0).label("cost"),
        )
        .filter(UsageRecord.created_at >= seven_days_ago)
        .group_by(func.date(UsageRecord.created_at))
        .order_by(func.date(UsageRecord.created_at))
        .all()
    )
    daily_actions = [{"date": str(r.date), "count": r.count, "cost": float(r.cost)} for r in daily_rows]

    # Top 5 tenants by cost
    top_rows = (
        db.query(
            Tenant.name,
            func.count(UsageRecord.id).label("actions"),
            func.coalesce(func.sum(UsageRecord.estimated_cost_usd), 0).label("cost"),
        )
        .join(UsageRecord, UsageRecord.tenant_id == Tenant.id)
        .group_by(Tenant.name)
        .order_by(func.sum(UsageRecord.estimated_cost_usd).desc())
        .limit(5)
        .all()
    )
    top_tenants = [{"name": r.name, "actions": r.actions, "cost": float(r.cost)} for r in top_rows]

    return PlatformDashboard(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        total_users=total_users,
        active_users=active_users,
        total_documents=total_documents,
        total_conversations=total_conversations,
        total_actions=total_actions,
        total_cost=total_cost,
        daily_actions=daily_actions,
        top_tenants=top_tenants,
    )


# ═══════════════════════════════════════════
#  Tenant Management
# ═══════════════════════════════════════════


@router.get("/tenants", response_model=List[TenantSummary])
def list_all_tenants(
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """全租戶列表（含用量摘要）"""
    # Subqueries to avoid N+1 (was: 3 queries per tenant in a loop)
    user_counts = db.query(User.tenant_id, func.count(User.id).label("cnt")).group_by(User.tenant_id).subquery()
    doc_counts = (
        db.query(Document.tenant_id, func.count(Document.id).label("cnt")).group_by(Document.tenant_id).subquery()
    )
    usage_agg = (
        db.query(
            UsageRecord.tenant_id,
            func.count(UsageRecord.id).label("actions"),
            func.coalesce(func.sum(UsageRecord.estimated_cost_usd), 0).label("cost"),
        )
        .group_by(UsageRecord.tenant_id)
        .subquery()
    )

    q = (
        db.query(
            Tenant,
            func.coalesce(user_counts.c.cnt, 0).label("user_count"),
            func.coalesce(doc_counts.c.cnt, 0).label("doc_count"),
            func.coalesce(usage_agg.c.actions, 0).label("total_actions"),
            func.coalesce(usage_agg.c.cost, 0).label("total_cost"),
        )
        .outerjoin(user_counts, Tenant.id == user_counts.c.tenant_id)
        .outerjoin(doc_counts, Tenant.id == doc_counts.c.tenant_id)
        .outerjoin(usage_agg, Tenant.id == usage_agg.c.tenant_id)
    )
    if status:
        q = q.filter(Tenant.status == status)
    if search:
        q = q.filter(Tenant.name.ilike(f"%{search}%"))

    rows = q.order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for t, user_count, doc_count, total_actions, total_cost in rows:
        result.append(
            TenantSummary(
                id=str(t.id),
                name=t.name,
                plan=t.plan,
                status=t.status,
                created_at=t.created_at,
                user_count=user_count,
                document_count=doc_count,
                total_actions=total_actions,
                total_cost=float(total_cost),
            )
        )
    return result


@router.get("/tenants/{tenant_id}/stats", response_model=TenantDetailStats)
def tenant_detail_stats(
    tenant_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """單租戶詳細統計"""
    tenant = crud_tenant.get(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    user_count = db.query(func.count(User.id)).filter(User.tenant_id == tenant_id).scalar() or 0
    doc_count = db.query(func.count(Document.id)).filter(Document.tenant_id == tenant_id).scalar() or 0
    conv_count = db.query(func.count(Conversation.id)).filter(Conversation.tenant_id == tenant_id).scalar() or 0

    usage_agg = (
        db.query(
            func.count(UsageRecord.id).label("total_actions"),
            func.coalesce(func.sum(UsageRecord.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(UsageRecord.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(UsageRecord.pinecone_queries), 0).label("pinecone_queries"),
            func.coalesce(func.sum(UsageRecord.embedding_calls), 0).label("embedding_calls"),
            func.coalesce(func.sum(UsageRecord.estimated_cost_usd), 0).label("total_cost"),
        )
        .filter(UsageRecord.tenant_id == tenant_id)
        .first()
    )

    # Recent audit logs
    recent_logs = (
        db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).order_by(AuditLog.created_at.desc()).limit(10).all()
    )
    recent_actions = [
        {
            "id": str(log.id),
            "action": log.action,
            "actor_user_id": str(log.actor_user_id) if log.actor_user_id else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in recent_logs
    ]

    # User list
    users = db.query(User).filter(User.tenant_id == tenant_id).order_by(User.created_at).all()
    user_list = [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "status": u.status,
        }
        for u in users
    ]

    return TenantDetailStats(
        tenant_id=str(tenant.id),
        tenant_name=tenant.name,
        plan=tenant.plan,
        status=tenant.status,
        created_at=tenant.created_at,
        user_count=user_count,
        document_count=doc_count,
        conversation_count=conv_count,
        total_input_tokens=int(usage_agg.input_tokens or 0),
        total_output_tokens=int(usage_agg.output_tokens or 0),
        total_pinecone_queries=int(usage_agg.pinecone_queries or 0),
        total_embedding_calls=int(usage_agg.embedding_calls or 0),
        total_cost=float(usage_agg.total_cost or 0),
        total_actions=int(usage_agg.total_actions or 0),
        recent_actions=recent_actions,
        users=user_list,
    )


@router.put("/tenants/{tenant_id}")
def update_tenant_admin(
    tenant_id: UUID,
    tenant_in: TenantUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """調整租戶狀態/方案"""
    tenant = crud_tenant.get(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    updated = crud_tenant.update(db, db_obj=tenant, obj_in=tenant_in)
    return {
        "id": str(updated.id),
        "name": updated.name,
        "plan": updated.plan,
        "status": updated.status,
    }


# ═══════════════════════════════════════════
#  Cross-tenant User Search
# ═══════════════════════════════════════════


@router.get("/users", response_model=List[AdminUserInfo])
def search_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    tenant_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """跨租戶用戶搜尋"""
    from sqlalchemy.orm import joinedload

    q = db.query(User).options(
        joinedload(User.tenant),
        joinedload(User.department),
    )
    if search:
        q = q.filter((User.email.ilike(f"%{search}%")) | (User.full_name.ilike(f"%{search}%")))
    if role:
        q = q.filter(User.role == role)
    if tenant_id:
        q = q.filter(User.tenant_id == tenant_id)

    users = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for u in users:
        result.append(
            AdminUserInfo(
                id=str(u.id),
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                status=u.status,
                tenant_id=str(u.tenant_id),
                tenant_name=u.tenant.name if u.tenant else None,
                department_name=u.department.name if u.department else None,
                created_at=u.created_at,
            )
        )
    return result


# ═══════════════════════════════════════════
#  System Health
# ═══════════════════════════════════════════


@router.get("/system/health", response_model=SystemHealth)
async def system_health(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """系統健康狀態"""
    import sys
    import time
    import redis as redis_lib

    start = time.time()

    # Database check
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    # Redis check
    redis_status = "healthy"
    try:
        from app.config import settings

        r = redis_lib.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        r.ping()
        r.close()
    except Exception:
        redis_status = "unavailable"

    active_connections = 0
    try:
        active_connections = int(db.execute(text("SELECT count(*) FROM pg_stat_activity")).scalar() or 0)
    except Exception:
        active_connections = 0

    backend_observability = await _fetch_backend_observability()
    admin_api_metrics = metrics_snapshot("admin-api")
    task_summary = _get_celery_task_snapshot()
    overall = "healthy" if db_status == "healthy" and task_summary.get("ping_ok", False) else "degraded"

    return SystemHealth(
        status=overall,
        database=db_status,
        redis=redis_status,
        uptime_seconds=round(time.time() - start, 3),
        python_version=sys.version.split()[0],
        active_connections=active_connections,
        api_metrics=admin_api_metrics,
        backend_api_metrics=backend_observability.get("api_metrics", {}),
        observability={
            "sentry_enabled": bool(backend_observability.get("sentry_enabled")),
            "langfuse_enabled": bool(backend_observability.get("langfuse_enabled")),
        },
        task_summary=task_summary,
    )


@router.get("/system/tasks")
def system_tasks(
    current_user: User = Depends(require_superuser),
) -> Any:
    """背景任務與 queue 狀態摘要"""
    return _get_celery_task_snapshot()


@router.get("/llm/quality", response_model=LLMQualitySummary)
async def llm_quality_summary(
    tenant_id: Optional[UUID] = None,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    from app.config import settings
    import base64
    import httpx
    import json

    since = datetime.utcnow() - timedelta(days=days)
    feedback_query = db.query(ChatFeedback).filter(ChatFeedback.created_at >= since)
    if tenant_id:
        feedback_query = feedback_query.filter(ChatFeedback.tenant_id == tenant_id)

    positive_feedback = feedback_query.filter(ChatFeedback.rating == 2).count()
    negative_feedback = feedback_query.filter(ChatFeedback.rating == 1).count()
    total_feedback = positive_feedback + negative_feedback
    positive_feedback_rate = round(positive_feedback / total_feedback, 4) if total_feedback else None

    langfuse_enabled = bool(
        settings.LANGFUSE_ENABLED and settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY
    )
    if not langfuse_enabled:
        return LLMQualitySummary(
            tenant_id=str(tenant_id) if tenant_id else None,
            window_days=days,
            positive_feedback=positive_feedback,
            negative_feedback=negative_feedback,
            positive_feedback_rate=positive_feedback_rate,
            langfuse_enabled=False,
            source="feedback-only",
        )

    query: dict[str, Any] = {
        "view": "observations",
        "metrics": [
            {"measure": "count", "aggregation": "count"},
            {"measure": "latency", "aggregation": "avg"},
            {"measure": "latency", "aggregation": "p95"},
            {"measure": "totalCost", "aggregation": "sum"},
        ],
        "fromTimestamp": since.isoformat() + "Z",
        "toTimestamp": datetime.utcnow().isoformat() + "Z",
    }
    if tenant_id:
        query["filters"] = [
            {
                "column": "metadata",
                "operator": "equals",
                "key": "tenant_id",
                "value": str(tenant_id),
                "type": "stringObject",
            }
        ]

    token = base64.b64encode(
        f"{settings.LANGFUSE_PUBLIC_KEY}:{settings.LANGFUSE_SECRET_KEY}".encode("utf-8")
    ).decode("utf-8")
    endpoints = [
        f"{settings.LANGFUSE_HOST.rstrip('/')}/api/public/v2/metrics",
        f"{settings.LANGFUSE_HOST.rstrip('/')}/api/public/metrics",
    ]

    for endpoint in endpoints:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(
                    endpoint,
                    params={"query": json.dumps(query)},
                    headers={"Authorization": f"Basic {token}"},
                )
                response.raise_for_status()
                payload = response.json()
                rows = payload.get("data", []) if isinstance(payload, dict) else []
                metrics = rows[0].get("metrics", {}) if rows else {}
                return LLMQualitySummary(
                    tenant_id=str(tenant_id) if tenant_id else None,
                    window_days=days,
                    trace_count=int(metrics.get("count", 0) or 0),
                    avg_latency_ms=round(float(metrics.get("latency_avg", 0) or 0), 2),
                    p95_latency_ms=round(float(metrics.get("latency_p95", 0) or 0), 2),
                    total_cost_usd=round(float(metrics.get("totalCost_sum", 0) or 0), 6),
                    positive_feedback=positive_feedback,
                    negative_feedback=negative_feedback,
                    positive_feedback_rate=positive_feedback_rate,
                    langfuse_enabled=True,
                    source="langfuse",
                )
        except Exception:
            continue

    return LLMQualitySummary(
        tenant_id=str(tenant_id) if tenant_id else None,
        window_days=days,
        positive_feedback=positive_feedback,
        negative_feedback=negative_feedback,
        positive_feedback_rate=positive_feedback_rate,
        langfuse_enabled=True,
        source="langfuse-unreachable",
    )


# ═══════════════════════════════════════════
#  Quota Management
# ═══════════════════════════════════════════


@router.get("/tenants/{tenant_id}/quota", response_model=QuotaStatus)
def get_tenant_quota(
    tenant_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """查看租戶配額狀態（含使用量與使用率）"""
    status_data = crud_tenant.get_quota_status(db, tenant_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return QuotaStatus(**status_data)


@router.put("/tenants/{tenant_id}/quota", response_model=QuotaStatus)
def update_tenant_quota(
    tenant_id: UUID,
    quota_in: QuotaUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """設定租戶配額"""
    tenant = crud_tenant.get(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = quota_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    status_data = crud_tenant.get_quota_status(db, tenant_id)
    return QuotaStatus(**status_data)


@router.post("/tenants/{tenant_id}/quota/apply-plan")
def apply_plan_quota(
    tenant_id: UUID,
    plan: str = Query(..., description="方案: free, pro, enterprise"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """套用方案預設配額至租戶"""
    tenant = crud_tenant.get(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if plan not in PLAN_QUOTAS:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}")

    defaults = PLAN_QUOTAS[plan]
    tenant.plan = plan
    for field, value in defaults.items():
        setattr(tenant, field, value)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return {
        "message": f"已套用 {plan} 方案配額",
        "plan": plan,
        "quotas": defaults,
    }


@router.get("/tenants/{tenant_id}/alerts")
def get_tenant_alerts(
    tenant_id: UUID,
    alert_type: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """查詢租戶告警記錄"""
    tenant = crud_tenant.get(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    alerts = QuotaAlertService.get_alerts(db, tenant_id, alert_type=alert_type, limit=limit)
    return [
        {
            "id": str(a.id),
            "alert_type": a.alert_type,
            "resource": a.resource,
            "current_value": a.current_value,
            "limit_value": a.limit_value,
            "usage_ratio": a.usage_ratio,
            "message": a.message,
            "notified": a.notified,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]


@router.post("/tenants/{tenant_id}/alerts/check")
def check_tenant_alerts(
    tenant_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """手動觸發租戶配額檢查並建立告警"""
    tenant = crud_tenant.get(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    new_alerts = QuotaAlertService.check_and_create_alerts(db, tenant_id)
    return {
        "tenant_id": str(tenant_id),
        "new_alerts": len(new_alerts),
        "alerts": new_alerts,
    }


@router.get("/quota/plans")
def list_plan_quotas(
    current_user: User = Depends(require_superuser),
) -> Any:
    """列出所有方案預設配額"""
    return PLAN_QUOTAS


# ═══════════════════════════════════════════
#  Monitoring Center（跨租戶聚合）
# ═══════════════════════════════════════════


@router.get("/monitoring/alerts")
def get_monitoring_alerts(
    alert_type: Optional[str] = None,
    resource: Optional[str] = None,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(200, le=500),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """跨租戶配額告警聚合，供監控中心使用。"""
    since = datetime.utcnow() - timedelta(days=days)
    q = (
        db.query(QuotaAlert, Tenant.name.label("tenant_name"))
        .join(Tenant, Tenant.id == QuotaAlert.tenant_id)
        .filter(QuotaAlert.created_at >= since)
    )
    if alert_type:
        q = q.filter(QuotaAlert.alert_type == alert_type)
    if resource:
        q = q.filter(QuotaAlert.resource == resource)

    rows = q.order_by(QuotaAlert.created_at.desc()).limit(limit).all()

    alerts = [
        {
            "id": str(a.id),
            "tenant_id": str(a.tenant_id),
            "tenant_name": tenant_name,
            "alert_type": a.alert_type,
            "resource": a.resource,
            "current_value": a.current_value,
            "limit_value": a.limit_value,
            "usage_ratio": a.usage_ratio,
            "message": a.message,
            "notified": a.notified,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a, tenant_name in rows
    ]

    return {
        "total": len(alerts),
        "exceeded_count": sum(1 for a in alerts if a["alert_type"] == "exceeded"),
        "warning_count": sum(1 for a in alerts if a["alert_type"] == "warning"),
        "alerts": alerts,
    }


# ═══════════════════════════════════════════
#  Security Isolation Config
# ═══════════════════════════════════════════


@router.get("/tenants/{tenant_id}/security")
def get_tenant_security(
    tenant_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """查看租戶安全組態"""
    from app.services.security_isolation import (
        get_security_config,
        SecurityConfigResponse,
    )

    tenant = crud_tenant.get(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    config = get_security_config(db, tenant_id)
    if not config:
        return SecurityConfigResponse(
            tenant_id=str(tenant_id),
            isolation_level="standard",
        )
    return SecurityConfigResponse(
        tenant_id=str(config.tenant_id),
        isolation_level=config.isolation_level,
        pinecone_index_name=config.pinecone_index_name,
        pinecone_namespace=config.pinecone_namespace,
        encryption_key_id=config.encryption_key_id,
        data_retention_days=config.data_retention_days,
        ip_whitelist=config.ip_whitelist,
        require_mfa=config.require_mfa,
        audit_log_export_enabled=config.audit_log_export_enabled,
    )


@router.put("/tenants/{tenant_id}/security")
def update_tenant_security(
    tenant_id: UUID,
    update_data: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_superuser),
) -> Any:
    """更新租戶安全組態"""
    from app.services.security_isolation import (
        create_or_update_security_config,
        SecurityConfigUpdate,
        SecurityConfigResponse,
    )

    tenant = crud_tenant.get(db, tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    valid_levels = {"standard", "enhanced", "dedicated"}
    if "isolation_level" in update_data and update_data["isolation_level"] not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid isolation level. Must be one of: {valid_levels}",
        )

    config_update = SecurityConfigUpdate(**update_data)
    config = create_or_update_security_config(db, tenant_id, config_update)
    return SecurityConfigResponse(
        tenant_id=str(config.tenant_id),
        isolation_level=config.isolation_level,
        pinecone_index_name=config.pinecone_index_name,
        pinecone_namespace=config.pinecone_namespace,
        encryption_key_id=config.encryption_key_id,
        data_retention_days=config.data_retention_days,
        ip_whitelist=config.ip_whitelist,
        require_mfa=config.require_mfa,
        audit_log_export_enabled=config.audit_log_export_enabled,
    )
