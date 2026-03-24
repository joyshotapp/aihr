"""Unit tests for NewebPay payment provider (app/services/newebpay.py).

Covers:
  - _parse_trade_info: URL-encoded and JSON payload parsing
  - _aes_encrypt / _aes_decrypt: round-trip encryption
  - trade_no uniqueness across rapid calls
"""
import json
import urllib.parse
from unittest.mock import patch

import pytest

from app.services.newebpay import (
    NewebPayProvider,
    _aes_decrypt,
    _aes_encrypt,
    _parse_trade_info,
    _sha256_hash,
)
from app.services.payment_provider import CheckoutRequest


# ── _parse_trade_info ──────────────────────────────────────────────

class TestParseTradeInfo:
    """NewebPay TradeInfo can arrive as JSON or URL-encoded."""

    def test_json_format(self):
        """Direct JSON payload is parsed as-is."""
        payload = {
            "Status": "SUCCESS",
            "Result": {
                "MerchantOrderNo": "UHR1001",
                "Amt": 990,
                "TradeNo": "GW12345",
            },
        }
        result = _parse_trade_info(json.dumps(payload))
        assert result["Status"] == "SUCCESS"
        assert result["Result"]["MerchantOrderNo"] == "UHR1001"
        assert result["Result"]["Amt"] == 990

    def test_json_with_whitespace(self):
        """JSON with leading/trailing whitespace is handled."""
        payload = '  {"Status": "SUCCESS"}  '
        result = _parse_trade_info(payload)
        assert result["Status"] == "SUCCESS"

    def test_url_encoded_with_json_result(self):
        """URL-encoded body where Result is a nested JSON string."""
        inner_result = json.dumps({
            "MerchantOrderNo": "UHR2002",
            "Amt": 1500,
            "TradeNo": "GW67890",
            "PaymentType": "CREDIT",
        })
        body = urllib.parse.urlencode({
            "Status": "SUCCESS",
            "MerchantID": "MS1234",
            "Result": inner_result,
        })
        result = _parse_trade_info(body)
        assert result["Status"] == "SUCCESS"
        assert result["MerchantID"] == "MS1234"
        # Result should be parsed into a dict
        assert isinstance(result["Result"], dict)
        assert result["Result"]["MerchantOrderNo"] == "UHR2002"
        assert result["Result"]["Amt"] == 1500

    def test_url_encoded_without_result(self):
        """URL-encoded body with no Result key."""
        body = urllib.parse.urlencode({
            "Status": "FAILED",
            "MerchantID": "MS1234",
        })
        result = _parse_trade_info(body)
        assert result["Status"] == "FAILED"
        assert "Result" not in result

    def test_url_encoded_with_invalid_result_json(self):
        """Result that looks like a string but isn't valid JSON stays as-is."""
        body = urllib.parse.urlencode({
            "Status": "SUCCESS",
            "Result": "not-a-json{",
        })
        result = _parse_trade_info(body)
        assert result["Status"] == "SUCCESS"
        assert result["Result"] == "not-a-json{"

    def test_url_encoded_with_empty_result(self):
        """Empty Result string is not parsed."""
        body = urllib.parse.urlencode({
            "Status": "SUCCESS",
            "Result": "",
        })
        result = _parse_trade_info(body)
        assert result["Result"] == ""


# ── AES encrypt / decrypt round-trip ───────────────────────────────

class TestAESRoundTrip:
    """Verify encrypt→decrypt preserves data."""

    # 32-byte key, 16-byte IV (NewebPay spec)
    KEY = "abcdefghijklmnopqrstuvwxyz123456"
    IV = "abcdefghijklmnop"

    def test_round_trip(self):
        data = "MerchantOrderNo=UHR123&Amt=990"
        encrypted = _aes_encrypt(data, self.KEY, self.IV)
        decrypted = _aes_decrypt(encrypted, self.KEY, self.IV)
        assert decrypted == data

    def test_round_trip_unicode(self):
        data = "ItemDesc=UniHR 專業方案&Email=test@example.com"
        encrypted = _aes_encrypt(data, self.KEY, self.IV)
        decrypted = _aes_decrypt(encrypted, self.KEY, self.IV)
        assert decrypted == data

    def test_sha256_deterministic(self):
        encrypted = _aes_encrypt("test", self.KEY, self.IV)
        h1 = _sha256_hash(encrypted, self.KEY, self.IV)
        h2 = _sha256_hash(encrypted, self.KEY, self.IV)
        assert h1 == h2
        assert h1 == h1.upper()  # NewebPay expects uppercase hex


# ── trade_no uniqueness ────────────────────────────────────────────

