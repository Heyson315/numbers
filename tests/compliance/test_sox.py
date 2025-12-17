"""Tests for SOX compliance."""

import pytest
from src.compliance import SOXCompliance


class TestSOXCompliance:
    """Test SOX compliance controls."""
    
    @pytest.fixture
    def sox(self):
        """Create SOX compliance instance."""
        return SOXCompliance()
    
    def test_segregation_of_duties(self, sox):
        """Test segregation of duties check."""
        result = sox.check_segregation_of_duties(
            user_id="accountant@company.com",
            action="create_transaction",
            resource="transaction/TXN-001"
        )
        
        assert "approved" in result
    
    def test_generate_sox_report(self, sox):
        """Test SOX compliance report generation."""
        report = sox.generate_sox_report()
        
        assert "sox_section_404_compliance" in report
        assert "control_tests" in report
        assert "access_reviews" in report
