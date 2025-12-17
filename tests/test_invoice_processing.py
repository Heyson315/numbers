"""
Tests for invoice processing module.
"""

import pytest
from src.invoice_processing import InvoiceProcessor, Invoice
from datetime import datetime


class TestInvoiceProcessor:
    """Test invoice processing functionality."""

    def test_extract_invoice_data(self):
        """Test invoice data extraction."""
        processor = InvoiceProcessor()

        invoice_text = """
        ACME Office Supplies
        Invoice #INV-2024-001
        Date: 01/15/2024

        Office Paper - $125.00
        Pens (Box of 50) - $35.00

        Subtotal: $160.00
        Tax: $16.00
        Total: $176.00

        Payment Terms: Net 30
        """

        invoice = processor.extract_invoice_data(invoice_text)

        assert invoice is not None
        assert invoice.total_amount > 0
        assert invoice.vendor_name is not None
        assert invoice.confidence_score > 0

    def test_validate_invoice(self):
        """Test invoice validation."""
        processor = InvoiceProcessor()

        valid_invoice = Invoice(
            invoice_id="INV-001",
            vendor_name="Test Vendor",
            invoice_date=datetime.now(),
            due_date=None,
            total_amount=100.00,
            tax_amount=10.00,
            line_items=[],
            payment_terms="Net 30"
        )

        is_valid, errors = processor.validate_invoice(valid_invoice)
        assert is_valid
        assert len(errors) == 0

    def test_categorize_expense(self):
        """Test expense categorization."""
        processor = InvoiceProcessor()

        invoice = Invoice(
            invoice_id="INV-001",
            vendor_name="Staples Office Supplies",
            invoice_date=datetime.now(),
            due_date=None,
            total_amount=100.00,
            tax_amount=10.00,
            line_items=[{"description": "paper", "amount": 100}],
            payment_terms="Net 30"
        )

        category = processor.categorize_expense(invoice)
        assert category == "office_supplies"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
