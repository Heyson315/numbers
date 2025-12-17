"""Tests for HIPAA compliance."""

import pytest
from src.compliance import HIPAACompliance


class TestHIPAACompliance:
    """Test HIPAA compliance controls."""
    
    @pytest.fixture
    def hipaa(self):
        """Create HIPAA compliance instance."""
        return HIPAACompliance()
    
    def test_is_phi(self, hipaa):
        """Test PHI identification."""
        phi_data = {
            "patient_id": "P12345",
            "ssn": "123-45-6789",
            "diagnosis": "Type 2 Diabetes"
        }
        
        assert hipaa.is_phi(phi_data)
    
    def test_encrypt_decrypt_phi(self, hipaa):
        """Test PHI encryption and decryption."""
        phi_data = {
            "patient_id": "P12345",
            "medical_record": "MR-2024-001"
        }
        
        encrypted = hipaa.encrypt_phi(phi_data, user_id="doctor@hospital.com")
        assert encrypted != str(phi_data)
        
        decrypted = hipaa.decrypt_phi(
            encrypted,
            user_id="nurse@hospital.com",
            purpose="Patient care"
        )
        assert decrypted == phi_data
    
    def test_generate_hipaa_report(self, hipaa):
        """Test HIPAA compliance report generation."""
        report = hipaa.generate_hipaa_report()
        
        assert report["encryption_enabled"]
        assert report["access_logging_enabled"]
        assert report["breach_detection_enabled"]
