"""
Tests for security module.
"""

import pytest
import os
from src.security import (
    EncryptionManager,
    AccessControl,
    SecureDataHandler,
    generate_secure_filename
)


@pytest.fixture(autouse=True)
def set_encryption_key():
    """Set ENCRYPTION_KEY for all tests."""
    original_key = os.environ.get('ENCRYPTION_KEY')
    os.environ['ENCRYPTION_KEY'] = 'test_key_for_encryption_1234567890'
    yield
    if original_key is None:
        os.environ.pop('ENCRYPTION_KEY', None)
    else:
        os.environ['ENCRYPTION_KEY'] = original_key


class TestEncryptionManager:
    """Test encryption functionality."""

    def test_encrypt_decrypt_data(self):
        """Test data encryption and decryption."""
        manager = EncryptionManager()

        original_data = "Sensitive financial data: $10,000"
        encrypted = manager.encrypt_data(original_data)
        decrypted = manager.decrypt_data(encrypted)

        assert encrypted != original_data
        assert decrypted == original_data

    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        manager = EncryptionManager()

        original_dict = {
            "account_number": "123456789",
            "balance": 50000.00,
            "client": "ABC Corp"
        }

        encrypted = manager.encrypt_dict(original_dict)
        decrypted = manager.decrypt_dict(encrypted)

        assert decrypted == original_dict


class TestAccessControl:
    """Test access control and authentication."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        ac = AccessControl()

        password = "SecureP@ssw0rd123"
        hashed = ac.hash_password(password)

        assert hashed != password
        assert ac.verify_password(password, hashed)
        assert not ac.verify_password("wrong_password", hashed)

    def test_jwt_token_creation(self):
        """Test JWT token creation and verification."""
        ac = AccessControl()

        data = {"user_id": "test_user", "role": "accountant"}
        token = ac.create_access_token(data)

        assert token is not None

        payload = ac.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "test_user"

    def test_permission_checking(self):
        """Test role-based permission checking."""
        ac = AccessControl()

        assert ac.check_permission("admin", "delete")
        assert ac.check_permission("accountant", "write")
        assert not ac.check_permission("viewer", "write")
        assert ac.check_permission("auditor", "audit")

    def test_api_key_generation(self):
        """Test API key generation."""
        ac = AccessControl()

        api_key = ac.generate_api_key("user123", "accountant")

        assert api_key is not None
        assert len(api_key) == 64  # SHA256 hex digest


class TestSecureDataHandler:
    """Test secure data handling."""

    def test_store_retrieve_secure_data(self):
        """Test secure data storage and retrieval."""
        handler = SecureDataHandler()

        data = {
            "transaction_id": "TX123",
            "amount": 5000.00,
            "account": "987654321"
        }

        identifier = "test_transaction"
        path = handler.store_secure_data(data, identifier)

        assert path is not None

        retrieved = handler.retrieve_secure_data(identifier)
        assert retrieved == data

    def test_sanitize_input(self):
        """Test input sanitization - now only strips whitespace."""
        handler = SecureDataHandler()

        dangerous_input = "'; DROP TABLE users; --"
        sanitized = handler.sanitize_input(dangerous_input)

        assert "'" not in sanitized
        assert ";" not in sanitized
        assert "--" not in sanitized


def test_generate_secure_filename():
    """Test secure filename generation."""
    original = "../../etc/passwd"
    secure = generate_secure_filename(original)

    assert ".." not in secure
    assert "/" not in secure
    assert "\\" not in secure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
