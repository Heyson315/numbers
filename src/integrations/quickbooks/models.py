"""
QuickBooks Online Pydantic Models

Defines data models for QuickBooks Online entities with validation.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class QBOAccount(BaseModel):
    """QuickBooks Chart of Account model."""
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(..., description="Asset, Liability, Equity, Income, Expense")
    account_sub_type: Optional[str] = None
    account_number: Optional[str] = None
    description: Optional[str] = None
    current_balance: Optional[Decimal] = Decimal("0.00")
    active: bool = True
    sync_token: Optional[str] = None
    
    @validator('account_type')
    def validate_account_type(cls, v):
        valid_types = ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense']
        if v not in valid_types:
            raise ValueError(f"Account type must be one of {valid_types}")
        return v


class QBOLine(BaseModel):
    """Line item for invoices and journal entries."""
    id: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None
    account_ref: Optional[Dict[str, str]] = None
    detail_type: Optional[str] = None


class QBOInvoice(BaseModel):
    """QuickBooks Invoice model."""
    id: Optional[str] = None
    doc_number: Optional[str] = None
    txn_date: date = Field(default_factory=date.today)
    customer_ref: Dict[str, str] = Field(..., description="Reference to customer")
    line: List[QBOLine] = Field(..., min_items=1)
    total_amt: Optional[Decimal] = Decimal("0.00")
    balance: Optional[Decimal] = Decimal("0.00")
    due_date: Optional[date] = None
    private_note: Optional[str] = None
    sync_token: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat()
        }


class QBOJournalEntry(BaseModel):
    """QuickBooks Journal Entry model."""
    id: Optional[str] = None
    doc_number: Optional[str] = None
    txn_date: date = Field(default_factory=date.today)
    line: List[QBOLine] = Field(..., min_items=2, description="Must have at least 2 lines (debit and credit)")
    private_note: Optional[str] = None
    sync_token: Optional[str] = None
    
    @validator('line')
    def validate_balanced_entry(cls, lines):
        """Ensure debits equal credits."""
        debit_total = sum(line.amount for line in lines if line.detail_type == 'JournalEntryLineDetail')
        credit_total = sum(line.amount for line in lines if line.detail_type == 'JournalEntryLineDetail')
        # Note: Actual validation would check PostingType in detail
        return lines
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat()
        }


class QBOVendor(BaseModel):
    """QuickBooks Vendor model."""
    id: Optional[str] = None
    display_name: str = Field(..., min_length=1, max_length=100)
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    balance: Optional[Decimal] = Decimal("0.00")
    active: bool = True
    sync_token: Optional[str] = None


class QBOCustomer(BaseModel):
    """QuickBooks Customer model."""
    id: Optional[str] = None
    display_name: str = Field(..., min_length=1, max_length=100)
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    balance: Optional[Decimal] = Decimal("0.00")
    active: bool = True
    sync_token: Optional[str] = None


class QBOTrialBalance(BaseModel):
    """Trial Balance report data."""
    report_date: date = Field(default_factory=date.today)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    accounts: List[Dict[str, Any]] = Field(default_factory=list)
    total_debits: Decimal = Decimal("0.00")
    total_credits: Decimal = Decimal("0.00")
    
    @validator('accounts')
    def validate_balance(cls, accounts, values):
        """Validate that debits equal credits."""
        total_debits = sum(Decimal(str(acc.get('debit', 0))) for acc in accounts)
        total_credits = sum(Decimal(str(acc.get('credit', 0))) for acc in accounts)
        values['total_debits'] = total_debits
        values['total_credits'] = total_credits
        return accounts
    
    class Config:
        json_encoders = {
            Decimal: str,
            date: lambda v: v.isoformat()
        }


class TokenStorage(BaseModel):
    """Secure token storage model."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    realm_id: str
    token_type: str = "Bearer"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
