"""
Microsoft 365 Integration Tests

Tests for SharePoint, OneDrive, Power BI, and Power Automate integration.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime


class TestGraphClient:
    """Test Microsoft Graph API client."""

    @patch.dict('os.environ', {
        'M365_TENANT_ID': 'test-tenant-id',
        'M365_CLIENT_ID': 'test-client-id',
        'M365_CLIENT_SECRET': 'test-client-secret'
    })
    def test_init_from_env(self):
        """Test client initialization from environment variables."""
        with patch('src.integrations.graph_client.ClientSecretCredential'):
            from src.integrations.graph_client import GraphClient
            client = GraphClient.from_env()
            assert client.tenant_id == 'test-tenant-id'
            assert client.client_id == 'test-client-id'

    @patch.dict('os.environ', {'M365_TENANT_ID': '', 'M365_CLIENT_ID': ''}, clear=True)
    def test_init_missing_credentials_raises_error(self):
        """Test that missing credentials raises ValueError."""
        from src.integrations.graph_client import GraphClient
        with pytest.raises(ValueError, match="Missing M365 credentials"):
            GraphClient.from_env()

    @patch.dict('os.environ', {
        'M365_TENANT_ID': 'test-tenant',
        'M365_CLIENT_ID': 'test-client',
        'M365_CLIENT_SECRET': 'test-secret'
    })
    def test_headers_include_bearer_token(self):
        """Test that headers include Bearer token."""
        with patch('src.integrations.graph_client.ClientSecretCredential') as mock_cred:
            mock_cred.return_value.get_token.return_value = Mock(
                token='test_token',
                expires_on=datetime.now().timestamp() + 3600
            )
            from src.integrations.graph_client import GraphClient
            client = GraphClient.from_env()
            headers = client._headers()
            assert headers["Authorization"] == "Bearer test_token"

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'M365_TENANT_ID': 'test-tenant',
        'M365_CLIENT_ID': 'test-client',
        'M365_CLIENT_SECRET': 'test-secret'
    })
    async def test_search_sites(self):
        """Test searching for SharePoint sites."""
        with patch('src.integrations.graph_client.ClientSecretCredential') as mock_cred:
            mock_cred.return_value.get_token.return_value = Mock(
                token='test_token',
                expires_on=datetime.now().timestamp() + 3600
            )
            
            mock_response = {
                "value": [
                    {"id": "site1", "name": "Encyclopedia", "displayName": "Encyclopedia KB", "webUrl": "https://test.sharepoint.com/sites/Encyclopedia"},
                    {"id": "site2", "name": "Projects", "displayName": "Project Management", "webUrl": "https://test.sharepoint.com/sites/Projects"}
                ]
            }
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_response_obj = Mock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = Mock()
                mock_client.request = AsyncMock(return_value=mock_response_obj)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client
                
                from src.integrations.graph_client import GraphClient
                client = GraphClient.from_env()
                sites = await client.search_sites("Encyclopedia")
                
                assert len(sites) == 2
                assert sites[0].name == "Encyclopedia"
                assert sites[1].display_name == "Project Management"

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'M365_TENANT_ID': 'test-tenant',
        'M365_CLIENT_ID': 'test-client',
        'M365_CLIENT_SECRET': 'test-secret'
    })
    async def test_get_site_lists(self):
        """Test getting lists from a SharePoint site."""
        with patch('src.integrations.graph_client.ClientSecretCredential') as mock_cred:
            mock_cred.return_value.get_token.return_value = Mock(
                token='test_token',
                expires_on=datetime.now().timestamp() + 3600
            )
            
            mock_response = {
                "value": [
                    {"id": "list1", "name": "Articles", "displayName": "KB Articles", "webUrl": "https://test.sharepoint.com/sites/Encyclopedia/Lists/Articles"},
                    {"id": "list2", "name": "Tasks", "displayName": "Project Tasks", "webUrl": "https://test.sharepoint.com/sites/Encyclopedia/Lists/Tasks"}
                ]
            }
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_response_obj = Mock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = Mock()
                mock_client.request = AsyncMock(return_value=mock_response_obj)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client
                
                from src.integrations.graph_client import GraphClient
                client = GraphClient.from_env()
                lists = await client.get_site_lists("site-id")
                
                assert len(lists) == 2
                assert lists[0].name == "Articles"

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'M365_TENANT_ID': 'test-tenant',
        'M365_CLIENT_ID': 'test-client',
        'M365_CLIENT_SECRET': 'test-secret'
    })
    async def test_list_drive_items(self):
        """Test listing files in document library."""
        with patch('src.integrations.graph_client.ClientSecretCredential') as mock_cred:
            mock_cred.return_value.get_token.return_value = Mock(
                token='test_token',
                expires_on=datetime.now().timestamp() + 3600
            )
            
            mock_response = {
                "value": [
                    {"id": "file1", "name": "Report.xlsx", "size": 1024, "parentReference": {"path": "/root"}, "lastModifiedDateTime": "2024-12-17T10:00:00Z", "webUrl": "https://test.sharepoint.com/file1"},
                    {"id": "folder1", "name": "Archives", "folder": {}, "size": 0, "parentReference": {"path": "/root"}, "webUrl": "https://test.sharepoint.com/folder1"}
                ]
            }
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_response_obj = Mock()
                mock_response_obj.json.return_value = mock_response
                mock_response_obj.raise_for_status = Mock()
                mock_client.request = AsyncMock(return_value=mock_response_obj)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client
                
                from src.integrations.graph_client import GraphClient
                client = GraphClient.from_env()
                items = await client.list_drive_items("site-id")
                
                assert len(items) == 2
                assert items[0].name == "Report.xlsx"
                assert items[0].is_folder is False
                assert items[1].name == "Archives"
                assert items[1].is_folder is True


class TestEncyclopediaClient:
    """Test Encyclopedia knowledge base client."""

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'M365_TENANT_ID': 'test-tenant',
        'M365_CLIENT_ID': 'test-client',
        'M365_CLIENT_SECRET': 'test-secret'
    })
    async def test_get_articles(self):
        """Test getting knowledge base articles."""
        with patch('src.integrations.graph_client.ClientSecretCredential') as mock_cred:
            mock_cred.return_value.get_token.return_value = Mock(
                token='test_token',
                expires_on=datetime.now().timestamp() + 3600
            )
            
            # Mock get_site_lists
            mock_lists = {
                "value": [{"id": "articles-list", "name": "Articles", "displayName": "Articles"}]
            }
            
            # Mock get_list_items
            mock_items = {
                "value": [
                    {"id": "1", "fields": {"Title": "QB Setup Guide", "Content": "How to set up QuickBooks", "Category": "QuickBooks", "Tags": "setup,guide"}, "lastModifiedDateTime": "2024-12-17T10:00:00Z"},
                    {"id": "2", "fields": {"Title": "Invoice Processing", "Content": "Process invoices efficiently", "Category": "Workflows", "Tags": "invoices,automation"}}
                ]
            }
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                
                # Return different responses for different calls
                def mock_request(*args, **kwargs):
                    url = args[1] if len(args) > 1 else kwargs.get('url', '')
                    mock_resp = Mock()
                    mock_resp.raise_for_status = Mock()
                    if '/lists' in url and '/items' in url:
                        mock_resp.json.return_value = mock_items
                    elif '/lists' in url:
                        mock_resp.json.return_value = mock_lists
                    return mock_resp
                
                mock_client.request = AsyncMock(side_effect=mock_request)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client
                
                from src.integrations.graph_client import GraphClient, EncyclopediaClient
                graph = GraphClient.from_env()
                enc = EncyclopediaClient(graph, "site-id")
                
                articles = await enc.get_articles()
                
                assert len(articles) == 2
                assert articles[0]["title"] == "QB Setup Guide"
                assert articles[0]["category"] == "QuickBooks"


class TestProjectManagementClient:
    """Test Project Management client."""

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'M365_TENANT_ID': 'test-tenant',
        'M365_CLIENT_ID': 'test-client',
        'M365_CLIENT_SECRET': 'test-secret'
    })
    async def test_get_tasks(self):
        """Test getting project tasks."""
        with patch('src.integrations.graph_client.ClientSecretCredential') as mock_cred:
            mock_cred.return_value.get_token.return_value = Mock(
                token='test_token',
                expires_on=datetime.now().timestamp() + 3600
            )
            
            mock_lists = {
                "value": [{"id": "tasks-list", "name": "Tasks", "displayName": "Tasks"}]
            }
            
            mock_items = {
                "value": [
                    {"id": "1", "fields": {"Title": "Review QB Integration", "Status": "In Progress", "Priority": "High", "DueDate": "2024-12-20"}},
                    {"id": "2", "fields": {"Title": "Setup Power BI", "Status": "Not Started", "Priority": "Normal"}}
                ]
            }
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                
                def mock_request(*args, **kwargs):
                    url = args[1] if len(args) > 1 else kwargs.get('url', '')
                    mock_resp = Mock()
                    mock_resp.raise_for_status = Mock()
                    if '/items' in url:
                        mock_resp.json.return_value = mock_items
                    else:
                        mock_resp.json.return_value = mock_lists
                    return mock_resp
                
                mock_client.request = AsyncMock(side_effect=mock_request)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_class.return_value = mock_client
                
                from src.integrations.graph_client import GraphClient, ProjectManagementClient
                graph = GraphClient.from_env()
                pm = ProjectManagementClient(graph, "site-id")
                
                tasks = await pm.get_tasks()
                
                assert len(tasks) == 2
                assert tasks[0]["title"] == "Review QB Integration"
                assert tasks[0]["status"] == "In Progress"


class TestPowerAutomateClient:
    """Test Power Automate webhook client."""

    def test_register_webhook(self):
        """Test registering a webhook."""
        from src.integrations.graph_client import PowerAutomateClient
        client = PowerAutomateClient()
        client.register_webhook("test_flow", "https://prod-123.westus.logic.azure.com/workflows/...")
        
        assert "test_flow" in client._webhook_urls

    @pytest.mark.asyncio
    async def test_trigger_flow_not_registered(self):
        """Test triggering unregistered flow raises error."""
        from src.integrations.graph_client import PowerAutomateClient
        client = PowerAutomateClient()
        
        with pytest.raises(ValueError, match="not registered"):
            await client.trigger_flow("unregistered", {"data": "test"})

    @pytest.mark.asyncio
    async def test_trigger_flow_success(self):
        """Test successfully triggering a flow."""
        from src.integrations.graph_client import PowerAutomateClient
        client = PowerAutomateClient()
        client.register_webhook("test_flow", "https://prod-123.westus.logic.azure.com/workflows/...")
        
        mock_response = Mock()
        mock_response.json.return_value = {"status": "accepted"}
        mock_response.raise_for_status = Mock()
        mock_response.content = b'{"status": "accepted"}'
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await client.trigger_flow("test_flow", {"invoice_id": "123"})
            
            assert result["status"] == "accepted"


class TestM365Routes:
    """Test Microsoft 365 API routes."""

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'M365_TENANT_ID': 'test-tenant',
        'M365_CLIENT_ID': 'test-client',
        'M365_CLIENT_SECRET': 'test-secret'
    })
    async def test_status_configured(self):
        """Test status endpoint when configured."""
        from src.integrations.m365_routes import m365_status
        result = await m365_status()
        
        assert result["configured"] is True
        assert result["tenant_id"].startswith("test-ten")

    @pytest.mark.asyncio
    @patch.dict('os.environ', {'M365_TENANT_ID': '', 'M365_CLIENT_ID': '', 'M365_CLIENT_SECRET': ''}, clear=True)
    async def test_status_not_configured(self):
        """Test status endpoint when not configured."""
        from src.integrations.m365_routes import m365_status
        result = await m365_status()
        
        assert result["configured"] is False

    @pytest.mark.asyncio
    async def test_register_webhook(self):
        """Test webhook registration endpoint."""
        from src.integrations.m365_routes import register_webhook, WebhookRegister
        
        webhook = WebhookRegister(
            name="qb_sync",
            url="https://prod-123.westus.logic.azure.com/workflows/..."
        )
        
        result = await register_webhook(webhook)
        
        assert result["success"] is True
        assert "qb_sync" in result["message"]

    @pytest.mark.asyncio
    async def test_list_webhooks(self):
        """Test listing registered webhooks."""
        from src.integrations.m365_routes import (
            register_webhook, list_webhooks, WebhookRegister,
            _powerautomate_client
        )
        
        # Reset client state
        from src.integrations.m365_routes import get_powerautomate_client
        client = get_powerautomate_client()
        client._webhook_urls.clear()
        
        # Register a webhook
        await register_webhook(WebhookRegister(name="test_webhook", url="https://example.com"))
        
        result = await list_webhooks()
        
        assert "test_webhook" in result["webhooks"]
