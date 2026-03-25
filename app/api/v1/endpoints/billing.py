"""
Billing API — billing history & invoice listing.
"""
import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.responses import StreamingResponse

from app.api import deps
from app.models.user import User
from app.models.billing import BillingRecord
from app.models.tenant import Tenant

router = APIRouter()
logger = logging.getLogger("unihr.billing")


class BillingRecordOut(BaseModel):
    id: str
    external_id: Optional[str] = None
    amount_usd: float
    currency: str
    status: str
    description: Optional[str] = None
    plan: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    invoice_number: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[BillingRecordOut])
def list_billing_records(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """列出目前租戶的帳單紀錄"""
    if current_user.role not in ("owner", "admin") and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要 Owner 或 Admin 角色")

    records = (
        db.query(BillingRecord)
        .filter(BillingRecord.tenant_id == current_user.tenant_id)
        .order_by(BillingRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        BillingRecordOut(
            id=str(r.id),
            external_id=r.external_id,
            amount_usd=float(r.amount_usd),
            currency=r.currency,
            status=r.status,
            description=r.description,
            plan=r.plan,
            period_start=r.period_start,
            period_end=r.period_end,
            invoice_number=r.invoice_number,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/{record_id}", response_model=BillingRecordOut)
def get_billing_record(
    record_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """取得單筆帳單紀錄"""
    if current_user.role not in ("owner", "admin") and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要 Owner 或 Admin 角色")

    record = (
        db.query(BillingRecord)
        .filter(
            BillingRecord.id == record_id,
            BillingRecord.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="帳單紀錄不存在")

    return BillingRecordOut(
        id=str(record.id),
        external_id=record.external_id,
        amount_usd=float(record.amount_usd),
        currency=record.currency,
        status=record.status,
        description=record.description,
        plan=record.plan,
        period_start=record.period_start,
        period_end=record.period_end,
        invoice_number=record.invoice_number,
        created_at=record.created_at,
    )


@router.get("/{record_id}/pdf")
def download_invoice_pdf(
    record_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """下載帳單 PDF"""
    if current_user.role not in ("owner", "admin") and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要 Owner 或 Admin 角色")

    record = (
        db.query(BillingRecord)
        .filter(
            BillingRecord.id == record_id,
            BillingRecord.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="帳單紀錄不存在")

    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

    from app.services.invoice_pdf import generate_invoice_pdf
    pdf_buf = generate_invoice_pdf(record, tenant)

    filename = f"invoice-{record.invoice_number or record_id}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
