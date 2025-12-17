"""
QuickBooks Compliance Module

GAAP/IFRS validation hooks and chart of accounts mapping for financial compliance.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from enum import Enum

from .models import QBOAccount, QBOJournalEntry, QBOTrialBalance


class AccountingFramework(Enum):
    """Supported accounting frameworks."""
    USGAAP = "usgaap"
    IFRS = "ifrs"


class GAAPValidator:
    """US GAAP compliance validation."""
    
    # Standard US GAAP account types
    GAAP_ACCOUNT_TYPES = {
        "Asset": ["Current Asset", "Fixed Asset", "Other Asset"],
        "Liability": ["Current Liability", "Long-Term Liability", "Other Liability"],
        "Equity": ["Equity", "Retained Earnings"],
        "Revenue": ["Income", "Other Income"],
        "Expense": ["Cost of Goods Sold", "Expense", "Other Expense"]
    }
    
    def validate_account(self, account: QBOAccount) -> tuple[bool, List[str]]:
        """
        Validate account against US GAAP standards.
        
        Args:
            account: QBOAccount to validate
        
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        # Validate account type
        if account.account_type not in self.GAAP_ACCOUNT_TYPES:
            errors.append(f"Invalid account type: {account.account_type}")
        
        # Validate account sub-type if provided
        if account.account_sub_type:
            valid_subtypes = self.GAAP_ACCOUNT_TYPES.get(account.account_type, [])
            if account.account_sub_type not in valid_subtypes:
                errors.append(f"Invalid account sub-type: {account.account_sub_type} for type {account.account_type}")
        
        # Validate account name
        if not account.name or len(account.name) < 1:
            errors.append("Account name is required")
        
        # Validate account number format (if provided)
        if account.account_number:
            if not self._validate_account_number_format(account.account_number):
                errors.append(f"Invalid account number format: {account.account_number}")
        
        return len(errors) == 0, errors
    
    def _validate_account_number_format(self, account_number: str) -> bool:
        """Validate account number format (flexible for different numbering systems)."""
        # Allow alphanumeric with common separators
        return bool(account_number and len(account_number) <= 20)
    
    def validate_journal_entry(self, entry: QBOJournalEntry) -> tuple[bool, List[str]]:
        """
        Validate journal entry against US GAAP standards.
        
        Args:
            entry: QBOJournalEntry to validate
        
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        # Must have at least 2 lines (debit and credit)
        if len(entry.line) < 2:
            errors.append("Journal entry must have at least 2 lines (debit and credit)")
        
        # Validate debits equal credits
        debit_total = Decimal("0")
        credit_total = Decimal("0")
        
        for line in entry.line:
            # In QuickBooks, posting type is in the detail
            # Simplified validation here
            if line.amount > 0:
                debit_total += line.amount
            else:
                credit_total += abs(line.amount)
        
        # Allow small rounding differences
        difference = abs(debit_total - credit_total)
        if difference > Decimal("0.01"):
            errors.append(f"Debits ({debit_total}) must equal credits ({credit_total})")
        
        # Validate transaction date is present
        if not entry.txn_date:
            errors.append("Transaction date is required")
        
        return len(errors) == 0, errors
    
    def validate_trial_balance(self, trial_balance: QBOTrialBalance) -> tuple[bool, List[str]]:
        """
        Validate trial balance is in balance.
        
        Args:
            trial_balance: QBOTrialBalance to validate
        
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        # Validate debits equal credits
        difference = abs(trial_balance.total_debits - trial_balance.total_credits)
        if difference > Decimal("0.01"):
            errors.append(
                f"Trial balance is out of balance: "
                f"Debits={trial_balance.total_debits}, Credits={trial_balance.total_credits}, "
                f"Difference={difference}"
            )
        
        # Validate report has accounts
        if not trial_balance.accounts:
            errors.append("Trial balance has no accounts")
        
        # Validate date range
        if trial_balance.start_date and trial_balance.end_date:
            if trial_balance.start_date > trial_balance.end_date:
                errors.append("Start date must be before end date")
        
        return len(errors) == 0, errors
    
    def suggest_account_mapping(self, account_name: str, description: str = "") -> Dict[str, Any]:
        """
        Suggest US GAAP account mapping based on name and description.
        
        Args:
            account_name: Account name
            description: Account description
        
        Returns:
            Suggested account type and sub-type
        """
        name_lower = account_name.lower()
        desc_lower = description.lower() if description else ""
        
        # Asset accounts
        if any(keyword in name_lower for keyword in ["cash", "bank", "checking", "savings"]):
            return {"account_type": "Asset", "account_sub_type": "Current Asset"}
        elif any(keyword in name_lower for keyword in ["receivable", "ar", "accounts receivable"]):
            return {"account_type": "Asset", "account_sub_type": "Current Asset"}
        elif any(keyword in name_lower for keyword in ["inventory", "stock"]):
            return {"account_type": "Asset", "account_sub_type": "Current Asset"}
        elif any(keyword in name_lower for keyword in ["equipment", "furniture", "vehicle", "building", "land"]):
            return {"account_type": "Asset", "account_sub_type": "Fixed Asset"}
        
        # Liability accounts
        elif any(keyword in name_lower for keyword in ["payable", "ap", "accounts payable"]):
            return {"account_type": "Liability", "account_sub_type": "Current Liability"}
        elif any(keyword in name_lower for keyword in ["loan", "note payable", "mortgage"]):
            return {"account_type": "Liability", "account_sub_type": "Long-Term Liability"}
        elif any(keyword in name_lower for keyword in ["tax", "payroll", "withholding"]):
            return {"account_type": "Liability", "account_sub_type": "Current Liability"}
        
        # Equity accounts
        elif any(keyword in name_lower for keyword in ["equity", "capital", "stock", "retained earnings"]):
            return {"account_type": "Equity", "account_sub_type": "Equity"}
        
        # Revenue accounts
        elif any(keyword in name_lower for keyword in ["revenue", "sales", "income", "fees"]):
            return {"account_type": "Revenue", "account_sub_type": "Income"}
        
        # Expense accounts
        elif any(keyword in name_lower for keyword in ["expense", "cost", "salary", "rent", "utilities"]):
            return {"account_type": "Expense", "account_sub_type": "Expense"}
        
        # Default to expense if unsure
        return {"account_type": "Expense", "account_sub_type": "Expense", "confidence": "low"}


