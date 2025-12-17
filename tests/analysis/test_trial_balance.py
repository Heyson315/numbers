"""Tests for trial balance analysis."""

import pytest
from decimal import Decimal
from src.analysis import TrialBalanceAnalyzer


class TestTrialBalanceAnalyzer:
    """Test trial balance analysis functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return TrialBalanceAnalyzer(materiality_threshold=Decimal("0.05"))
    
    def test_balanced_trial_balance(self, analyzer):
        """Test analysis of balanced trial balance."""
        trial_balance = {
            "accounts": [
                {"account_name": "Cash", "debit": "1000", "credit": "0"},
                {"account_name": "Accounts Payable", "debit": "0", "credit": "1000"}
            ],
            "total_debits": "1000",
            "total_credits": "1000"
        }
        
        result = analyzer.analyze_trial_balance(trial_balance)
        
        assert result["is_balanced"]
        assert len(result["issues"]) == 0
    
    def test_out_of_balance(self, analyzer):
        """Test analysis of out-of-balance trial balance."""
        trial_balance = {
            "accounts": [
                {"account_name": "Cash", "debit": "1000", "credit": "0"},
                {"account_name": "Accounts Payable", "debit": "0", "credit": "500"}
            ],
            "total_debits": "1000",
            "total_credits": "500"
        }
        
        result = analyzer.analyze_trial_balance(trial_balance)
        
        assert not result["is_balanced"]
        assert len(result["issues"]) > 0
        assert result["issues"][0]["type"] == "out_of_balance"
