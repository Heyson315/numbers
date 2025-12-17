"""
Microsoft 365 Integration Tests

Tests for Graph API client, OneDrive, and SharePoint functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.integrations.m365 import GraphClient, OneDriveManager, SharePointManager
from src.integrations.m365 import M365DriveItem


class TestGraphClient:
    """Test Microsoft Graph API client."""
    
    def test_initialization(self):
        """Test GraphClient initialization."""
        with patch.dict('os.environ', {
            'AZURE_TENANT_ID': 'test_tenant',
            'AZURE_CLIENT_ID': 'test_client',
            'AZURE_CLIENT_SECRET': 'test_secret'
        }):
            client = GraphClient()
            assert client.tenant_id == 'test_tenant'
            assert client.client_id == 'test_client'
    
    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        client = GraphClient()
        result = client.get_authorization_url()
        
        assert 'authorization_url' in result
        assert 'login.microsoftonline.com' in result['authorization_url']


class TestOneDriveManager:
    """Test OneDrive operations."""
    
    @pytest.fixture
    def mock_graph_client(self):
        """Create mock Graph client."""
        client = Mock(spec=GraphClient)
        client.request = AsyncMock(return_value={"value": []})
        client.get_valid_token = AsyncMock(return_value='test_token')
        return client
    
    def test_validate_file_allowed_type(self, mock_graph_client):
        """Test file validation for allowed type."""
        manager = OneDriveManager(mock_graph_client)
        file_item = M365DriveItem(
            id='test_id',
            name='invoice.pdf',
            size=1024,
            created_datetime='2024-01-01T00:00:00Z',
            last_modified_datetime='2024-01-01T00:00:00Z'
        )
        
        result = manager.validate_file(file_item)
        assert result.is_valid
        assert result.file_type == 'pdf'
    
    def test_validate_file_disallowed_type(self, mock_graph_client):
        """Test file validation for disallowed type."""
        manager = OneDriveManager(mock_graph_client)
        file_item = M365DriveItem(
            id='test_id',
            name='malware.exe',
            size=1024,
            created_datetime='2024-01-01T00:00:00Z',
            last_modified_datetime='2024-01-01T00:00:00Z'
        )
        
        result = manager.validate_file(file_item)
        assert not result.is_valid
        assert len(result.validation_errors) > 0


@pytest.mark.skipif(
    not pytest.config.getoption("--integration"),
    reason="Requires Microsoft 365 credentials"
)
class TestM365Integration:
    """Integration tests requiring live M365 connection."""
    
    @pytest.mark.asyncio
    async def test_live_list_files(self):
        """Test listing files from live OneDrive."""
        # This requires valid credentials
        pass
