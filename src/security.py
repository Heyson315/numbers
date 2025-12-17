"""
Security Utilities Module

Provides encryption, access control, and secure data handling utilities
for CPA firm financial data processing.
"""

import os
import hashlib
import hmac
import secrets
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import json
import base64
from jose import jwt, JWTError
from passlib.context import CryptContext


class EncryptionManager:
    """Handles encryption and decryption of sensitive financial data."""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager.

        Args:
            encryption_key: Base encryption key (if None, reads from environment)
        """
        if encryption_key is None:
            encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())

        self.key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        self.cipher = Fernet(self._derive_key(self.key))

    def _derive_key(self, password: bytes, salt: Optional[bytes] = None) -> bytes:
        """
        Derive a proper Fernet key from the password.
        
        Note: This method is used during initialization to create a single cipher
        for the instance. The cipher is then reused for all encrypt/decrypt operations.
        If salt is not provided, a random salt is generated (non-deterministic).
        """
        if len(password) == 44:  # Already a valid Fernet key
            try:
                Fernet(password)
                return password
            except Exception:
                # Not a valid Fernet key, will derive one below
                pass

        # Generate salt if not provided
        if salt is None:
            salt = os.urandom(16)
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        derived_key = kdf.derive(password)
        return base64.urlsafe_b64encode(derived_key)

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data.

        Args:
            data: Plain text data to encrypt

        Returns:
            Encrypted data as base64 string (format: salt||ciphertext)
        """
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.

        Args:
            encrypted_data: Encrypted data as base64 string

        Returns:
            Decrypted plain text data
        """
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary of data."""
        json_data = json.dumps(data)
        return self.encrypt_data(json_data)

    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt data back to dictionary."""
        json_data = self.decrypt_data(encrypted_data)
        return json.loads(json_data)


class AccessControl:
    """Manages access control and authentication."""
    
    def __init__(self, secret_key: Optional[str] = None, algorithm: Optional[str] = None):
        """
        Initialize access control.

        Args:
            secret_key: Secret key for JWT tokens
            algorithm: JWT algorithm
        """
        self.secret_key = secret_key or os.getenv('SECRET_KEY', secrets.token_urlsafe(32))
        self.algorithm = algorithm or os.getenv('JWT_ALGORITHM', 'HS256')
        # Use a multi-scheme context with a stable default (pbkdf2_sha256) to avoid
        # bcrypt backend edge cases on newer Python versions (e.g., 3.14) where
        # long internal test vectors can trigger ValueError during backend feature
        # detection. Bcrypt is retained for compatibility with existing hashes.
        self.pwd_context = CryptContext(
            schemes=["pbkdf2_sha256", "bcrypt"],
            default="pbkdf2_sha256",
            deprecated="auto"
        )

        # Role-based permissions
        self.permissions = {
            'admin': ['read', 'write', 'delete', 'audit', 'manage_users'],
            'accountant': ['read', 'write', 'audit'],
            'auditor': ['read', 'audit'],
            'viewer': ['read']
        }

    def hash_password(self, password: str) -> str:
        """Hash a password for secure storage."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in the token
            expires_delta: Token expiration time

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=24)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def check_permission(self, role: str, required_permission: str) -> bool:
        """
        Check if a role has a specific permission.

        Args:
            role: User role
            required_permission: Permission to check

        Returns:
            True if role has permission, False otherwise
        """
        role_permissions = self.permissions.get(role.lower(), [])
        return required_permission in role_permissions

    def generate_api_key(self, user_id: str, role: str) -> str:
        """
        Generate a secure API key for a user.

        Args:
            user_id: User identifier
            role: User role

        Returns:
            API key string
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{user_id}:{role}:{timestamp}"
        # Use HMAC-SHA256 with the secret key for the API key
        return hmac.new(
            key=self.secret_key.encode() if isinstance(self.secret_key, str) else self.secret_key,
            msg=data.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()


class SecureDataHandler:
    """Handles secure storage and retrieval of sensitive financial data."""

    def __init__(self):
        """Initialize secure data handler."""
        self.encryption_manager = EncryptionManager()
        self.storage_path = os.getenv('SECURE_FILE_STORAGE_PATH', './secure_data')
        os.makedirs(self.storage_path, exist_ok=True)

    def store_secure_data(
        self,
        data: Dict[str, Any],
        identifier: str
    ) -> str:
        """
        Store data securely with encryption.

        Args:
            data: Data to store
            identifier: Unique identifier for the data

        Returns:
            Storage reference/path
        """
        encrypted_data = self.encryption_manager.encrypt_dict(data)
        file_path = os.path.join(self.storage_path, f"{identifier}.enc")

        with open(file_path, 'w') as data_file:
            data_file.write(encrypted_data)

        return file_path

    def retrieve_secure_data(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt stored data.

        Args:
            identifier: Unique identifier for the data

        Returns:
            Decrypted data or None if not found
        """
        file_path = os.path.join(self.storage_path, f"{identifier}.enc")

        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r') as data_file:
            encrypted_data = data_file.read()

        return self.encryption_manager.decrypt_dict(encrypted_data)

    def sanitize_input(self, input_data: str) -> str:
        """
        Sanitize user input to prevent injection attacks.

        Args:
            input_data: Raw input string

        Returns:
            The (unchanged) input string.
        """
        # Remove potential SQL injection characters
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        sanitized = input_data

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized.strip()


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a secure filename to prevent directory traversal.

    Args:
        original_filename: Original filename

    Returns:
        Secure filename
    """
    # Remove directory components
    filename = os.path.basename(original_filename)

    # Remove special characters
    filename = ''.join(char for char in filename if char.isalnum() or char in '._-')

    # Add timestamp to ensure uniqueness
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)

    return f"{name}_{timestamp}{ext}"
