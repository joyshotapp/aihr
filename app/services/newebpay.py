"""
NewebPay (藍新金流) Payment Provider

Integration docs: https://www.newebpay.com/website/Page/content/download_api
API Version: 2.3 (MPG multi-payment gateway)

Flow:
  1. Backend creates encrypted TradeInfo → generates checkout form data
  2. Frontend auto-submits form to NewebPay MPG URL
  3. User completes payment on NewebPay hosted page
  4. NewebPay POSTs encrypted result to NotifyURL (backend webhook)
  5. NewebPay redirects user to ReturnURL (frontend confirmation)

Encryption: AES-256-CBC + SHA256 hash
"""
import hashlib
import json
import logging
import time
import urllib.parse
import uuid
from binascii import hexlify, unhexlify
from datetime import datetime, timezone
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from app.config import settings
from app.services.payment_provider import (
    CheckoutRequest,
    CheckoutResult,
    PaymentProvider,
    WebhookEvent,
)

logger = logging.getLogger("unihr.newebpay")

# ── NewebPay Endpoints ──
NEWEBPAY_MPG_URL = "https://core.newebpay.com/MPG/mpg_gateway"
NEWEBPAY_MPG_URL_TEST = "https://ccore.newebpay.com/MPG/mpg_gateway"


def _get_mpg_url() -> str:
    if settings.NEWEBPAY_TEST_MODE:
        return NEWEBPAY_MPG_URL_TEST
    return NEWEBPAY_MPG_URL


# ── AES-256-CBC Encryption (NewebPay TradeInfo) ──

def _aes_encrypt(data: str, key: str, iv: str) -> str:
    """AES-256-CBC encrypt and return hex string."""
    cipher = AES.new(
        key.encode("utf-8"),
        AES.MODE_CBC,
        iv.encode("utf-8"),
    )
    padded = pad(data.encode("utf-8"), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return hexlify(encrypted).decode("utf-8")


def _aes_decrypt(hex_data: str, key: str, iv: str) -> str:
    """Decrypt AES-256-CBC hex string."""
    cipher = AES.new(
        key.encode("utf-8"),
        AES.MODE_CBC,
        iv.encode("utf-8"),
    )
    decrypted = unpad(cipher.decrypt(unhexlify(hex_data)), AES.block_size)
    return decrypted.decode("utf-8")


def _sha256_hash(trade_info_encrypted: str, key: str, iv: str) -> str:
    """Generate SHA256 TradeSha for verification.

    Formula: SHA256("HashKey={key}&{trade_info_encrypted}&HashIV={iv}")
    """
    raw = f"HashKey={key}&{trade_info_encrypted}&HashIV={iv}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()


def _parse_trade_info(decrypted_str: str) -> dict:
    """Parse decrypted NewebPay TradeInfo.

    NewebPay notify payloads are typically URL-encoded key/value pairs where
    ``Result`` itself is a JSON string. Support both that format and direct JSON.
    """
    stripped = decrypted_str.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)

    parsed = urllib.parse.parse_qs(stripped, keep_blank_values=True)
    trade_info = {
        key: values[0] if len(values) == 1 else values
        for key, values in parsed.items()
    }
    result_payload = trade_info.get("Result")
    if isinstance(result_payload, str) and result_payload:
        try:
            trade_info["Result"] = json.loads(result_payload)
        except json.JSONDecodeError:
            pass
    return trade_info


# ── NewebPay Provider ──

