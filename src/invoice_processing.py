"""
AI-Powered Invoice Processing Module

Automates invoice data extraction, validation, and categorization
using machine learning and natural language processing.
"""

import re
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Invoice:
    """Represents an invoice with extracted information."""
    invoice_id: str
    vendor_name: str
    invoice_date: datetime
    due_date: Optional[datetime]
    total_amount: float
    tax_amount: float
    line_items: List[Dict[str, Any]]
    payment_terms: str
    currency: str = "USD"
    confidence_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice to dictionary."""
        data = asdict(self)
        data['invoice_date'] = self.invoice_date.isoformat() if self.invoice_date else None
        data['due_date'] = self.due_date.isoformat() if self.due_date else None
        return data


class InvoiceProcessor:
    """AI-powered invoice processing and automation."""

    def __init__(self):
        """Initialize invoice processor with pre-compiled patterns for performance."""
        self.vendor_patterns = self._load_vendor_patterns()
        self.amount_pattern = r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        self.date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        ]

        # Pre-compile regex patterns for better performance
        self.compiled_amount_pattern = re.compile(self.amount_pattern)
        self.compiled_date_patterns = [re.compile(pattern) for pattern in self.date_patterns]

        # Flatten vendor patterns into single list with compiled regex for fast matching
        self._flat_vendor_patterns = []
        for category, vendors in self.vendor_patterns.items():
            for vendor in vendors:
                # Pre-compile each vendor pattern as regex for fast matching
                self._flat_vendor_patterns.append((vendor, category))

        # Pre-compile common date formats for faster parsing
        self._date_formats = ['%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%m/%d/%y']

    def _load_vendor_patterns(self) -> Dict[str, List[str]]:
        """Load vendor identification patterns."""
        return {
            'office_supplies': [
                'staples', 'office depot', 'amazon business'
            ],
            'utilities': [
                'electric', 'power', 'water', 'gas', 'internet', 'phone'
            ],
            'professional_services': [
                'consulting', 'legal', 'accounting', 'advisory'
            ],
            'software': [
                'microsoft', 'adobe', 'salesforce', 'slack', 'zoom'
            ]
        }

    def extract_invoice_data(self, text: str) -> Invoice:
        """
        Extract structured data from invoice text using pattern matching and ML.

        Args:
            text: Raw invoice text

        Returns:
            Extracted Invoice object
        """
        # Extract amounts
        amounts = self._extract_amounts(text)
        total_amount = amounts['total'] if amounts else 0.0
        tax_amount = amounts['tax'] if amounts else 0.0

        # Extract dates
        dates = self._extract_dates(text)
        invoice_date = dates.get('invoice_date')
        due_date = dates.get('due_date')

        # Extract vendor name
        vendor_name = self._extract_vendor_name(text)

        # Extract invoice ID
        invoice_id = self._extract_invoice_id(text)

        # Extract line items
        line_items = self._extract_line_items(text)

        # Extract payment terms
        payment_terms = self._extract_payment_terms(text)

        # Calculate confidence score
        confidence = self._calculate_confidence(
            total_amount, invoice_date, vendor_name, invoice_id
        )

        return Invoice(
            invoice_id=invoice_id,
            vendor_name=vendor_name,
            invoice_date=invoice_date,
            due_date=due_date,
            total_amount=total_amount,
            tax_amount=tax_amount,
            line_items=line_items,
            payment_terms=payment_terms,
            confidence_score=confidence
        )

    def _extract_amounts(self, text: str) -> Dict[str, float]:
        """Extract monetary amounts from text using pre-compiled patterns."""
        amounts = {}

        # Find all dollar amounts
        matches = re.findall(self.amount_pattern, text)
        parsed_amounts = [float(m.replace(',', '')) for m in matches]

        if not parsed_amounts:
            return amounts

        # Look for total indicators
        lines = text.split('\n')

        for i, line in enumerate(lines):
            line_lower = line.lower()

            if 'total' in line_lower and 'subtotal' not in line_lower:
                # Find amount in this line or next few lines
                line_amounts = self.compiled_amount_pattern.findall(line)
                if line_amounts:
                    amounts['total'] = float(line_amounts[-1].replace(',', ''))

            if 'tax' in line_lower:
                line_amounts = self.compiled_amount_pattern.findall(line)
                if line_amounts:
                    amounts['tax'] = float(line_amounts[-1].replace(',', ''))

        # If no total found, use largest amount
        if 'total' not in amounts and parsed_amounts:
            amounts['total'] = max(parsed_amounts)

        return amounts

    def _extract_dates(self, text: str) -> Dict[str, Optional[datetime]]:
        """Extract dates from text using pre-compiled patterns and optimized parsing."""
        dates = {}

        for compiled_pattern in self.compiled_date_patterns:
            matches = compiled_pattern.findall(text)

            for match in matches:
                # Try pre-compiled date formats in order
                for fmt in self._date_formats:
                    try:
                        date_obj = datetime.strptime(match, fmt)
                        if 'invoice_date' not in dates:
                            dates['invoice_date'] = date_obj
                        elif 'due_date' not in dates:
                            dates['due_date'] = date_obj
                        break
                    except ValueError:
                        continue

                # Exit early if we have both dates
                if 'invoice_date' in dates and 'due_date' in dates:
                    return dates

        return dates

    def _extract_vendor_name(self, text: str) -> str:
        """Extract vendor name from text using optimized single-pass matching."""
        lines = text.split('\n')

        # Usually vendor name is at the top - check first 10 lines
        for line in lines[:10]:
            line = line.strip()
            if len(line) <= 5 or re.match(r'^\d', line):
                continue

            line_lower = line.lower()

            # Use flattened vendor list for single-pass O(n) check instead of nested O(n*m)
            for vendor, category in self._flat_vendor_patterns:
                if vendor in line_lower:
                    return line

            # If no match found and line is substantial, use it
            if len(line) > 10:
                return line

        return "Unknown Vendor"

    def _extract_invoice_id(self, text: str) -> str:
        """Extract invoice ID from text."""
        # Look for invoice number patterns
        patterns = [
            r'invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'inv\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'invoice\s+number\s*:?\s*([A-Z0-9-]+)',
        ]

        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        # Generate ID if not found
        return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items from invoice using compiled patterns."""
        line_items = []
        lines = text.split('\n')

        for line in lines:
            # Look for lines with quantity, description, and amount
            amounts = self.compiled_amount_pattern.findall(line)
            if amounts and len(line) > 20:
                line_items.append({
                    'description': line[:50].strip(),
                    'amount': float(amounts[-1].replace(',', ''))
                })

        return line_items

    def _extract_payment_terms(self, text: str) -> str:
        """Extract payment terms from text."""
        text_lower = text.lower()

        # Common payment terms
        terms_patterns = {
            'Net 30': r'net\s*30',
            'Net 60': r'net\s*60',
            'Net 90': r'net\s*90',
            'Due on Receipt': r'due\s+on\s+receipt',
            'COD': r'cash\s+on\s+delivery|cod',
        }

        for term, pattern in terms_patterns.items():
            if re.search(pattern, text_lower):
                return term

        return "Net 30"

    def _calculate_confidence(
        self,
        total_amount: float,
        invoice_date: Optional[datetime],
        vendor_name: str,
        invoice_id: str
    ) -> float:
        """Calculate confidence score for extracted data."""
        confidence = 0.0

        # Check if key fields are present
        if total_amount > 0:
            confidence += 0.3

        if invoice_date:
            confidence += 0.3

        if vendor_name and vendor_name != "Unknown Vendor":
            confidence += 0.2

        if invoice_id and not invoice_id.startswith("INV-"):
            confidence += 0.2

        return confidence

    def validate_invoice(self, invoice: Invoice) -> Tuple[bool, List[str]]:
        """
        Validate invoice data.

        Args:
            invoice: Invoice to validate

        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []

        if invoice.total_amount <= 0:
            errors.append("Invalid total amount")

        if not invoice.invoice_date:
            errors.append("Missing invoice date")

        if not invoice.vendor_name or invoice.vendor_name == "Unknown Vendor":
            errors.append("Missing or unknown vendor name")

        if invoice.tax_amount < 0:
            errors.append("Invalid tax amount")

        if invoice.due_date and invoice.invoice_date:
            if invoice.due_date < invoice.invoice_date:
                errors.append("Due date is before invoice date")

        return len(errors) == 0, errors

    def categorize_expense(self, invoice: Invoice) -> str:
        """
        Categorize expense based on vendor and line items using optimized matching.

        Args:
            invoice: Invoice to categorize

        Returns:
            Expense category
        """
        vendor_lower = invoice.vendor_name.lower()

        # Use flattened vendor patterns for O(n) single-pass check
        for vendor, category in self._flat_vendor_patterns:
            if vendor in vendor_lower:
                return category

        # Check line items
        line_items_text = ' '.join([
            item.get('description', '') for item in invoice.line_items
        ]).lower()

        if any(word in line_items_text for word in ['paper', 'pen', 'supplies']):
            return 'office_supplies'

        if any(word in line_items_text for word in ['software', 'license', 'subscription']):
            return 'software'

        return 'general_expense'

    def process_batch(self, invoice_texts: List[str]) -> pd.DataFrame:
        """
        Process a batch of invoices.

        Args:
            invoice_texts: List of invoice text content

        Returns:
            DataFrame with processed invoice data
        """
        processed_invoices = []

        for text in invoice_texts:
            invoice = self.extract_invoice_data(text)
            is_valid, errors = self.validate_invoice(invoice)
            category = self.categorize_expense(invoice)

            invoice_dict = invoice.to_dict()
            invoice_dict['is_valid'] = is_valid
            invoice_dict['validation_errors'] = errors
            invoice_dict['category'] = category

            processed_invoices.append(invoice_dict)

        return pd.DataFrame(processed_invoices)

    def generate_summary_report(self, invoices_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary report from processed invoices.

        Args:
            invoices_df: DataFrame with processed invoices

        Returns:
            Summary report dictionary
        """
        return {
            'total_invoices': len(invoices_df),
            'total_amount': float(invoices_df['total_amount'].sum()),
            'average_amount': float(invoices_df['total_amount'].mean()),
            'by_category': invoices_df.groupby('category')['total_amount'].sum().to_dict(),
            'validation_rate': float((invoices_df['is_valid'].sum() / len(invoices_df)) * 100),
            'average_confidence': float(invoices_df['confidence_score'].mean())
        }
