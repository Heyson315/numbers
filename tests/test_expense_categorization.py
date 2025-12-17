"""
Tests for expense categorization module.
"""

import pytest
from src.expense_categorization import ExpenseCategorizer, SmartReconciliation


class TestExpenseCategorizer:
    """Test expense categorization functionality."""

    def test_categorize_office_supplies(self):
        """Test categorization of office supplies."""
        categorizer = ExpenseCategorizer()

        category, confidence = categorizer.categorize(
            description="Office paper and pens",
            vendor="Staples",
            amount=50.00
        )

        assert category == "office_supplies"
        assert confidence > 0

    def test_categorize_software(self):
        """Test categorization of software expenses."""
        categorizer = ExpenseCategorizer()

        category, confidence = categorizer.categorize(
            description="Microsoft 365 subscription",
            vendor="Microsoft",
            amount=150.00
        )

        assert category == "software"
        assert confidence > 0

    def test_suggest_gl_account(self):
        """Test GL account suggestion."""
        categorizer = ExpenseCategorizer()

        gl_account = categorizer.suggest_gl_account("office_supplies")
        assert gl_account == "6100"

        gl_account = categorizer.suggest_gl_account("software")
        assert gl_account == "6800"

    def test_categorize_batch(self):
        """Test batch categorization."""
        categorizer = ExpenseCategorizer()

        expenses = [
            {"description": "Office supplies", "vendor": "Staples", "amount": 50},
            {"description": "Software license", "vendor": "Adobe", "amount": 200}
        ]

        results = categorizer.categorize_batch(expenses)

        assert len(results) == 2
        assert all('category' in r for r in results)
        assert all('confidence' in r for r in results)


class TestSmartReconciliation:
    """Test transaction reconciliation."""

    def test_fuzzy_match_transactions(self):
        """Test transaction matching."""
        reconciler = SmartReconciliation()

        bank_txs = [
            {"date": "2024-01-15", "amount": 100.00, "description": "ACME Corp"},
        ]

        book_txs = [
            {"date": "2024-01-15", "amount": 100.00, "description": "ACME Corporation"},
        ]

        matches = reconciler.fuzzy_match_transactions(bank_txs, book_txs)

        assert len(matches) > 0
        matched = [m for m in matches if m['status'] == 'matched']
        assert len(matched) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
