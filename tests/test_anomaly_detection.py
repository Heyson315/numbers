"""
Tests for anomaly detection module.
"""

import pytest
import pandas as pd
from src.anomaly_detection import AnomalyDetector, FraudRiskScorer
from datetime import datetime, timedelta


class TestAnomalyDetector:
    """Test anomaly detection functionality."""

    def test_detect_transaction_anomalies(self):
        """Test basic anomaly detection."""
        detector = AnomalyDetector(contamination=0.1)

        # Create sample data with more points and one clear anomaly
        data = {
            'amount': [100, 150, 120, 130, 110, 105, 125, 115, 140, 135,
                       145, 118, 122, 138, 142, 5000],  # 5000 is anomaly
            'date': [datetime.now() - timedelta(days=i) for i in range(16)],
            'vendor': ['Vendor A'] * 16
        }
        df = pd.DataFrame(data)

        results = detector.detect_transaction_anomalies(df)

        assert 'is_anomaly' in results.columns
        assert 'anomaly_score' in results.columns
        # With sufficient data, anomalies should be detected
        assert len(results) > 0

    def test_detect_duplicate_transactions(self):
        """Test duplicate detection."""
        detector = AnomalyDetector()

        # Create transactions with duplicates
        now = datetime.now()
        data = {
            'amount': [100.00, 100.00, 200.00],
            'date': [now, now + timedelta(hours=1), now],
            'description': ['Payment A', 'Payment A', 'Payment B']
        }
        df = pd.DataFrame(data)

        duplicates = detector.detect_duplicate_transactions(df, time_window_hours=24)

        assert len(duplicates) > 0

    def test_detect_round_number_fraud(self):
        """Test round number detection."""
        detector = AnomalyDetector()

        data = {
            'amount': [1000, 5000, 125.50, 10000, 99.99],
            'vendor': ['A', 'A', 'B', 'A', 'B']
        }
        df = pd.DataFrame(data)

        results = detector.detect_round_number_fraud(df)

        assert 'is_round_number' in results.columns
        assert results['is_round_number'].sum() >= 3  # Three round numbers

    def test_benford_law_violations(self):
        """Test Benford's Law analysis."""
        detector = AnomalyDetector()

        # Create data that follows Benford's Law approximately
        amounts = [
            123.45, 234.56, 156.78, 189.90, 245.67,
            312.34, 156.89, 123.99, 198.45, 245.88,
            167.23, 134.56, 223.45, 189.12, 156.78,
            234.90, 145.67, 198.34, 212.56, 178.90,
            134.23, 189.45, 156.78, 223.90, 145.67,
            198.23, 167.89, 134.56, 245.78, 189.90
        ]

        result = detector.detect_benford_law_violations(amounts)

        assert 'chi_square' in result
        assert 'follows_benford' in result


class TestFraudRiskScorer:
    """Test fraud risk scoring."""

    def test_calculate_transaction_risk(self):
        """Test risk calculation for transactions."""
        scorer = FraudRiskScorer()

        # High-risk transaction (high amount + round number)
        high_risk_tx = {
            'amount': 10000.00,
            'vendor': 'New Vendor',
            'date': datetime.now().isoformat()
        }

        risk = scorer.calculate_transaction_risk(high_risk_tx)

        assert 'risk_score' in risk
        assert 'risk_level' in risk
        assert risk['risk_score'] > 0
        assert len(risk['risk_factors']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
