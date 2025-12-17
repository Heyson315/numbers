#!/usr/bin/env python3
"""
Example: Invoice Processing Automation

This example demonstrates how to use the invoice processing module
to extract and validate invoice data.
"""

from src.invoice_processing import InvoiceProcessor
from src.expense_categorization import ExpenseCategorizer
import json


def main():
    # Initialize processors
    invoice_processor = InvoiceProcessor()
    expense_categorizer = ExpenseCategorizer()
    
    # Sample invoice text
    invoice_text = """
    ACME Office Supplies Inc.
    123 Business Street
    New York, NY 10001
    
    INVOICE
    
    Invoice Number: INV-2024-0542
    Invoice Date: 01/15/2024
    Due Date: 02/14/2024
    
    Bill To:
    Smith & Associates CPA Firm
    456 Financial Ave
    Boston, MA 02101
    
    Description                          Qty    Unit Price    Amount
    ----------------------------------------------------------------
    Premium Copy Paper (Case)             10      $35.00     $350.00
    Black Toner Cartridges                 5     $120.00     $600.00
    Blue Pens (Box of 50)                  3      $15.00      $45.00
    File Folders (Pack of 100)             2      $25.00      $50.00
    
                                          Subtotal:        $1,045.00
                                          Tax (8.5%):        $88.83
                                          Total:          $1,133.83
    
    Payment Terms: Net 30
    
    Thank you for your business!
    """
    
    print("=" * 80)
    print("INVOICE PROCESSING EXAMPLE")
    print("=" * 80)
    
    # Extract invoice data
    print("\n1. Extracting invoice data...")
    invoice = invoice_processor.extract_invoice_data(invoice_text)
    
    print(f"\n   Invoice ID: {invoice.invoice_id}")
    print(f"   Vendor: {invoice.vendor_name}")
    print(f"   Date: {invoice.invoice_date}")
    print(f"   Total: ${invoice.total_amount:,.2f}")
    print(f"   Tax: ${invoice.tax_amount:,.2f}")
    print(f"   Payment Terms: {invoice.payment_terms}")
    print(f"   Confidence Score: {invoice.confidence_score:.2%}")
    
    # Validate invoice
    print("\n2. Validating invoice...")
    is_valid, errors = invoice_processor.validate_invoice(invoice)
    
    if is_valid:
        print("   ✓ Invoice is valid")
    else:
        print("   ✗ Invoice validation failed:")
        for error in errors:
            print(f"     - {error}")
    
    # Categorize expense
    print("\n3. Categorizing expense...")
    category = invoice_processor.categorize_expense(invoice)
    gl_account = expense_categorizer.suggest_gl_account(category)
    
    print(f"   Category: {category}")
    print(f"   Suggested GL Account: {gl_account}")
    
    # Display line items
    print("\n4. Line items:")
    for i, item in enumerate(invoice.line_items, 1):
        print(f"   {i}. {item.get('description', 'N/A')}: ${item.get('amount', 0):,.2f}")
    
    # Generate summary
    print("\n5. Summary Report:")
    print("-" * 80)
    print(json.dumps(invoice.to_dict(), indent=2, default=str))
    
    print("\n" + "=" * 80)
    print("Processing complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
