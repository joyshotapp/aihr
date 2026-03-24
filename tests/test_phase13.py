"""Phase 13 tests — Progress, Quality Dashboard, Branding validation"""
import json
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError


# ═══════════════════════════════════════════
#  1. Progress tracking
# ═══════════════════════════════════════════

class TestProgressTracking:
    """Test Redis-based document processing progress"""

    def test_set_progress_writes_redis(self):
        from app.tasks.document_tasks import _set_progress
        mock_redis = MagicMock()
        with patch("app.core.redis_client.get_redis_client", return_value=mock_redis):
            _set_progress("doc-123", 50, "向量化中 2/4")

        mock_redis.setex.assert_called_once()
        key, ttl, val = mock_redis.setex.call_args[0]
        assert key == "doc_progress:doc-123"
        assert ttl == 3600
        data = json.loads(val)
        assert data["pct"] == 50
        assert data["detail"] == "向量化中 2/4"

    def test_set_progress_no_redis(self):
        """No exception when Redis is unavailable"""
        from app.tasks.document_tasks import _set_progress
        with patch("app.core.redis_client.get_redis_client", return_value=None):
            _set_progress("doc-123", 75, "writing")  # should not raise

    def test_set_progress_redis_error(self):
        """Gracefully handles Redis errors"""
        from app.tasks.document_tasks import _set_progress
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = ConnectionError("Redis down")
        with patch("app.core.redis_client.get_redis_client", return_value=mock_redis):
            _set_progress("doc-123", 50, "test")  # should not raise


# ═══════════════════════════════════════════
#  2. Branding Validation
# ═══════════════════════════════════════════

class TestBrandingValidation:
    """Test hex color and URL validation on BrandingSettings"""

    def _make(self, **kwargs):
        from app.api.v1.endpoints.tenant_admin import BrandingSettings
        return BrandingSettings(**kwargs)

    def test_valid_hex_colors(self):
        b = self._make(brand_primary_color="#3b82f6", brand_secondary_color="#1e40af")
        assert b.brand_primary_color == "#3b82f6"
        assert b.brand_secondary_color == "#1e40af"

    def test_none_colors_allowed(self):
        b = self._make(brand_primary_color=None, brand_secondary_color=None)
        assert b.brand_primary_color is None

    def test_empty_string_becomes_none(self):
        b = self._make(brand_primary_color="")
        assert b.brand_primary_color is None

    def test_invalid_hex_rejected(self):
        with pytest.raises(ValidationError):
            self._make(brand_primary_color="red")

    def test_short_hex_rejected(self):
        with pytest.raises(ValidationError):
            self._make(brand_primary_color="#fff")

    def test_valid_url(self):
        b = self._make(brand_logo_url="https://example.com/logo.png")
        assert b.brand_logo_url == "https://example.com/logo.png"

    def test_http_url_allowed(self):
        b = self._make(brand_favicon_url="http://cdn.example.com/fav.ico")
        assert b.brand_favicon_url == "http://cdn.example.com/fav.ico"

    def test_invalid_url_rejected(self):
        with pytest.raises(ValidationError):
            self._make(brand_logo_url="javascript:alert(1)")

    def test_empty_url_becomes_none(self):
        b = self._make(brand_logo_url="")
        assert b.brand_logo_url is None

    def test_url_too_long_rejected(self):
        with pytest.raises(ValidationError):
            self._make(brand_logo_url="https://example.com/" + "a" * 500)


# ═══════════════════════════════════════════
#  3. Quality Dashboard Schema
# ═══════════════════════════════════════════

class TestQualityDashboardSchemas:
    """Test quality dashboard response schemas"""

    def test_document_quality_summary_defaults(self):
        from app.api.v1.endpoints.tenant_admin import DocumentQualitySummary
        s = DocumentQualitySummary()
        assert s.total_documents == 0
        assert s.avg_quality_score is None

    def test_retrieval_quality_summary_defaults(self):
        from app.api.v1.endpoints.tenant_admin import RetrievalQualitySummary
        s = RetrievalQualitySummary()
        assert s.total_queries == 0
        assert s.avg_chunk_score is None

    def test_quality_dashboard_composition(self):
        from app.api.v1.endpoints.tenant_admin import (
            QualityDashboard, DocumentQualitySummary, RetrievalQualitySummary,
        )
        qd = QualityDashboard(
            document_quality=DocumentQualitySummary(
                total_documents=10, completed=8, failed=2,
                avg_quality_score=0.75,
                quality_distribution={"excellent": 3, "good": 3, "fair": 1, "poor": 1},
            ),
            retrieval_quality=RetrievalQualitySummary(
                total_queries=100,
                avg_chunk_score=0.65,
                low_score_queries=15,
                score_distribution={"0.0-0.3": 5, "0.3-0.5": 10, "0.5-0.7": 30, "0.7-0.9": 40, "0.9-1.0": 15},
            ),
        )
        assert qd.document_quality.avg_quality_score == 0.75
        assert qd.retrieval_quality.low_score_queries == 15


# ═══════════════════════════════════════════
#  4. Document Progress Endpoint Schema
# ═══════════════════════════════════════════

class TestDocumentProgressSchema:
    """Test the DocumentProgress response model"""

    def test_progress_schema(self):
        from app.api.v1.endpoints.documents import DocumentProgress
        p = DocumentProgress(document_id="abc-123", status="embedding", pct=65, detail="向量化中 3/5")
        assert p.pct == 65
        assert p.status == "embedding"

    def test_progress_defaults(self):
        from app.api.v1.endpoints.documents import DocumentProgress
        p = DocumentProgress(document_id="abc-123", status="pending")
        assert p.pct == 0
        assert p.detail == ""
