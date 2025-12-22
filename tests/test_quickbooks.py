"""
QuickBooks Integration Tests

Tests for QuickBooks OAuth 2.0 authentication and API client.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx


class TestQuickBooksAuth:
    """Test QuickBooks OAuth 2.0 authentication."""

    @patch.dict('os.environ', {
        'QB_CLIENT_ID': 'test_client_id',
        'QB_CLIENT_SECRET': 'test_client_secret',
        'QB_REDIRECT_URI': 'http://localhost:8000/quickbooks/callback'
    })
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        from src.integrations.quickbooks import QuickBooksAuth
        auth = QuickBooksAuth()
        assert auth.client_id == 'test_client_id'
        assert auth.client_secret == 'test_client_secret'
        assert auth.redirect_uri == 'http://localhost:8000/quickbooks/callback'

    @patch.dict('os.environ', {'QB_CLIENT_ID': '', 'QB_CLIENT_SECRET': ''}, clear=True)
    def test_init_missing_credentials_raises_error(self):
        """Test that missing credentials raises ValueError."""
        from src.integrations.quickbooks import QuickBooksAuth
        with pytest.raises(ValueError, match="Set QB_CLIENT_ID"):
            QuickBooksAuth()

    @patch.dict('os.environ', {
        'QB_CLIENT_ID': 'test_client_id',
        'QB_CLIENT_SECRET': 'test_client_secret'
    })
    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        from src.integrations.quickbooks import QuickBooksAuth
        auth = QuickBooksAuth()
        url, state = auth.get_authorization_url()
        
        assert "appcenter.intuit.com/connect/oauth2" in url
        assert "client_id=test_client_id" in url
        assert "response_type=code" in url
        assert "scope=com.intuit.quickbooks.accounting" in url
        assert f"state={state}" in url
        assert len(state) > 20  # State should be a secure random token

    @patch.dict('os.environ', {
        'QB_CLIENT_ID': 'test_client_id',
        'QB_CLIENT_SECRET': 'test_client_secret'
    })
    def test_get_authorization_url_with_custom_state(self):
        """Test authorization URL with custom state parameter."""
        from src.integrations.quickbooks import QuickBooksAuth
        auth = QuickBooksAuth()
        custom_state = "my_custom_state_123"
        url, state = auth.get_authorization_url(state=custom_state)
        
        assert state == custom_state
        assert f"state={custom_state}" in url

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'QB_CLIENT_ID': 'test_client_id',
        'QB_CLIENT_SECRET': 'test_client_secret'
    })
    async def test_exchange_code_success(self):
        """Test successful code exchange for tokens."""
        from src.integrations.quickbooks import QuickBooksAuth
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            auth = QuickBooksAuth()
            tokens = await auth.exchange_code("test_code", "test_realm_id")
            
            assert tokens["access_token"] == "test_access_token"
            assert tokens["refresh_token"] == "test_refresh_token"
            assert tokens["realm_id"] == "test_realm_id"

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'QB_CLIENT_ID': 'test_client_id',
        'QB_CLIENT_SECRET': 'test_client_secret'
    })
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        from src.integrations.quickbooks import QuickBooksAuth
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            auth = QuickBooksAuth()
            tokens = await auth.refresh_token("old_refresh_token")
            
            assert tokens["access_token"] == "new_access_token"


class TestQuickBooksClient:
    """Test QuickBooks API client."""

    def test_init_sandbox_mode(self):
        """Test client initialization in sandbox mode."""
        from src.integrations.quickbooks import QuickBooksClient
        client = QuickBooksClient("test_token", "test_realm", sandbox=True)
        
        assert client.access_token == "test_token"
        assert client.realm_id == "test_realm"
        assert "sandbox-quickbooks" in client.base_url

    def test_init_production_mode(self):
        """Test client initialization in production mode."""
        from src.integrations.quickbooks import QuickBooksClient
        client = QuickBooksClient("test_token", "test_realm", sandbox=False)
        
        assert "sandbox" not in client.base_url
        assert "quickbooks.api.intuit.com" in client.base_url

    def test_headers_include_bearer_token(self):
        """Test that headers include Bearer token."""
        from src.integrations.quickbooks import QuickBooksClient
        client = QuickBooksClient("my_access_token", "my_realm")
        
        assert client.headers["Authorization"] == "Bearer my_access_token"
        assert client.headers["Accept"] == "application/json"
        assert client.headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_customers(self):
        """Test getting customers from QuickBooks."""
        from src.integrations.quickbooks import QuickBooksClient
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "QueryResponse": {
                "Customer": [
                    {"Id": "1", "DisplayName": "Test Customer 1"},
                    {"Id": "2", "DisplayName": "Test Customer 2"}
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            client = QuickBooksClient("test_token", "test_realm")
            customers = await client.get_customers()
            
            assert len(customers) == 2
            assert customers[0]["DisplayName"] == "Test Customer 1"

    @pytest.mark.asyncio
    async def test_get_invoices(self):
        """Test getting invoices from QuickBooks."""
        from src.integrations.quickbooks import QuickBooksClient
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "QueryResponse": {
                "Invoice": [
                    {"Id": "101", "TotalAmt": 500.00},
                    {"Id": "102", "TotalAmt": 750.00}
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            client = QuickBooksClient("test_token", "test_realm")
            invoices = await client.get_invoices()
            
            assert len(invoices) == 2
            assert invoices[0]["TotalAmt"] == 500.00

    @pytest.mark.asyncio
    async def test_get_invoices_with_date_filter(self):
        """Test getting invoices with date filter."""
        from src.integrations.quickbooks import QuickBooksClient
        
        mock_response = Mock()
        mock_response.json.return_value = {"QueryResponse": {"Invoice": []}}
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            client = QuickBooksClient("test_token", "test_realm")
            await client.get_invoices(start_date="2024-01-01")
            
            # Verify the query included date filter
            call_args = mock_client.request.call_args
            assert "2024-01-01" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_create_customer(self):
        """Test creating a customer in QuickBooks."""
        from src.integrations.quickbooks import QuickBooksClient
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "Customer": {"Id": "123", "DisplayName": "New Customer"}
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            client = QuickBooksClient("test_token", "test_realm")
            result = await client.create_customer("New Customer", "test@example.com")
            
            assert result["Customer"]["DisplayName"] == "New Customer"

    @pytest.mark.asyncio
    async def test_get_accounts(self):
        """Test getting chart of accounts."""
        from src.integrations.quickbooks import QuickBooksClient
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "QueryResponse": {
                "Account": [
                    {"Id": "1", "Name": "Checking", "AccountType": "Bank"},
                    {"Id": "2", "Name": "Revenue", "AccountType": "Income"}
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            client = QuickBooksClient("test_token", "test_realm")
            accounts = await client.get_accounts()
            
            assert len(accounts) == 2
            assert accounts[0]["Name"] == "Checking"

    @pytest.mark.asyncio
    async def test_get_profit_loss_report(self):
        """Test getting Profit & Loss report."""
        from src.integrations.quickbooks import QuickBooksClient
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "Header": {"ReportName": "ProfitAndLoss"},
            "Rows": {"Row": []}
        }
        mock_response.raise_for_status = Mock()
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            client = QuickBooksClient("test_token", "test_realm")
            report = await client.get_profit_loss("2024-01-01", "2024-12-31")
            
            assert report["Header"]["ReportName"] == "ProfitAndLoss"


class TestQuickBooksRoutes:
    """Test QuickBooks API routes."""

    @pytest.mark.asyncio
    async def test_status_not_connected(self):
        """Test status endpoint when not connected."""
        from src.integrations.quickbooks_routes import quickbooks_status, qb_tokens
        qb_tokens.clear()
        
        result = await quickbooks_status()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_status_connected(self):
        """Test status endpoint when connected."""
        from src.integrations.quickbooks_routes import quickbooks_status, qb_tokens
        qb_tokens["access_token"] = "test_token"
        qb_tokens["realm_id"] = "test_realm"
        
        result = await quickbooks_status()
        assert result["connected"] is True
        assert result["realm_id"] == "test_realm"
        
        qb_tokens.clear()

    @pytest.mark.asyncio
    async def test_disconnect_clears_tokens(self):
        """Test disconnect endpoint clears tokens."""
        from src.integrations.quickbooks_routes import disconnect_quickbooks, qb_tokens, qb_states
        qb_tokens["access_token"] = "test_token"
        qb_states["test_state"] = True
        
        result = await disconnect_quickbooks()
        
        assert result["message"] == "QuickBooks disconnected successfully"
        assert len(qb_tokens) == 0
        assert len(qb_states) == 0

    @pytest.mark.asyncio
    async def test_get_customers_not_connected(self):
        """Test get_customers raises error when not connected."""
        from src.integrations.quickbooks_routes import get_customers, qb_tokens
        from fastapi import HTTPException
        qb_tokens.clear()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_customers()
        
        assert exc_info.value.status_code == 401
        assert "not connected" in exc_info.value.detail.lower()