class TestTradeNoUniqueness:
    """trade_no must be unique even on rapid consecutive calls."""

    @patch("app.services.newebpay.settings")
    def test_no_collision_on_rapid_calls(self, mock_settings):
        mock_settings.NEWEBPAY_MERCHANT_ID = "TEST_MID"
        mock_settings.NEWEBPAY_HASH_KEY = "a" * 32
        mock_settings.NEWEBPAY_HASH_IV = "b" * 16
        mock_settings.NEWEBPAY_TEST_MODE = True
        mock_settings.BACKEND_BASE_URL = "http://localhost"
        mock_settings.FRONTEND_BASE_URL = "http://localhost"

        provider = NewebPayProvider()
        req = CheckoutRequest(
            tenant_id="t-001",
            plan="pro",
            amount=990,
            email="test@test.com",
        )
        trade_nos = {provider.create_checkout(req).trade_no for _ in range(50)}
        assert len(trade_nos) == 50, "trade_no collision detected within 50 rapid calls"

    @patch("app.services.newebpay.settings")
    def test_trade_no_format(self, mock_settings):
        mock_settings.NEWEBPAY_MERCHANT_ID = "TEST_MID"
        mock_settings.NEWEBPAY_HASH_KEY = "a" * 32
        mock_settings.NEWEBPAY_HASH_IV = "b" * 16
        mock_settings.NEWEBPAY_TEST_MODE = True
        mock_settings.BACKEND_BASE_URL = "http://localhost"
        mock_settings.FRONTEND_BASE_URL = "http://localhost"

        provider = NewebPayProvider()
        req = CheckoutRequest(
            tenant_id="t-001", plan="pro", amount=990, email="t@t.com",
        )
        trade_no = provider.create_checkout(req).trade_no
        assert trade_no.startswith("UHR")
        # UHR + 13-digit ms timestamp + 8-char hex = 24 chars
        assert len(trade_no) == 24


# ── verify_webhook integration ─────────────────────────────────────

class TestVerifyWebhook:
    """Full encrypt → webhook verify round-trip."""

    KEY = "abcdefghijklmnopqrstuvwxyz123456"
    IV = "abcdefghijklmnop"

    @patch("app.services.newebpay.settings")
    def test_success_webhook(self, mock_settings):
        mock_settings.NEWEBPAY_MERCHANT_ID = "TEST_MID"
        mock_settings.NEWEBPAY_HASH_KEY = self.KEY
        mock_settings.NEWEBPAY_HASH_IV = self.IV

        provider = NewebPayProvider()

        # Simulate what NewebPay would send
        trade_info_inner = {
            "Status": "SUCCESS",
            "Result": {
                "MerchantOrderNo": "UHR1234567890",
                "TradeNo": "GW0001",
                "Amt": 990,
                "PaymentType": "CREDIT",
                "OrderComment": json.dumps({
                    "tenant_id": "t-abc",
                    "plan": "pro",
                }),
            },
        }
        plaintext = json.dumps(trade_info_inner)
        encrypted = _aes_encrypt(plaintext, self.KEY, self.IV)
        sha = _sha256_hash(encrypted, self.KEY, self.IV)

        event = provider.verify_webhook({
            "Status": "SUCCESS",
            "TradeInfo": encrypted,
            "TradeSha": sha,
        })

        assert event.event_type == "payment.success"
        assert event.trade_no == "UHR1234567890"
        assert event.gateway_trade_no == "GW0001"
        assert event.amount == 990
        assert event.tenant_id == "t-abc"
        assert event.plan == "pro"

    @patch("app.services.newebpay.settings")
    def test_failed_sha_raises(self, mock_settings):
        mock_settings.NEWEBPAY_MERCHANT_ID = "TEST_MID"
        mock_settings.NEWEBPAY_HASH_KEY = self.KEY
        mock_settings.NEWEBPAY_HASH_IV = self.IV

        provider = NewebPayProvider()
        encrypted = _aes_encrypt('{"Status":"SUCCESS"}', self.KEY, self.IV)

        with pytest.raises(ValueError, match="TradeSha verification failed"):
            provider.verify_webhook({
                "Status": "SUCCESS",
                "TradeInfo": encrypted,
                "TradeSha": "WRONG_HASH",
            })

    @patch("app.services.newebpay.settings")
    def test_url_encoded_webhook(self, mock_settings):
        """Webhook with URL-encoded TradeInfo (not JSON)."""
        mock_settings.NEWEBPAY_MERCHANT_ID = "TEST_MID"
        mock_settings.NEWEBPAY_HASH_KEY = self.KEY
        mock_settings.NEWEBPAY_HASH_IV = self.IV

        provider = NewebPayProvider()

        inner_result = json.dumps({
            "MerchantOrderNo": "UHR9999",
            "TradeNo": "GW0002",
            "Amt": 2000,
            "PaymentType": "CREDIT",
            "OrderComment": json.dumps({"tenant_id": "t-xyz", "plan": "enterprise"}),
        })
        plaintext = urllib.parse.urlencode({
            "Status": "SUCCESS",
            "Result": inner_result,
        })
        encrypted = _aes_encrypt(plaintext, self.KEY, self.IV)
        sha = _sha256_hash(encrypted, self.KEY, self.IV)

        event = provider.verify_webhook({
            "Status": "SUCCESS",
            "TradeInfo": encrypted,
            "TradeSha": sha,
        })

        assert event.event_type == "payment.success"
        assert event.trade_no == "UHR9999"
        assert event.amount == 2000
        assert event.tenant_id == "t-xyz"
        assert event.plan == "enterprise"
