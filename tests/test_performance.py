"""
Performance tests for optimized code.

Tests to ensure performance improvements are maintained and regression is avoided.
"""

import pytest
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.expense_categorization import SmartReconciliation
from src.anomaly_detection import AnomalyDetector
from src.invoice_processing import InvoiceProcessor


# Helper functions for test data generation (moves logic out of tests)
def generate_transaction_pairs(count: int) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Generate matching pairs of bank and book transactions for testing."""
    bank_txs = []
    book_txs = []
    base_date = datetime.now()
    
    for i in range(count):
        amount = 100.0 + (i % 100) * 10
        date = base_date + timedelta(days=i % 30)
        
        bank_txs.append({
            'amount': amount,
            'date': date.isoformat(),
            'description': f'Transaction {i}'
        })
        
        # Create corresponding book transaction with slight offset
        book_txs.append({
            'amount': amount + (0.01 if i % 10 == 0 else 0),
            'date': (date + timedelta(hours=i % 24)).isoformat(),
            'description': f'Book Entry {i}'
        })
    
    return bank_txs, book_txs


def generate_duplicate_test_data(n_transactions: int) -> pd.DataFrame:
    """Generate test data for duplicate detection testing."""
    dates = pd.date_range(start='2024-01-01', periods=n_transactions, freq='h')
    
    data = {
        'date': dates,
        'amount': [100.0 + (i % 50) * 10 for i in range(n_transactions)],
        'description': [f'Transaction {i}' for i in range(n_transactions)],
        'vendor': [f'Vendor {i % 20}' for i in range(n_transactions)]
    }
    
    return pd.DataFrame(data)


def measure_execution_time(func, *args, **kwargs) -> tuple[Any, float]:
    """Measure execution time of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed_time = time.time() - start_time
    return result, elapsed_time


# Pytest fixtures for common test data
@pytest.fixture
def large_transaction_pairs():
    """Fixture providing 500 transaction pairs."""
    return generate_transaction_pairs(500)


@pytest.fixture
def duplicate_test_dataframe():
    """Fixture providing DataFrame with 1000 transactions."""
    return generate_duplicate_test_data(1000)


@pytest.fixture
def sample_invoice_text():
    """Fixture providing sample invoice text."""
    return """
    ABC Consulting Services
    123 Business Ave
    Invoice #12345
    Date: 01/15/2024
    
    Description                  Amount
    Consulting Services         $5,000.00
    Travel Expenses             $1,200.50
    Materials                   $  350.00
    
    Subtotal                    $6,550.50
    Tax (8%)                    $  524.04
    Total                       $7,074.54
    
    Payment Terms: Net 30
    """


