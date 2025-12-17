"""Tests for GDPR compliance."""

import pytest
from src.compliance import GDPRCompliance


class TestGDPRCompliance:
    """Test GDPR compliance controls."""
    
    @pytest.fixture
    def gdpr(self):
        """Create GDPR compliance instance."""
        return GDPRCompliance()
    
    def test_record_consent(self, gdpr):
        """Test consent recording."""
        consent = gdpr.record_consent(
            data_subject_id="user@example.com",
            purpose="marketing",
            consent_given=True,
            user_id="admin@company.com"
        )
        
        assert consent["consent_given"]
        assert consent["purpose"] == "marketing"
    
    def test_check_consent(self, gdpr):
        """Test consent checking."""
        gdpr.record_consent(
            data_subject_id="user@example.com",
            purpose="marketing",
            consent_given=True
        )
        
        has_consent = gdpr.check_consent("user@example.com", "marketing")
        assert has_consent
    
    def test_right_to_erasure(self, gdpr):
        """Test GDPR right to erasure."""
        result = gdpr.right_to_erasure(
            data_subject_id="user@example.com",
            user_id="dpo@company.com",
            reason="User requested deletion"
        )
        
        assert result["status"] in ["erased", "not_found"]