class IFRSValidator:
    """IFRS compliance validation."""
    
    # Standard IFRS account classifications
    IFRS_CLASSIFICATIONS = {
        "Asset": ["Current Asset", "Non-current Asset"],
        "Liability": ["Current Liability", "Non-current Liability"],
        "Equity": ["Equity"],
        "Income": ["Revenue", "Other Income"],
        "Expense": ["Expense", "Finance Costs"]
    }
    
    def validate_account(self, account: QBOAccount) -> tuple[bool, List[str]]:
        """
        Validate account against IFRS standards.
        
        Args:
            account: QBOAccount to validate
        
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        # Map QuickBooks types to IFRS
        qbo_to_ifrs = {
            "Asset": "Asset",
            "Liability": "Liability",
            "Equity": "Equity",
            "Revenue": "Income",
            "Expense": "Expense"
        }
        
        ifrs_type = qbo_to_ifrs.get(account.account_type)
        if not ifrs_type:
            errors.append(f"Cannot map account type {account.account_type} to IFRS")
        
        # Validate account name
        if not account.name or len(account.name) < 1:
            errors.append("Account name is required")
        
        return len(errors) == 0, errors
    
    def validate_journal_entry(self, entry: QBOJournalEntry) -> tuple[bool, List[str]]:
        """
        Validate journal entry against IFRS standards.
        
        Similar to GAAP but with IFRS-specific rules.
        """
        # IFRS validation is similar to GAAP for basic double-entry bookkeeping
        gaap_validator = GAAPValidator()
        return gaap_validator.validate_journal_entry(entry)
    
    def suggest_ifrs_classification(self, account: QBOAccount) -> Dict[str, str]:
        """
        Suggest IFRS classification for an account.
        
        Args:
            account: QBOAccount to classify
        
        Returns:
            IFRS classification
        """
        # Map QuickBooks to IFRS with focus on current vs non-current
        name_lower = account.name.lower()
        
        if account.account_type == "Asset":
            if any(keyword in name_lower for keyword in ["cash", "receivable", "inventory", "prepaid"]):
                return {"ifrs_classification": "Current Asset"}
            else:
                return {"ifrs_classification": "Non-current Asset"}
        
        elif account.account_type == "Liability":
            if any(keyword in name_lower for keyword in ["payable", "accrued", "current"]):
                return {"ifrs_classification": "Current Liability"}
            else:
                return {"ifrs_classification": "Non-current Liability"}
        
        elif account.account_type == "Equity":
            return {"ifrs_classification": "Equity"}
        
        elif account.account_type == "Revenue":
            return {"ifrs_classification": "Revenue"}
        
        elif account.account_type == "Expense":
            if any(keyword in name_lower for keyword in ["interest", "finance"]):
                return {"ifrs_classification": "Finance Costs"}
            else:
                return {"ifrs_classification": "Expense"}
        
        return {"ifrs_classification": "Unknown"}