class TestPerformanceRegression:
    """Performance regression tests for critical paths."""

    def test_transaction_matching_performance(self):
        """Test that transaction matching scales well with large datasets."""
        reconciliation = SmartReconciliation()

        # Generate test data - 500 transactions each
        bank_txs = []
        book_txs = []

        base_date = datetime.now()
        for i in range(500):
            amount = 100.0 + (i % 100) * 10
            date = base_date + timedelta(days=i % 30)

            bank_txs.append({
                'amount': amount,
                'date': date.isoformat(),
                'description': f'Transaction {i}'
            })

            # Create corresponding book transaction with slight offset
            book_txs.append({
                'amount': amount + (0.01 if i % 10 == 0 else 0),
                'date': (date + timedelta(hours=i % 24)).isoformat(),
                'description': f'Book Entry {i}'
            })

        # Time the matching operation
        start_time = time.time()
        matches = reconciliation.fuzzy_match_transactions(bank_txs, book_txs)
        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds for 500x500)
        # With optimization, this should be much faster (< 1 second)
        assert elapsed_time < 5.0, f"Transaction matching too slow: {elapsed_time:.2f}s"

        # Verify results are correct
        assert len(matches) > 0
        matched = [m for m in matches if m['status'] == 'matched']
        assert len(matched) > 400, "Should match most transactions"

    def test_duplicate_detection_performance(self):
        """Test that duplicate detection scales well with large datasets."""
        detector = AnomalyDetector()

        # Create DataFrame with 1000 transactions
        n_transactions = 1000
        dates = pd.date_range(start='2024-01-01', periods=n_transactions, freq='h')

        data = {
            'date': dates,
            'amount': [100.0 + (i % 50) * 10 for i in range(n_transactions)],
            'description': [f'Transaction {i}' for i in range(n_transactions)],
            'vendor': [f'Vendor {i % 20}' for i in range(n_transactions)]
        }

        df = pd.DataFrame(data)

        # Time the duplicate detection
        start_time = time.time()
        duplicates = detector.detect_duplicate_transactions(df)
        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 3 seconds for 1000 transactions)
        # With optimization, this should be much faster (< 0.5 seconds)
        assert elapsed_time < 3.0, f"Duplicate detection too slow: {elapsed_time:.2f}s"

        # Verify results are sensible
        assert isinstance(duplicates, list)

    def test_invoice_processing_performance(self):
        """Test that invoice processing with vendor extraction is efficient."""
        processor = InvoiceProcessor()

        # Create sample invoice text
        invoice_text = """
        ABC Consulting Services
        123 Business Ave
        Invoice #12345
        Date: 01/15/2024

        Description                  Amount
        Consulting Services         $5,000.00
        Travel Expenses             $1,200.50
        Materials                   $  350.00

        Subtotal                    $6,550.50
        Tax (8%)                    $  524.04
        Total                       $7,074.54

        Payment Terms: Net 30
        """

        # Process multiple times to test repeated operations
        start_time = time.time()
        for _ in range(100):
            invoice = processor.extract_invoice_data(invoice_text)
            processor.validate_invoice(invoice)
            processor.categorize_expense(invoice)
        elapsed_time = time.time() - start_time

        # Should process 100 invoices quickly (< 2 seconds)
        assert elapsed_time < 2.0, f"Invoice processing too slow: {elapsed_time:.2f}s"

    def test_pattern_compilation_performance(self):
        """Test that pre-compiled patterns improve performance."""
        processor1 = InvoiceProcessor()

        # Verify patterns are compiled and reused
        assert hasattr(processor1, 'compiled_amount_pattern')
        assert hasattr(processor1, 'compiled_date_patterns')
        assert hasattr(processor1, '_flat_vendor_patterns')

        # Test that the same instance reuses compiled patterns
        text = "Total: $1,234.56 Date: 01/15/2024"

        start_time = time.time()
        for _ in range(1000):
            processor1._extract_amounts(text)
        elapsed_time = time.time() - start_time

        # Should be very fast with pre-compiled patterns (< 0.5 seconds for 1000 calls)
        assert elapsed_time < 0.5, f"Pattern matching too slow: {elapsed_time:.2f}s"


def build_transactions_for_size(size: int) -> tuple[List[Dict], List[Dict]]:
    """Helper to build transaction lists of specific size."""
    now_iso = datetime.now().isoformat()
    bank_txs = [
        {
            'amount': 100.0 + i,
            'date': now_iso,
            'description': f'Tx {i}'
        }
        for i in range(size)
    ]
    book_txs = [
        {
            'amount': 100.0 + i,
            'date': now_iso,
            'description': f'Bk {i}'
        }
        for i in range(size)
    ]
    return bank_txs, book_txs


