from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.audit import AuditLog, UsageRecord
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# 默認留存年限
_DEFAULT_RETENTION_YEARS = 7


def _compute_audit_hash(
    tenant_id: UUID,
    actor_user_id: Optional[UUID],
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    created_at_iso: str,
) -> str:
    """
    計算稽核事件的 SHA-256 內容雜湊。
    將關鍵欄位正規化為瀏別 '|' 的字串，確保對後做驗證時結果一致。
    """
    canonical = "|".join([
        str(tenant_id),
        str(actor_user_id) if actor_user_id else "",
        action,
        resource_type or "",
        resource_id or "",
        created_at_iso,
    ])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Audit Log CRUD
def create_audit_log(
    db: Session,
    *,
    tenant_id: UUID,
    actor_user_id: Optional[UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    retention_years: int = _DEFAULT_RETENTION_YEARS,
) -> AuditLog:
    from app.config import settings
    retention_years = getattr(settings, "AUDIT_RETENTION_YEARS", retention_years)

    now = datetime.now(timezone.utc)
    created_at_iso = now.isoformat()

    content_hash = _compute_audit_hash(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        created_at_iso=created_at_iso,
    )

    db_obj = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=resource_type,
        target_id=resource_id,
        detail_json=details,
        ip_address=ip_address,
        content_hash=content_hash,
        expires_at=now + timedelta(days=retention_years * 365),
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def verify_audit_log(db: Session, *, audit_log_id: UUID) -> Dict[str, Any]:
    """
    重新計算確認指定稽核記錄的內容雜湊是否一致。
    回傳 {"valid": bool, "reason": str}
    """
    log = db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
    if not log:
        return {"valid": False, "reason": "not_found"}
    if not log.content_hash:
        return {"valid": False, "reason": "no_hash_stored"}

    created_at_iso = log.created_at.isoformat() if log.created_at else ""
    expected = _compute_audit_hash(
        tenant_id=log.tenant_id,
        actor_user_id=log.actor_user_id,
        action=log.action,
        resource_type=log.target_type,
        resource_id=log.target_id,
        created_at_iso=created_at_iso,
    )
    if expected == log.content_hash:
        return {"valid": True, "reason": "ok"}
    logger.warning("Audit log %s hash mismatch! stored=%s expected=%s", audit_log_id, log.content_hash, expected)
    return {"valid": False, "reason": "hash_mismatch"}


def purge_expired_audit_logs(db: Session) -> int:
    """
    刪除已超過留存期限的稽核記錄。
    DB trigger 只封鎖未到期的紀錄，到期紀錄此函數可清除。
    回傳刪除筆數。
    """
    now = datetime.now(timezone.utc)
    deleted = (
        db.query(AuditLog)
        .filter(AuditLog.expires_at < now)
        .delete(synchronize_session=False)
    )
    db.commit()
    logger.info("purge_expired_audit_logs: deleted %d records", deleted)
    return deleted



def get_audit_logs(
    db: Session,
    *,
    tenant_id: UUID,
    action: Optional[str] = None,
    actor_user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AuditLog]:
    query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if actor_user_id:
        query = query.filter(AuditLog.actor_user_id == actor_user_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


# Usage Record CRUD
def create_usage_record(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: Optional[UUID],
    action_type: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    pinecone_queries: int = 0,
    embedding_calls: int = 0,
    estimated_cost: float = 0.0,
    metadata: Optional[Dict] = None
) -> UsageRecord:
    db_obj = UsageRecord(
        tenant_id=tenant_id,
        user_id=user_id,
        action_type=action_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        pinecone_queries=pinecone_queries,
        embedding_calls=embedding_calls,
        estimated_cost_usd=estimated_cost,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_usage_summary(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    獲取租戶用量摘要（如指定 user_id 則只查該使用者個人用量）
    """
    query = db.query(UsageRecord).filter(UsageRecord.tenant_id == tenant_id)
    
    if user_id:
        query = query.filter(UsageRecord.user_id == user_id)
    if start_date:
        query = query.filter(UsageRecord.created_at >= start_date)
    if end_date:
        query = query.filter(UsageRecord.created_at <= end_date)
    
    # 聚合統計
    result = query.with_entities(
        func.sum(UsageRecord.input_tokens).label('total_input_tokens'),
        func.sum(UsageRecord.output_tokens).label('total_output_tokens'),
        func.sum(UsageRecord.pinecone_queries).label('total_pinecone_queries'),
        func.sum(UsageRecord.embedding_calls).label('total_embedding_calls'),
        func.sum(UsageRecord.estimated_cost_usd).label('total_cost'),
        func.count(UsageRecord.id).label('total_actions')
    ).first()
    
    return {
        "tenant_id": str(tenant_id),
        "total_input_tokens": result.total_input_tokens or 0,
        "total_output_tokens": result.total_output_tokens or 0,
        "total_pinecone_queries": result.total_pinecone_queries or 0,
        "total_embedding_calls": result.total_embedding_calls or 0,
        "total_cost": float(result.total_cost or 0),
        "total_actions": result.total_actions or 0
    }


def get_usage_by_action_type(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    按操作類型分組統計（如指定 user_id 則只查該使用者）
    """
    query = db.query(UsageRecord).filter(UsageRecord.tenant_id == tenant_id)
    
    if user_id:
        query = query.filter(UsageRecord.user_id == user_id)
    if start_date:
        query = query.filter(UsageRecord.created_at >= start_date)
    if end_date:
        query = query.filter(UsageRecord.created_at <= end_date)
    
    results = query.with_entities(
        UsageRecord.action_type,
        func.count(UsageRecord.id).label('count'),
        func.sum(UsageRecord.input_tokens).label('total_input_tokens'),
        func.sum(UsageRecord.output_tokens).label('total_output_tokens'),
        func.sum(UsageRecord.estimated_cost_usd).label('total_cost')
    ).group_by(UsageRecord.action_type).all()
    
    return [
        {
            "action_type": r.action_type,
            "count": r.count,
            "total_input_tokens": r.total_input_tokens or 0,
            "total_output_tokens": r.total_output_tokens or 0,
            "total_cost": float(r.total_cost or 0)
        }
        for r in results
    ]


def get_usage_records(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: Optional[UUID] = None,
    action_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[UsageRecord]:
    query = db.query(UsageRecord).filter(UsageRecord.tenant_id == tenant_id)
    
    if user_id:
        query = query.filter(UsageRecord.user_id == user_id)
    if action_type:
        query = query.filter(UsageRecord.action_type == action_type)
    if start_date:
        query = query.filter(UsageRecord.created_at >= start_date)
    if end_date:
        query = query.filter(UsageRecord.created_at <= end_date)
    
    return query.order_by(UsageRecord.created_at.desc()).offset(skip).limit(limit).all()
