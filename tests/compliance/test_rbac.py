"""Tests for RBAC functionality."""

import pytest
from src.compliance import RBACManager, Permission, Role


class TestRBACManager:
    """Test role-based access control."""
    
    @pytest.fixture
    def rbac(self):
        """Create RBAC manager instance."""
        return RBACManager()
    
    def test_assign_role(self, rbac):
        """Test role assignment."""
        rbac.assign_role("user@example.com", Role.ACCOUNTANT)
        
        assert rbac.has_permission("user@example.com", Permission.READ_FINANCIALS)
        assert rbac.has_permission("user@example.com", Permission.WRITE_FINANCIALS)
    
    def test_admin_has_all_permissions(self, rbac):
        """Test admin role has all permissions."""
        rbac.assign_role("admin@example.com", Role.ADMIN)
        
        # Check a few key permissions
        assert rbac.has_permission("admin@example.com", Permission.READ_FINANCIALS)
        assert rbac.has_permission("admin@example.com", Permission.MANAGE_USERS)
        assert rbac.has_permission("admin@example.com", Permission.SYSTEM_CONFIG)
    
    def test_viewer_limited_permissions(self, rbac):
        """Test viewer role has limited permissions."""
        rbac.assign_role("viewer@example.com", Role.VIEWER)
        
        assert rbac.has_permission("viewer@example.com", Permission.READ_FINANCIALS)
        assert not rbac.has_permission("viewer@example.com", Permission.WRITE_FINANCIALS)
        assert not rbac.has_permission("viewer@example.com", Permission.MANAGE_USERS)
    
    def test_revoke_role(self, rbac):
        """Test role revocation."""
        rbac.assign_role("user@example.com", Role.ACCOUNTANT)
        assert rbac.has_permission("user@example.com", Permission.WRITE_FINANCIALS)
        
        rbac.revoke_role("user@example.com", Role.ACCOUNTANT)
        assert not rbac.has_permission("user@example.com", Permission.WRITE_FINANCIALS)
