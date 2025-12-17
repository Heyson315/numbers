"""
QuickBooks Online API Client

Provides comprehensive API client for QuickBooks Online with rate limiting,
retry logic, and comprehensive audit logging.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
import asyncio
from functools import wraps

from src.audit_logging import AuditLogger, AuditEventType
from .auth import QuickBooksAuth
from .models import (
    QBOAccount,
    QBOInvoice,
    QBOJournalEntry,
    QBOVendor,
    QBOCustomer,
    QBOTrialBalance
)


def rate_limit(max_per_minute: int = 500):
    """Decorator to enforce rate limiting (Intuit limit: 500 req/min)."""
    def decorator(func):
        last_calls = []
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = datetime.utcnow()
            # Remove calls older than 1 minute
            cutoff = now.timestamp() - 60
            last_calls[:] = [t for t in last_calls if t > cutoff]
            
            # Check rate limit
            if len(last_calls) >= max_per_minute:
                sleep_time = 60 - (now.timestamp() - last_calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            last_calls.append(now.timestamp())
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator to retry API calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    last_exception = e
                    # Don't retry on 4xx client errors (except 429 rate limit)
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        raise
                    
                    # Wait with exponential backoff
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        await asyncio.sleep(wait_time)
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        await asyncio.sleep(wait_time)
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


class QuickBooksClient:
    """QuickBooks Online API Client with OAuth 2.0 and rate limiting."""
    
    SANDBOX_URL = "https://sandbox-quickbooks.api.intuit.com/v3"
    PRODUCTION_URL = "https://quickbooks.api.intuit.com/v3"
    
    def __init__(
        self,
        auth: QuickBooksAuth,
        realm_id: str,
        sandbox: bool = True,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize QuickBooks client.
        
        Args:
            auth: QuickBooksAuth instance for token management
            realm_id: QuickBooks company/realm ID
            sandbox: Whether to use sandbox environment
            audit_logger: Audit logger for API calls
        """
        self.auth = auth
        self.realm_id = realm_id
        self.base_url = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
        self.audit_logger = audit_logger or AuditLogger()
        self.environment = "sandbox" if sandbox else "production"
    
    async def _get_headers(self, user_id: str = "system") -> Dict[str, str]:
        """Get headers with valid access token."""
        access_token = await self.auth.get_valid_token(self.realm_id, user_id)
        if not access_token:
            raise ValueError("No valid access token available")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    @rate_limit(max_per_minute=500)
    @retry_with_backoff(max_retries=3)
    async def _request(
        self,
        method: str,
        endpoint: str,
        user_id: str = "system",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make API request with rate limiting and retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            user_id: User ID for audit logging
            **kwargs: Additional request parameters
        
        Returns:
            API response data
        """
        url = f"{self.base_url}/company/{self.realm_id}/{endpoint}"
        headers = await self._get_headers(user_id)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.API_CALL,
            user_id=user_id,
            action=f"qbo_{method.lower()}",
            resource=endpoint,
            status="initiated",
            details={"environment": self.environment}
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    timeout=30.0,
                    **kwargs
                )
                response.raise_for_status()
                data = response.json()
            
            self.audit_logger.log_event(
                event_type=AuditEventType.API_CALL,
                user_id=user_id,
                action=f"qbo_{method.lower()}",
                resource=endpoint,
                status="success"
            )
            
            return data
            
        except httpx.HTTPStatusError as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action=f"qbo_{method.lower()}",
                resource=endpoint,
                status="error",
                details={"error": str(e), "status_code": e.response.status_code}
            )
            raise
    
    # Account Operations
    async def get_accounts(
        self,
        user_id: str = "system",
        active_only: bool = True
    ) -> List[QBOAccount]:
        """
        Get chart of accounts.
        
        Args:
            user_id: User ID for audit logging
            active_only: Only return active accounts
        
        Returns:
            List of QBOAccount objects
        """
        query = "SELECT * FROM Account"
        if active_only:
            query += " WHERE Active = true"
        
        response = await self._request(
            "GET",
            "query",
            user_id=user_id,
            params={"query": query}
        )
        
        accounts = []
        for acc_data in response.get("QueryResponse", {}).get("Account", []):
            accounts.append(QBOAccount(**acc_data))
        
        return accounts
    
    async def create_account(
        self,
        account: QBOAccount,
        user_id: str = "system"
    ) -> QBOAccount:
        """Create new account."""
        response = await self._request(
            "POST",
            "account",
            user_id=user_id,
            json=account.dict(exclude_none=True)
        )
        return QBOAccount(**response.get("Account", {}))
    
    # Invoice Operations
    async def get_invoices(
        self,
        user_id: str = "system",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[QBOInvoice]:
        """
        Get invoices with optional date filtering.
        
        Args:
            user_id: User ID for audit logging
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
        
        Returns:
            List of QBOInvoice objects
        """
        query = "SELECT * FROM Invoice"
        conditions = []
        
        if start_date:
            conditions.append(f"TxnDate >= '{start_date}'")
        if end_date:
            conditions.append(f"TxnDate <= '{end_date}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        response = await self._request(
            "GET",
            "query",
            user_id=user_id,
            params={"query": query}
        )
        
        invoices = []
        for inv_data in response.get("QueryResponse", {}).get("Invoice", []):
            invoices.append(QBOInvoice(**inv_data))
        
        return invoices
    
    async def create_invoice(
        self,
        invoice: QBOInvoice,
        user_id: str = "system"
    ) -> QBOInvoice:
        """Create new invoice."""
        response = await self._request(
            "POST",
            "invoice",
            user_id=user_id,
            json=invoice.dict(exclude_none=True)
        )
        return QBOInvoice(**response.get("Invoice", {}))
    
    # Journal Entry Operations
    async def get_journal_entries(
        self,
        user_id: str = "system",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[QBOJournalEntry]:
        """Get journal entries with optional date filtering."""
        query = "SELECT * FROM JournalEntry"
        conditions = []
        
        if start_date:
            conditions.append(f"TxnDate >= '{start_date}'")
        if end_date:
            conditions.append(f"TxnDate <= '{end_date}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        response = await self._request(
            "GET",
            "query",
            user_id=user_id,
            params={"query": query}
        )
        
        entries = []
        for je_data in response.get("QueryResponse", {}).get("JournalEntry", []):
            entries.append(QBOJournalEntry(**je_data))
        
        return entries
    
    async def create_journal_entry(
        self,
        journal_entry: QBOJournalEntry,
        user_id: str = "system"
    ) -> QBOJournalEntry:
        """Create new journal entry."""
        response = await self._request(
            "POST",
            "journalentry",
            user_id=user_id,
            json=journal_entry.dict(exclude_none=True)
        )
        return QBOJournalEntry(**response.get("JournalEntry", {}))
    
    # Vendor Operations
    async def get_vendors(
        self,
        user_id: str = "system",
        active_only: bool = True
    ) -> List[QBOVendor]:
        """Get vendors."""
        query = "SELECT * FROM Vendor"
        if active_only:
            query += " WHERE Active = true"
        
        response = await self._request(
            "GET",
            "query",
            user_id=user_id,
            params={"query": query}
        )
        
        vendors = []
        for vendor_data in response.get("QueryResponse", {}).get("Vendor", []):
            vendors.append(QBOVendor(**vendor_data))
        
        return vendors
    
    # Customer Operations
    async def get_customers(
        self,
        user_id: str = "system",
        active_only: bool = True
    ) -> List[QBOCustomer]:
        """Get customers."""
        query = "SELECT * FROM Customer"
        if active_only:
            query += " WHERE Active = true"
        
        response = await self._request(
            "GET",
            "query",
            user_id=user_id,
            params={"query": query}
        )
        
        customers = []
        for cust_data in response.get("QueryResponse", {}).get("Customer", []):
            customers.append(QBOCustomer(**cust_data))
        
        return customers
    
    # Report Operations
    async def get_trial_balance(
        self,
        user_id: str = "system",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> QBOTrialBalance:
        """
        Get trial balance report.
        
        Args:
            user_id: User ID for audit logging
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            QBOTrialBalance object
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = await self._request(
            "GET",
            "reports/TrialBalance",
            user_id=user_id,
            params=params
        )
        
        # Parse trial balance report
        report_data = {
            "report_date": datetime.utcnow().date(),
            "start_date": start_date,
            "end_date": end_date,
            "accounts": []
        }
        
        # Extract account data from report
        rows = response.get("Rows", {}).get("Row", [])
        for row in rows:
            if row.get("type") == "Data":
                cols = row.get("ColData", [])
                if len(cols) >= 3:
                    report_data["accounts"].append({
                        "account_name": cols[0].get("value", ""),
                        "debit": cols[1].get("value", "0"),
                        "credit": cols[2].get("value", "0")
                    })
        
        return QBOTrialBalance(**report_data)