class TestScalability:
    """Tests to ensure code scales well with data size."""

    def test_transaction_matching_scales_linearly(self):
        """Test that transaction matching scales roughly O(n+m) not O(n*m)."""
        reconciliation = SmartReconciliation()

        times = []
        sizes = [50, 100, 200]

        for size in sizes:
            bank_txs = [
                {
                    'amount': 100.0 + i,
                    'date': datetime.now().isoformat(),
                    'description': f'Tx {i}'
                }
                for i in range(size)
            ]
            book_txs = [
                {
                    'amount': 100.0 + i,
                    'date': datetime.now().isoformat(),
                    'description': f'Bk {i}'
                }
                for i in range(size)
            ]

            start_time = time.time()
            reconciliation.fuzzy_match_transactions(bank_txs, book_txs)
            elapsed = time.time() - start_time
            times.append(elapsed)

        # With O(n²), doubling size should quadruple time
        # With O(n), doubling size should roughly double time
        # Check that 4x size increase is less than 10x time increase (should be ~4x for linear)
        if times[0] > 0:
            ratio = times[2] / times[0]  # 4x data size
            assert ratio < 10, f"Scaling worse than expected: {ratio:.2f}x time for 4x data"

    def test_duplicate_detection_with_many_amounts(self):
        """Test duplicate detection handles many unique amounts efficiently."""
        detector = AnomalyDetector()

        # Create data with 500 unique amounts
        n = 500
        dates = pd.date_range(start='2024-01-01', periods=n, freq='h')

        df = pd.DataFrame({
            'date': dates,
            'amount': [100.0 + i * 0.5 for i in range(n)],  # All unique amounts
            'description': [f'Tx {i}' for i in range(n)]
        })

        start_time = time.time()
        duplicates = detector.detect_duplicate_transactions(df)
        elapsed_time = time.time() - start_time

        # Should handle all unique amounts quickly (< 1 second)
        assert elapsed_time < 1.0, f"Too slow with many unique amounts: {elapsed_time:.2f}s"

        # Should find no duplicates (all amounts are unique)
        assert len(duplicates) == 0


# Edge case tests to address Sourcery feedback
class TestEdgeCases:
    """Edge case tests for various scenarios."""
    
    def test_transaction_matching_empty_lists(self):
        """Test transaction matching with empty input lists."""
        reconciliation = SmartReconciliation()
        
        # Empty bank transactions - book transactions become unmatched
        matches = reconciliation.fuzzy_match_transactions([], [{'amount': 100}])
        assert len(matches) == 1
        assert matches[0]['status'] == 'unmatched_book'
        
        # Empty book transactions
        matches = reconciliation.fuzzy_match_transactions([{'amount': 100}], [])
        assert len(matches) == 1
        assert matches[0]['status'] == 'unmatched_bank'
        
        # Both empty
        matches = reconciliation.fuzzy_match_transactions([], [])
        assert matches == []
    
    def test_transaction_matching_highly_imbalanced(self):
        """Test transaction matching with highly imbalanced list sizes."""
        reconciliation = SmartReconciliation()
        
        # 1 bank transaction vs 100 book transactions
        bank_txs = [{'amount': 100.0, 'date': '2024-01-01', 'description': 'Test'}]
        book_txs, _ = generate_transaction_pairs(100)
        
        matches = reconciliation.fuzzy_match_transactions(bank_txs, book_txs)
        assert len(matches) >= 1
    
    def test_duplicate_detection_missing_columns(self):
        """Test duplicate detection with missing required columns."""
        detector = AnomalyDetector()
        
        # DataFrame without 'amount' column
        df = pd.DataFrame({'date': ['2024-01-01'], 'description': ['Test']})
        duplicates = detector.detect_duplicate_transactions(df)
        assert duplicates == []
        
        # DataFrame without 'date' column
        df = pd.DataFrame({'amount': [100.0], 'description': ['Test']})
        duplicates = detector.detect_duplicate_transactions(df)
        assert duplicates == []
    
    def test_duplicate_detection_non_standard_dates(self):
        """Test duplicate detection with various date formats."""
        detector = AnomalyDetector()
        
        # Test with ISO format dates
        df = pd.DataFrame({
            'date': ['2024-01-01T10:00:00', '2024-01-01T11:00:00'],
            'amount': [100.0, 100.0],
            'description': ['Test1', 'Test2']
        })
        duplicates = detector.detect_duplicate_transactions(df)
        assert isinstance(duplicates, list)
        
        # Test with date-only format
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-01'],
            'amount': [100.0, 100.0],
            'description': ['Test1', 'Test2']
        })
        duplicates = detector.detect_duplicate_transactions(df)
        assert isinstance(duplicates, list)
    
    def test_duplicate_detection_empty_dataframe(self):
        """Test duplicate detection with empty DataFrame."""
        detector = AnomalyDetector()
        
        df = pd.DataFrame()
        duplicates = detector.detect_duplicate_transactions(df)
        assert duplicates == []
        
        # DataFrame with columns but no rows
        df = pd.DataFrame({'date': [], 'amount': [], 'description': []})
        duplicates = detector.detect_duplicate_transactions(df)
        assert duplicates == []
