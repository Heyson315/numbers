"""
Enhanced Role-Based Access Control

Granular permissions with role hierarchy and permission matrix.
"""

from typing import List, Dict, Set, Optional
from enum import Enum
from datetime import datetime

from src.audit_logging import AuditLogger, AuditEventType


class Permission(Enum):
    """Granular permissions."""
    # Read permissions
    READ_FINANCIALS = "read:financials"
    READ_AUDIT_LOGS = "read:audit_logs"
    READ_USERS = "read:users"
    
    # Write permissions
    WRITE_FINANCIALS = "write:financials"
    WRITE_JOURNAL_ENTRIES = "write:journal_entries"
    WRITE_INVOICES = "write:invoices"
    
    # Admin permissions
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    MANAGE_INTEGRATIONS = "manage:integrations"
    MANAGE_COMPLIANCE = "manage:compliance"
    
    # Audit permissions
    AUDIT_REVIEW = "audit:review"
    AUDIT_EXPORT = "audit:export"
    
    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_BACKUP = "system:backup"


class Role(Enum):
    """Role hierarchy: Admin > Auditor > Accountant > Viewer."""
    ADMIN = "admin"
    AUDITOR = "auditor"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class RBACManager:
    """Manage role-based access control with granular permissions."""
    
    # Role to permissions mapping
    ROLE_PERMISSIONS = {
        Role.ADMIN: {
            Permission.READ_FINANCIALS,
            Permission.READ_AUDIT_LOGS,
            Permission.READ_USERS,
            Permission.WRITE_FINANCIALS,
            Permission.WRITE_JOURNAL_ENTRIES,
            Permission.WRITE_INVOICES,
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            Permission.MANAGE_INTEGRATIONS,
            Permission.MANAGE_COMPLIANCE,
            Permission.AUDIT_REVIEW,
            Permission.AUDIT_EXPORT,
            Permission.SYSTEM_CONFIG,
            Permission.SYSTEM_BACKUP
        },
        Role.AUDITOR: {
            Permission.READ_FINANCIALS,
            Permission.READ_AUDIT_LOGS,
            Permission.READ_USERS,
            Permission.AUDIT_REVIEW,
            Permission.AUDIT_EXPORT
        },
        Role.ACCOUNTANT: {
            Permission.READ_FINANCIALS,
            Permission.WRITE_FINANCIALS,
            Permission.WRITE_JOURNAL_ENTRIES,
            Permission.WRITE_INVOICES,
            Permission.READ_AUDIT_LOGS
        },
        Role.VIEWER: {
            Permission.READ_FINANCIALS
        }
    }
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize RBAC manager."""
        self.audit_logger = audit_logger or AuditLogger()
        self._user_roles: Dict[str, Set[Role]] = {}
        self._custom_permissions: Dict[str, Set[Permission]] = {}
    
    def assign_role(
        self,
        user_id: str,
        role: Role,
        assigned_by: str = "system"
    ) -> None:
        """
        Assign role to user.
        
        Args:
            user_id: User ID
            role: Role to assign
            assigned_by: User performing the assignment
        """
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
        
        self._user_roles[user_id].add(role)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.PERMISSION_CHANGE,
            user_id=assigned_by,
            action="assign_role",
            resource=f"user/{user_id}",
            status="success",
            details={"role": role.value, "assigned_to": user_id}
        )
    
    def revoke_role(
        self,
        user_id: str,
        role: Role,
        revoked_by: str = "system"
    ) -> None:
        """Revoke role from user."""
        if user_id in self._user_roles and role in self._user_roles[user_id]:
            self._user_roles[user_id].remove(role)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.PERMISSION_CHANGE,
                user_id=revoked_by,
                action="revoke_role",
                resource=f"user/{user_id}",
                status="success",
                details={"role": role.value, "revoked_from": user_id}
            )
    
    def has_permission(
        self,
        user_id: str,
        permission: Permission
    ) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
        
        Returns:
            True if user has permission
        """
        # Check role-based permissions
        user_roles = self._user_roles.get(user_id, set())
        for role in user_roles:
            if permission in self.ROLE_PERMISSIONS.get(role, set()):
                return True
        
        # Check custom permissions
        custom_perms = self._custom_permissions.get(user_id, set())
        if permission in custom_perms:
            return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user."""
        permissions = set()
        
        # Add role-based permissions
        user_roles = self._user_roles.get(user_id, set())
        for role in user_roles:
            permissions.update(self.ROLE_PERMISSIONS.get(role, set()))
        
        # Add custom permissions
        permissions.update(self._custom_permissions.get(user_id, set()))
        
        return permissions
    
    def check_access(
        self,
        user_id: str,
        required_permission: Permission,
        resource: str = "unknown"
    ) -> bool:
        """
        Check access and log attempt.
        
        Args:
            user_id: User ID
            required_permission: Required permission
            resource: Resource being accessed
        
        Returns:
            True if access granted
        """
        has_access = self.has_permission(user_id, required_permission)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS if has_access else AuditEventType.SECURITY_ALERT,
            user_id=user_id,
            action="access_check",
            resource=resource,
            status="success" if has_access else "denied",
            details={"required_permission": required_permission.value}
        )
        
        return has_access
    
    def enforce_segregation_of_duties(
        self,
        user_id: str,
        action: str,
        resource: str
    ) -> bool:
        """
        Enforce segregation of duties (SOX requirement).
        
        Args:
            user_id: User ID
            action: Action being performed
            resource: Resource being accessed
        
        Returns:
            True if SOD check passes
        """
        # Example: User who creates transactions cannot approve them
        # In production, implement more sophisticated SOD rules
        
        user_roles = self._user_roles.get(user_id, set())
        
        # Admins can override SOD (with logging)
        if Role.ADMIN in user_roles:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="sod_override",
                resource=resource,
                status="warning",
                details={"action": action, "note": "Admin SOD override"}
            )
            return True
        
        # Check specific SOD rules
        # Example rule: Accountant cannot also be Auditor for same transaction
        if Role.ACCOUNTANT in user_roles and Role.AUDITOR in user_roles:
            if action == "approve_transaction":
                self.audit_logger.log_event(
                    event_type=AuditEventType.SECURITY_ALERT,
                    user_id=user_id,
                    action="sod_violation",
                    resource=resource,
                    status="denied",
                    details={"action": action, "reason": "User has conflicting roles"}
                )
                return False
        
        return True
