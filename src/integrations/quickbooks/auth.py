"""
QuickBooks OAuth 2.0 Authentication with PKCE

Secure token management with automatic refresh and encrypted storage.
"""

import os
import secrets
import base64
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode

from src.security import EncryptionManager
from src.audit_logging import AuditLogger, AuditEventType
from .models import TokenStorage


class QuickBooksAuth:
    """Handle QuickBooks OAuth 2.0 authentication with PKCE."""
    
    AUTHORIZATION_URL = "https://appcenter.intuit.com/connect/oauth2"
    TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        encryption_manager: Optional[EncryptionManager] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize QuickBooks authentication.
        
        Args:
            client_id: QuickBooks app client ID
            client_secret: QuickBooks app client secret
            redirect_uri: OAuth redirect URI
            encryption_manager: Encryption manager for token storage
            audit_logger: Audit logger for security events
        """
        self.client_id = client_id or os.getenv("QBO_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("QBO_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("QBO_REDIRECT_URI", "http://localhost:8000/api/quickbooks/auth/callback")
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("QBO_CLIENT_ID and QBO_CLIENT_SECRET must be configured")
        
        self.encryption_manager = encryption_manager or EncryptionManager()
        self.audit_logger = audit_logger or AuditLogger()
        self._token_storage: Dict[str, str] = {}  # In-memory token cache (encrypted)
    
    def generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate random code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Create SHA256 hash of verifier
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_authorization_url(
        self,
        state: Optional[str] = None,
        use_pkce: bool = True
    ) -> Dict[str, str]:
        """
        Generate OAuth 2.0 authorization URL with PKCE.
        
        Args:
            state: Optional state parameter for CSRF protection
            use_pkce: Whether to use PKCE flow (recommended)
        
        Returns:
            Dictionary with authorization_url, state, and optionally code_verifier
        """
        state = state or secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        
        result = {
            "authorization_url": f"{self.AUTHORIZATION_URL}?{urlencode(params)}",
            "state": state
        }
        
        if use_pkce:
            code_verifier, code_challenge = self.generate_pkce_pair()
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
            result["authorization_url"] = f"{self.AUTHORIZATION_URL}?{urlencode(params)}"
            result["code_verifier"] = code_verifier
        
        self.audit_logger.log_event(
            event_type=AuditEventType.API_CALL,
            user_id="system",
            action="generate_auth_url",
            resource="quickbooks_oauth",
            status="success",
            details={"use_pkce": use_pkce}
        )
        
        return result
    
    async def exchange_code(
        self,
        code: str,
        realm_id: str,
        code_verifier: Optional[str] = None,
        user_id: str = "system"
    ) -> TokenStorage:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from OAuth callback
            realm_id: QuickBooks company/realm ID
            code_verifier: PKCE code verifier (if PKCE was used)
            user_id: User ID for audit logging
        
        Returns:
            TokenStorage object with tokens
        """
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        if code_verifier:
            data["code_verifier"] = code_verifier
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json"
                    },
                    data=data,
                    timeout=30.0
                )
                response.raise_for_status()
                tokens = response.json()
            
            # Create token storage object
            token_storage = TokenStorage(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_at=datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600)),
                realm_id=realm_id,
                token_type=tokens.get("token_type", "Bearer")
            )
            
            # Store encrypted tokens
            await self.store_tokens(realm_id, token_storage, user_id)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.USER_LOGIN,
                user_id=user_id,
                action="exchange_auth_code",
                resource="quickbooks_oauth",
                status="success",
                details={"realm_id": realm_id}
            )
            
            return token_storage
            
        except httpx.HTTPStatusError as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="exchange_auth_code",
                resource="quickbooks_oauth",
                status="error",
                details={"error": str(e), "status_code": e.response.status_code}
            )
            raise
    
    async def refresh_token(
        self,
        refresh_token: str,
        realm_id: str,
        user_id: str = "system"
    ) -> TokenStorage:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Current refresh token
            realm_id: QuickBooks company/realm ID
            user_id: User ID for audit logging
        
        Returns:
            New TokenStorage object
        """
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.TOKEN_URL,
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json"
                    },
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                tokens = response.json()
            
            token_storage = TokenStorage(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_at=datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600)),
                realm_id=realm_id,
                token_type=tokens.get("token_type", "Bearer")
            )
            
            await self.store_tokens(realm_id, token_storage, user_id)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.API_CALL,
                user_id=user_id,
                action="refresh_token",
                resource="quickbooks_oauth",
                status="success",
                details={"realm_id": realm_id}
            )
            
            return token_storage
            
        except httpx.HTTPStatusError as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="refresh_token",
                resource="quickbooks_oauth",
                status="error",
                details={"error": str(e), "realm_id": realm_id}
            )
            raise
    
    async def store_tokens(
        self,
        realm_id: str,
        token_storage: TokenStorage,
        user_id: str = "system"
    ) -> None:
        """
        Store tokens encrypted in secure storage.
        
        Args:
            realm_id: QuickBooks company/realm ID
            token_storage: Token storage object
            user_id: User ID for audit logging
        """
        # Encrypt token data
        encrypted_data = self.encryption_manager.encrypt_dict(token_storage.dict())
        
        # Store in memory (in production, use secure database)
        self._token_storage[realm_id] = encrypted_data
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_MODIFY,
            user_id=user_id,
            action="store_tokens",
            resource="quickbooks_tokens",
            status="success",
            details={"realm_id": realm_id}
        )
    
    async def get_tokens(self, realm_id: str) -> Optional[TokenStorage]:
        """
        Retrieve and decrypt stored tokens.
        
        Args:
            realm_id: QuickBooks company/realm ID
        
        Returns:
            TokenStorage object or None if not found
        """
        encrypted_data = self._token_storage.get(realm_id)
        if not encrypted_data:
            return None
        
        # Decrypt token data
        token_data = self.encryption_manager.decrypt_dict(encrypted_data)
        return TokenStorage(**token_data)
    
    async def get_valid_token(
        self,
        realm_id: str,
        user_id: str = "system"
    ) -> Optional[str]:
        """
        Get valid access token, refreshing if necessary.
        
        Args:
            realm_id: QuickBooks company/realm ID
            user_id: User ID for audit logging
        
        Returns:
            Valid access token or None
        """
        token_storage = await self.get_tokens(realm_id)
        if not token_storage:
            return None
        
        # Check if token is expired or will expire in next 5 minutes
        if datetime.utcnow() + timedelta(minutes=5) >= token_storage.expires_at:
            # Refresh token
            token_storage = await self.refresh_token(
                token_storage.refresh_token,
                realm_id,
                user_id
            )
        
        return token_storage.access_token
    
    async def revoke_tokens(
        self,
        realm_id: str,
        user_id: str = "system"
    ) -> bool:
        """
        Revoke access and refresh tokens.
        
        Args:
            realm_id: QuickBooks company/realm ID
            user_id: User ID for audit logging
        
        Returns:
            True if successful
        """
        token_storage = await self.get_tokens(realm_id)
        if not token_storage:
            return False
        
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        try:
            async with httpx.AsyncClient() as client:
                # Revoke refresh token
                await client.post(
                    self.REVOKE_URL,
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={"token": token_storage.refresh_token},
                    timeout=30.0
                )
            
            # Remove from storage
            self._token_storage.pop(realm_id, None)
            
            self.audit_logger.log_event(
                event_type=AuditEventType.USER_LOGOUT,
                user_id=user_id,
                action="revoke_tokens",
                resource="quickbooks_oauth",
                status="success",
                details={"realm_id": realm_id}
            )
            
            return True
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="revoke_tokens",
                resource="quickbooks_oauth",
                status="error",
                details={"error": str(e), "realm_id": realm_id}
            )
            return False
