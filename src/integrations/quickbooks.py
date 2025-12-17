"""QuickBooks Online Integration"""
import os
import httpx
from urllib.parse import urlencode
from typing import Optional
import secrets
import base64


class QuickBooksAuth:
    """Handle QuickBooks OAuth2 authentication."""
    
    AUTHORIZATION_URL = "https://appcenter.intuit.com/connect/oauth2"
    TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    def __init__(self):
        self.client_id = os.getenv("QB_CLIENT_ID")
        self.client_secret = os.getenv("QB_CLIENT_SECRET")
        self.redirect_uri = os.getenv("QB_REDIRECT_URI", "http://localhost:8000/quickbooks/callback")
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Set QB_CLIENT_ID and QB_CLIENT_SECRET in .env")
    
    def get_authorization_url(self, state: Optional[str] = None) -> tuple:
        """Generate OAuth2 authorization URL."""
        state = state or secrets.token_urlsafe(32)
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        url = f"{self.AUTHORIZATION_URL}?{urlencode(params)}"
        return url, state
    
    async def exchange_code(self, code: str, realm_id: str) -> dict:
        """Exchange authorization code for tokens."""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                }
            )
            response.raise_for_status()
            tokens = response.json()
            tokens["realm_id"] = realm_id
            return tokens
    
    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token."""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }
            )
            response.raise_for_status()
            return response.json()


class QuickBooksClient:
    """QuickBooks Online API Client."""
    
    SANDBOX_URL = "https://sandbox-quickbooks.api.intuit.com/v3"
    PRODUCTION_URL = "https://quickbooks.api.intuit.com/v3"
    
    def __init__(self, access_token: str, realm_id: str, sandbox: bool = True):
        self.access_token = access_token
        self.realm_id = realm_id
        self.base_url = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make API request."""
        url = f"{self.base_url}/company/{self.realm_id}/{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
    
    # ========== Customers ==========
    async def get_customers(self, max_results: int = 100) -> list:
        """Get all customers."""
        query = f"SELECT * FROM Customer MAXRESULTS {max_results}"
        result = await self._request("GET", f"query?query={query}")
        return result.get("QueryResponse", {}).get("Customer", [])
    
    async def create_customer(self, display_name: str, email: Optional[str] = None) -> dict:
        """Create a new customer."""
        data = {"DisplayName": display_name}
        if email:
            data["PrimaryEmailAddr"] = {"Address": email}
        return await self._request("POST", "customer", json=data)
    
    # ========== Invoices ==========
    async def get_invoices(self, start_date: Optional[str] = None) -> list:
        """Get invoices, optionally filtered by date."""
        query = "SELECT * FROM Invoice"
        if start_date:
            query += f" WHERE TxnDate >= '{start_date}'"
        result = await self._request("GET", f"query?query={query}")
        return result.get("QueryResponse", {}).get("Invoice", [])
    
    async def create_invoice(
        self,
        customer_id: str,
        line_items: list,
        due_date: Optional[str] = None
    ) -> dict:
        """Create an invoice."""
        lines = []
        for idx, item in enumerate(line_items, 1):
            lines.append({
                "LineNum": idx,
                "Amount": item["amount"],
                "DetailType": "SalesItemLineDetail",
                "Description": item.get("description", ""),
                "SalesItemLineDetail": {
                    "ItemRef": {"value": item.get("item_id", "1")},
                    "Qty": item.get("quantity", 1),
                    "UnitPrice": item["amount"]
                }
            })
        
        invoice_data = {
            "CustomerRef": {"value": customer_id},
            "Line": lines
        }
        if due_date:
            invoice_data["DueDate"] = due_date
        
        return await self._request("POST", "invoice", json=invoice_data)
    
    # ========== Expenses/Purchases ==========
    async def get_expenses(self, start_date: Optional[str] = None) -> list:
        """Get purchases/expenses."""
        query = "SELECT * FROM Purchase"
        if start_date:
            query += f" WHERE TxnDate >= '{start_date}'"
        result = await self._request("GET", f"query?query={query}")
        return result.get("QueryResponse", {}).get("Purchase", [])
    
    # ========== Accounts ==========
    async def get_accounts(self) -> list:
        """Get chart of accounts."""
        result = await self._request("GET", "query?query=SELECT * FROM Account")
        return result.get("QueryResponse", {}).get("Account", [])
    
    # ========== Reports ==========
    async def get_profit_loss(self, start_date: str, end_date: str) -> dict:
        """Get Profit & Loss report."""
        return await self._request(
            "GET",
            f"reports/ProfitAndLoss?start_date={start_date}&end_date={end_date}"
        )
    
    async def get_balance_sheet(self, as_of_date: str) -> dict:
        """Get Balance Sheet report."""
        return await self._request(
            "GET",
            f"reports/BalanceSheet?date_macro=Custom&end_date={as_of_date}"
        )
