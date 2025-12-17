"""
QuickBooks Integration Tests

Tests for QuickBooks OAuth, client operations, and sync functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.integrations.quickbooks import QuickBooksAuth, QuickBooksClient
from src.integrations.quickbooks import QBOAccount, QBOInvoice, GAAPValidator


class TestQuickBooksAuth:
    """Test QuickBooks OAuth 2.0 authentication."""
    
    def test_initialization(self):
        """Test QuickBooksAuth initialization."""
        with patch.dict('os.environ', {
            'QBO_CLIENT_ID': 'test_client_id',
            'QBO_CLIENT_SECRET': 'test_secret'
        }):
            qb_auth = QuickBooksAuth()
            assert qb_auth.client_id == 'test_client_id'
            assert qb_auth.client_secret == 'test_secret'
    
    def test_generate_pkce_pair(self):
        """Test PKCE code verifier and challenge generation."""
        qb_auth = QuickBooksAuth()
        verifier, challenge = qb_auth.generate_pkce_pair()
        
        assert len(verifier) >= 43
        assert len(challenge) >= 43
        assert verifier != challenge
    
    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        qb_auth = QuickBooksAuth()
        result = qb_auth.get_authorization_url()
        
        assert 'authorization_url' in result
        assert 'state' in result
        assert 'code_verifier' in result
        assert 'appcenter.intuit.com' in result['authorization_url']


class TestQuickBooksClient:
    """Test QuickBooks API client."""
    
    @pytest.fixture
    def mock_auth(self):
        """Create mock auth."""
        auth = Mock(spec=QuickBooksAuth)
        auth.get_valid_token = AsyncMock(return_value='test_token')
        return auth
    
    def test_client_initialization(self, mock_auth):
        """Test client initialization."""
        client = QuickBooksClient(mock_auth, realm_id='test_realm')
        assert client.realm_id == 'test_realm'
        assert client.environment == 'sandbox'


class TestGAAPValidator:
    """Test GAAP validation."""
    
    def test_validate_account(self):
        """Test account validation."""
        validator = GAAPValidator()
        account = QBOAccount(
            name='Cash',
            account_type='Asset',
            account_sub_type='Current Asset'
        )
        
        is_valid, errors = validator.validate_account(account)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_account_type(self):
        """Test invalid account type."""
        validator = GAAPValidator()
        account = QBOAccount(
            name='Test',
            account_type='InvalidType',
            account_sub_type='Current Asset'
        )
        
        is_valid, errors = validator.validate_account(account)
        assert not is_valid
        assert len(errors) > 0


@pytest.mark.skipif(
    not pytest.config.getoption("--integration"),
    reason="Requires QuickBooks credentials"
)
class TestQuickBooksIntegration:
    """Integration tests requiring live QuickBooks connection."""
    
    @pytest.mark.asyncio
    async def test_live_get_accounts(self):
        """Test getting accounts from live QuickBooks."""
        # This requires valid credentials
        pass
