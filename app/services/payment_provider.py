"""
Payment Provider Abstraction Layer

Provides a clean interface for payment gateway operations.
Current implementation: NewebPay (藍新金流)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class CheckoutRequest:
    """Unified checkout request."""
    tenant_id: str
    plan: str
    amount: int  # in smallest currency unit (e.g., TWD dollars, not cents)
    currency: str = "TWD"
    description: str = ""
    email: str = ""


@dataclass
class CheckoutResult:
    """Unified checkout result."""
    checkout_url: str
    trade_no: str  # our order reference
    form_fields: dict  # form fields to POST to checkout_url


@dataclass
class WebhookEvent:
    """Parsed webhook event."""
    event_type: str  # "payment.success", "payment.failed", "subscription.cancelled"
    trade_no: str  # our order reference
    gateway_trade_no: str  # gateway's own trade id
    amount: int
    currency: str
    tenant_id: str
    plan: str
    raw: dict


class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    @abstractmethod
    def create_checkout(self, req: CheckoutRequest) -> CheckoutResult:
        ...

    @abstractmethod
    def verify_webhook(self, payload: dict) -> WebhookEvent:
        ...
