"""
NewebPay Payment Webhook & Checkout API

Endpoints:
  - POST /payment/checkout   — Create checkout form data for NewebPay MPG
  - POST /payment/notify     — Receive NewebPay payment notification (webhook)
  - POST /payment/return     — Handle user return from NewebPay (optional)

Flow:
  1. Frontend calls POST /payment/checkout → gets form fields
  2. Frontend auto-submits form to NewebPay MPG URL
  3. NewebPay POSTs encrypted result to /payment/notify
  4. We verify, decrypt, activate plan, create BillingRecord
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.config import settings
from app.models.billing import BillingRecord
from app.models.tenant import Tenant
from app.models.user import User
from app.services.newebpay import get_payment_provider
from app.services.subscription import get_plan, PLAN_MATRIX

router = APIRouter()
logger = logging.getLogger("unihr.payment")


# ── Schemas ──

class CheckoutRequestBody(BaseModel):
    target_plan: str  # "pro" or "enterprise"


class CheckoutResponse(BaseModel):
    mpg_url: str
    form_fields: dict  # MerchantID, TradeInfo, TradeSha, Version
    trade_no: str


# ── Checkout endpoint ──

@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    body: CheckoutRequestBody,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create NewebPay MPG checkout form data.

    Frontend should auto-submit these fields to mpg_url via POST form.
    """
    if current_user.role not in ("owner",) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有 Owner 可以變更方案")

    if body.target_plan not in PLAN_MATRIX:
        raise HTTPException(status_code=400, detail="無效的方案名稱")

    if not settings.NEWEBPAY_MERCHANT_ID:
        raise HTTPException(status_code=503, detail="金流尚未設定")

    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Validate upgrade path
    plan_order = {"free": 0, "pro": 1, "enterprise": 2}
    current_level = plan_order.get(tenant.plan or "free", 0)
    target_level = plan_order.get(body.target_plan, 0)
    if target_level <= current_level:
        raise HTTPException(status_code=400, detail="無法降級，請聯繫客服")

    plan_config = get_plan(body.target_plan)
    amount = plan_config["price_monthly_twd"]  # TWD amount

    from app.services.payment_provider import CheckoutRequest
    provider = get_payment_provider()
    result = provider.create_checkout(CheckoutRequest(
        tenant_id=str(tenant.id),
        plan=body.target_plan,
        amount=amount,
        currency="TWD",
        description=f"UniHR {plan_config['display_name']} 方案月費",
        email=current_user.email or "",
    ))

    logger.info(
        "Checkout created: tenant=%s plan=%s amount=%d trade_no=%s",
        tenant.id, body.target_plan, amount, result.trade_no,
    )

    return CheckoutResponse(
        mpg_url=result.checkout_url,
        form_fields=result.form_fields,
        trade_no=result.trade_no,
    )


# ── Webhook (NotifyURL) ──

@router.post("/notify")
async def payment_notify(request: Request, db: Session = Depends(deps.get_db)):
    """Handle NewebPay payment notification.

    NewebPay POSTs form-encoded data: Status, MerchantID, TradeInfo, TradeSha.
    """
    if not settings.NEWEBPAY_HASH_KEY:
        raise HTTPException(status_code=503, detail="Payment not configured")

    form = await request.form()
    form_data = dict(form)

    provider = get_payment_provider()
    try:
        event = provider.verify_webhook(form_data)
    except ValueError as e:
        logger.warning("Payment webhook verification failed: %s", e)
        raise HTTPException(status_code=400, detail="驗證失敗")

    logger.info(
        "Payment event: type=%s trade_no=%s amount=%d tenant=%s",
        event.event_type, event.trade_no, event.amount, event.tenant_id,
    )

    if event.event_type == "payment.success":
        _handle_payment_success(db, event)
    elif event.event_type == "payment.failed":
        _handle_payment_failed(db, event)

    # NewebPay expects HTTP 200 to confirm receipt
    return JSONResponse(content={"received": True})


# ── Return URL (user redirect after payment) ──

@router.post("/return")
async def payment_return(request: Request):
    """Handle NewebPay ReturnURL — user redirect after payment.

    This is informational only; actual processing happens in /notify.
    """
    return JSONResponse(content={"status": "ok"})


# ── Internal handlers ──

def _handle_payment_success(db: Session, event):
    """Activate plan and create billing record on successful payment."""
    from app.services.payment_provider import WebhookEvent

    if not event.tenant_id or not event.plan:
        logger.warning("payment.success: missing tenant_id or plan")
        return

    tenant = db.query(Tenant).filter(Tenant.id == event.tenant_id).first()
    if not tenant:
        logger.warning("payment.success: tenant %s not found", event.tenant_id)
        return

    if event.plan not in PLAN_MATRIX:
        logger.warning("payment.success: invalid plan %s", event.plan)
        return

    # Avoid duplicates
    existing = db.query(BillingRecord).filter(
        BillingRecord.external_id == event.gateway_trade_no
    ).first()
    if existing:
        logger.debug("Duplicate notification for %s, skipping", event.gateway_trade_no)
        return

    # Upgrade tenant
    old_plan = tenant.plan
    plan_config = get_plan(event.plan)

    tenant.plan = event.plan
    tenant.max_users = plan_config["max_users"]
    tenant.max_documents = plan_config["max_documents"]
    tenant.max_storage_mb = plan_config["max_storage_mb"]
    tenant.monthly_query_limit = plan_config["monthly_query_limit"]
    tenant.monthly_token_limit = plan_config["monthly_token_limit"]

    # Create billing record
    record = BillingRecord(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        external_id=event.gateway_trade_no,
        amount_usd=event.amount,  # Actually TWD, stored as-is
        currency=event.currency,
        status="paid",
        description=f"升級至 {plan_config['display_name']}",
        plan=event.plan,
        invoice_number=f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Payment commit failed for tenant %s: %s", tenant.id, e)
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(
        "Tenant %s upgraded via NewebPay: %s → %s (amount=%d TWD, trade=%s)",
        tenant.id, old_plan, event.plan, event.amount, event.gateway_trade_no,
    )


def _handle_payment_failed(db: Session, event):
    """Log payment failure and create failed billing record for tracking."""
    logger.warning(
        "Payment failed: tenant=%s plan=%s trade=%s",
        event.tenant_id, event.plan, event.trade_no,
    )

    if not event.tenant_id:
        return

    tenant = db.query(Tenant).filter(Tenant.id == event.tenant_id).first()
    if not tenant:
        return

    record = BillingRecord(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        external_id=event.gateway_trade_no or event.trade_no,
        amount_usd=event.amount,
        currency=event.currency,
        status="failed",
        description=f"付款失敗 — {event.plan} 方案",
        plan=event.plan,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