class NewebPayProvider(PaymentProvider):
    """藍新金流 MPG (Multi-Payment Gateway) integration."""

    def __init__(self):
        self.merchant_id = settings.NEWEBPAY_MERCHANT_ID
        self.hash_key = settings.NEWEBPAY_HASH_KEY
        self.hash_iv = settings.NEWEBPAY_HASH_IV

    def create_checkout(self, req: CheckoutRequest) -> CheckoutResult:
        """Build encrypted form data for NewebPay MPG.

        Returns CheckoutResult with the MPG URL and form fields
        that the frontend should auto-submit.
        """
        trade_no = f"UHR{int(time.time() * 1000)}{uuid.uuid4().hex[:8].upper()}"

        # TradeInfo parameters per NewebPay MPG spec
        trade_info = {
            "MerchantID": self.merchant_id,
            "RespondType": "JSON",
            "TimeStamp": str(int(time.time())),
            "Version": "2.0",
            "MerchantOrderNo": trade_no,
            "Amt": req.amount,
            "ItemDesc": req.description or f"UniHR {req.plan} 方案",
            "Email": req.email,
            "NotifyURL": f"{settings.BACKEND_BASE_URL}/api/v1/payment/notify",
            "ReturnURL": f"{settings.FRONTEND_BASE_URL}/subscription?payment=complete",
            "ClientBackURL": f"{settings.FRONTEND_BASE_URL}/subscription",
            # Credit card only for SaaS subscription
            "CREDIT": 1,
            "VACC": 0,  # disable ATM transfer
            "CVS": 0,  # disable convenience store
            # Custom fields — used in webhook to identify tenant
            "OrderComment": json.dumps({
                "tenant_id": req.tenant_id,
                "plan": req.plan,
            }),
        }

        # URL-encode the trade info
        trade_info_str = urllib.parse.urlencode(trade_info)

        # Encrypt
        trade_info_encrypted = _aes_encrypt(
            trade_info_str, self.hash_key, self.hash_iv
        )
        trade_sha = _sha256_hash(
            trade_info_encrypted, self.hash_key, self.hash_iv
        )

        # The checkout_url is the MPG endpoint; frontend needs to POST form data
        # We return formatted JSON that the frontend can use
        return CheckoutResult(
            checkout_url=_get_mpg_url(),
            trade_no=trade_no,
            form_fields={
                "MerchantID": self.merchant_id,
                "TradeInfo": trade_info_encrypted,
                "TradeSha": trade_sha,
                "Version": "2.0",
            },
        )

    def verify_webhook(self, form_data: dict) -> WebhookEvent:
        """Verify and decrypt NewebPay notify callback.

        NewebPay POSTs:
            Status, MerchantID, TradeInfo (encrypted), TradeSha
        """
        status_code = form_data.get("Status")
        trade_info_encrypted = form_data.get("TradeInfo", "")
        trade_sha = form_data.get("TradeSha", "")

        if not trade_info_encrypted or not trade_sha:
            raise ValueError("Missing TradeInfo or TradeSha")

        # 1. Verify SHA256 hash
        expected_sha = _sha256_hash(
            trade_info_encrypted, self.hash_key, self.hash_iv
        )
        if trade_sha.upper() != expected_sha:
            raise ValueError("TradeSha verification failed")

        # 2. Decrypt TradeInfo
        decrypted_str = _aes_decrypt(
            trade_info_encrypted, self.hash_key, self.hash_iv
        )
        trade_info = _parse_trade_info(decrypted_str)

        logger.info(
            "NewebPay notify: Status=%s TradeNo=%s",
            trade_info.get("Status"),
            (trade_info.get("Result") or {}).get("MerchantOrderNo", ""),
        )

        # 3. Extract result
        result = trade_info.get("Result", trade_info)
        merchant_order_no = result.get("MerchantOrderNo", "")
        gateway_trade_no = result.get("TradeNo", "")
        amount = int(result.get("Amt", 0))
        payment_type = result.get("PaymentType", "")

        # Parse tenant_id and plan from OrderComment
        order_comment = result.get("OrderComment", "{}")
        try:
            comment_data = json.loads(order_comment)
        except (json.JSONDecodeError, TypeError):
            comment_data = {}

        tenant_id = comment_data.get("tenant_id", "")
        plan = comment_data.get("plan", "")

        # Determine event type from Status
        trade_status = trade_info.get("Status") or status_code
        if trade_status == "SUCCESS":
            event_type = "payment.success"
        else:
            event_type = "payment.failed"

        return WebhookEvent(
            event_type=event_type,
            trade_no=merchant_order_no,
            gateway_trade_no=gateway_trade_no,
            amount=amount,
            currency="TWD",
            tenant_id=tenant_id,
            plan=plan,
            raw=trade_info,
        )


def get_payment_provider() -> NewebPayProvider:
    """Factory function — returns the configured payment provider."""
    return NewebPayProvider()
