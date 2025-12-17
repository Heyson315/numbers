"""
Microsoft Graph API Client

Azure AD OAuth 2.0 authentication and Graph API client with rate limiting.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import msal

from src.security import EncryptionManager
from src.audit_logging import AuditLogger, AuditEventType
from .models import M365TokenStorage


class GraphClient:
    """Microsoft Graph API Client with Azure AD authentication."""
    
    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
    AUTHORITY_URL = "https://login.microsoftonline.com"
    SCOPES = [
        "Files.ReadWrite.All",
        "Sites.ReadWrite.All",
        "User.Read"
    ]
    
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        encryption_manager: Optional[EncryptionManager] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize Graph client.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Azure AD application (client) ID
            client_secret: Azure AD client secret
            encryption_manager: Encryption manager for token storage
            audit_logger: Audit logger for API calls
        """
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("M365_REDIRECT_URI", "http://localhost:8000/api/m365/auth/callback")
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET must be configured")
        
        self.authority = f"{self.AUTHORITY_URL}/{self.tenant_id}"
        self.encryption_manager = encryption_manager or EncryptionManager()
        self.audit_logger = audit_logger or AuditLogger()
        self._token_storage: Dict[str, str] = {}  # Encrypted token cache
        
        # Initialize MSAL confidential client
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
    
    def get_authorization_url(self, state: Optional[str] = None) -> Dict[str, str]:
        """
        Generate Azure AD authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
        
        Returns:
            Dictionary with authorization_url and state
        """
        auth_url = self.msal_app.get_authorization_request_url(
            scopes=self.SCOPES,
            state=state,
            redirect_uri=self.redirect_uri
        )
        
        self.audit_logger.log_event(
            event_type=AuditEventType.API_CALL,
            user_id="system",
            action="generate_auth_url",
            resource="microsoft_graph",
            status="success"
        )
        
        return {"authorization_url": auth_url, "state": state}
    
    async def exchange_code(
        self,
        code: str,
        user_id: str = "system"
    ) -> M365TokenStorage:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            user_id: User ID for audit logging
        
        Returns:
            M365TokenStorage object with tokens
        """
        try:
            result = self.msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=self.SCOPES,
                redirect_uri=self.redirect_uri
            )
            
            if "error" in result:
                raise ValueError(f"Token acquisition failed: {result.get('error_description')}")
            
            token_storage = M365TokenStorage(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token"),
                expires_at=datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600)),
                scope=result.get("scope")
            )
            
            await self.store_tokens(user_id, token_storage)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.USER_LOGIN,
                user_id=user_id,
                action="exchange_auth_code",
                resource="microsoft_graph",
                status="success"
            )
            
            return token_storage
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="exchange_auth_code",
                resource="microsoft_graph",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def get_token_by_client_credentials(
        self,
        user_id: str = "system"
    ) -> M365TokenStorage:
        """
        Get token using client credentials flow (app-only auth).
        
        Args:
            user_id: User ID for audit logging
        
        Returns:
            M365TokenStorage object
        """
        try:
            result = self.msal_app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "error" in result:
                raise ValueError(f"Token acquisition failed: {result.get('error_description')}")
            
            token_storage = M365TokenStorage(
                access_token=result["access_token"],
                expires_at=datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600)),
                scope=result.get("scope")
            )
            
            await self.store_tokens(user_id, token_storage)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.API_CALL,
                user_id=user_id,
                action="acquire_client_token",
                resource="microsoft_graph",
                status="success"
            )
            
            return token_storage
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="acquire_client_token",
                resource="microsoft_graph",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def refresh_token(
        self,
        refresh_token: str,
        user_id: str = "system"
    ) -> M365TokenStorage:
        """
        Refresh access token.
        
        Args:
            refresh_token: Current refresh token
            user_id: User ID for audit logging
        
        Returns:
            New M365TokenStorage object
        """
        try:
            result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.SCOPES
            )
            
            if "error" in result:
                raise ValueError(f"Token refresh failed: {result.get('error_description')}")
            
            token_storage = M365TokenStorage(
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token", refresh_token),
                expires_at=datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600)),
                scope=result.get("scope")
            )
            
            await self.store_tokens(user_id, token_storage)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.API_CALL,
                user_id=user_id,
                action="refresh_token",
                resource="microsoft_graph",
                status="success"
            )
            
            return token_storage
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="refresh_token",
                resource="microsoft_graph",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def store_tokens(
        self,
        user_id: str,
        token_storage: M365TokenStorage
    ) -> None:
        """Store tokens encrypted."""
        encrypted_data = self.encryption_manager.encrypt_dict(token_storage.dict())
        self._token_storage[user_id] = encrypted_data
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_MODIFY,
            user_id=user_id,
            action="store_tokens",
            resource="microsoft_tokens",
            status="success"
        )
    
    async def get_tokens(self, user_id: str) -> Optional[M365TokenStorage]:
        """Retrieve and decrypt stored tokens."""
        encrypted_data = self._token_storage.get(user_id)
        if not encrypted_data:
            return None
        
        token_data = self.encryption_manager.decrypt_dict(encrypted_data)
        return M365TokenStorage(**token_data)
    
    async def get_valid_token(self, user_id: str = "system") -> Optional[str]:
        """Get valid access token, refreshing if necessary."""
        token_storage = await self.get_tokens(user_id)
        if not token_storage:
            return None
        
        # Check if token is expired or will expire in next 5 minutes
        if datetime.utcnow() + timedelta(minutes=5) >= token_storage.expires_at:
            if token_storage.refresh_token:
                token_storage = await self.refresh_token(token_storage.refresh_token, user_id)
            else:
                # Use client credentials flow for app-only access
                token_storage = await self.get_token_by_client_credentials(user_id)
        
        return token_storage.access_token
    
    async def request(
        self,
        method: str,
        endpoint: str,
        user_id: str = "system",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make Graph API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (relative to graph.microsoft.com/v1.0)
            user_id: User ID for audit logging
            **kwargs: Additional request parameters
        
        Returns:
            API response data
        """
        access_token = await self.get_valid_token(user_id)
        if not access_token:
            raise ValueError("No valid access token available")
        
        url = f"{self.GRAPH_API_ENDPOINT}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.API_CALL,
            user_id=user_id,
            action=f"graph_{method.lower()}",
            resource=endpoint,
            status="initiated"
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
                
                # Handle responses that may not have JSON body
                if response.status_code == 204:
                    return {}
                
                return response.json() if response.content else {}
            
        except httpx.HTTPStatusError as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action=f"graph_{method.lower()}",
                resource=endpoint,
                status="error",
                details={"error": str(e), "status_code": e.response.status_code}
            )
            raise
