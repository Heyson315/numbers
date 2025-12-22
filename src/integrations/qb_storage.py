"""QuickBooks Token Storage with Azure SQL Support"""
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

# pyodbc is optional - falls back to in-memory storage if not available
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    pyodbc = None
    PYODBC_AVAILABLE = False

logger = logging.getLogger(__name__)


class QBTokenStorage:
    """
    Persistent storage for QuickBooks OAuth tokens using Azure SQL.
    Falls back to in-memory storage if database is unavailable.
    """
    
    def __init__(self):
        self.connection_string = os.getenv("AZURE_SQL_CONNECTION_STRING") if PYODBC_AVAILABLE else None
        self._memory_cache: Dict[str, Any] = {}
        self._initialized = False
        
        if self.connection_string and PYODBC_AVAILABLE:
            self._init_database()
        else:
            if not PYODBC_AVAILABLE:
                logger.warning("pyodbc not installed - using in-memory storage (pip install pyodbc)")
            else:
                logger.warning("AZURE_SQL_CONNECTION_STRING not set - using in-memory storage")
    
    def _get_connection(self):
        """Get database connection."""
        if not self.connection_string or not PYODBC_AVAILABLE:
            return None
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def _init_database(self):
        """Initialize the QB tokens table if it doesn't exist."""
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='qb_tokens' AND xtype='U')
                CREATE TABLE qb_tokens (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    user_id NVARCHAR(255) DEFAULT 'default',
                    access_token NVARCHAR(MAX),
                    refresh_token NVARCHAR(MAX),
                    realm_id NVARCHAR(255),
                    token_type NVARCHAR(50),
                    expires_at DATETIME2,
                    created_at DATETIME2 DEFAULT GETUTCDATE(),
                    updated_at DATETIME2 DEFAULT GETUTCDATE(),
                    CONSTRAINT UQ_user_realm UNIQUE (user_id, realm_id)
                )
            """)
            conn.commit()
            self._initialized = True
            logger.info("QB tokens table initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
        finally:
            conn.close()
    
    def save_tokens(self, tokens: Dict[str, Any], user_id: str = "default") -> bool:
        """
        Save QuickBooks tokens to database.
        
        Args:
            tokens: Dict containing access_token, refresh_token, realm_id, etc.
            user_id: User identifier (for multi-tenant support)
        
        Returns:
            True if saved successfully
        """
        # Always update memory cache
        cache_key = f"{user_id}:{tokens.get('realm_id', 'default')}"
        self._memory_cache[cache_key] = {**tokens, "updated_at": datetime.now(timezone.utc).isoformat()}
        
        conn = self._get_connection()
        if not conn:
            logger.warning("Using in-memory storage only")
            return True
        
        try:
            cursor = conn.cursor()
            
            # Upsert tokens (MERGE for SQL Server)
            cursor.execute("""
                MERGE qb_tokens AS target
                USING (SELECT ? AS user_id, ? AS realm_id) AS source
                ON target.user_id = source.user_id AND target.realm_id = source.realm_id
                WHEN MATCHED THEN
                    UPDATE SET 
                        access_token = ?,
                        refresh_token = ?,
                        token_type = ?,
                        expires_at = ?,
                        updated_at = GETUTCDATE()
                WHEN NOT MATCHED THEN
                    INSERT (user_id, realm_id, access_token, refresh_token, token_type, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?);
            """, (
                user_id, tokens.get("realm_id"),
                tokens.get("access_token"), tokens.get("refresh_token"),
                tokens.get("token_type", "Bearer"), tokens.get("expires_at"),
                user_id, tokens.get("realm_id"),
                tokens.get("access_token"), tokens.get("refresh_token"),
                tokens.get("token_type", "Bearer"), tokens.get("expires_at")
            ))
            conn.commit()
            logger.info(f"Tokens saved for user {user_id}, realm {tokens.get('realm_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            return False
        finally:
            conn.close()
    
    def get_tokens(self, user_id: str = "default", realm_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve QuickBooks tokens from database.
        
        Args:
            user_id: User identifier
            realm_id: Optional specific realm ID
        
        Returns:
            Token dict or None if not found
        """
        # Check memory cache first
        if realm_id:
            cache_key = f"{user_id}:{realm_id}"
            if cache_key in self._memory_cache:
                return self._memory_cache[cache_key]
        
        conn = self._get_connection()
        if not conn:
            # Return from memory cache if no database
            for key, value in self._memory_cache.items():
                if key.startswith(f"{user_id}:"):
                    return value
            return None
        
        try:
            cursor = conn.cursor()
            
            if realm_id:
                cursor.execute("""
                    SELECT access_token, refresh_token, realm_id, token_type, expires_at, updated_at
                    FROM qb_tokens
                    WHERE user_id = ? AND realm_id = ?
                """, (user_id, realm_id))
            else:
                cursor.execute("""
                    SELECT TOP 1 access_token, refresh_token, realm_id, token_type, expires_at, updated_at
                    FROM qb_tokens
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                tokens = {
                    "access_token": row[0],
                    "refresh_token": row[1],
                    "realm_id": row[2],
                    "token_type": row[3],
                    "expires_at": row[4].isoformat() if row[4] else None,
                    "updated_at": row[5].isoformat() if row[5] else None
                }
                # Update cache
                cache_key = f"{user_id}:{tokens['realm_id']}"
                self._memory_cache[cache_key] = tokens
                return tokens
            return None
        except Exception as e:
            logger.error(f"Failed to get tokens: {e}")
            return None
        finally:
            conn.close()
    
    def delete_tokens(self, user_id: str = "default", realm_id: Optional[str] = None) -> bool:
        """
        Delete QuickBooks tokens (disconnect).
        
        Args:
            user_id: User identifier
            realm_id: Optional specific realm ID to delete
        
        Returns:
            True if deleted successfully
        """
        # Clear memory cache
        if realm_id:
            cache_key = f"{user_id}:{realm_id}"
            self._memory_cache.pop(cache_key, None)
        else:
            keys_to_delete = [k for k in self._memory_cache if k.startswith(f"{user_id}:")]
            for key in keys_to_delete:
                del self._memory_cache[key]
        
        conn = self._get_connection()
        if not conn:
            return True
        
        try:
            cursor = conn.cursor()
            
            if realm_id:
                cursor.execute("DELETE FROM qb_tokens WHERE user_id = ? AND realm_id = ?", (user_id, realm_id))
            else:
                cursor.execute("DELETE FROM qb_tokens WHERE user_id = ?", (user_id,))
            
            conn.commit()
            logger.info(f"Tokens deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete tokens: {e}")
            return False
        finally:
            conn.close()
    
    def is_connected(self, user_id: str = "default") -> bool:
        """Check if user has valid QuickBooks connection."""
        tokens = self.get_tokens(user_id)
        return tokens is not None and "access_token" in tokens


# Singleton instance
_storage: Optional[QBTokenStorage] = None


def get_qb_storage() -> QBTokenStorage:
    """Get the singleton QBTokenStorage instance."""
    global _storage
    if _storage is None:
        _storage = QBTokenStorage()
    return _storage
