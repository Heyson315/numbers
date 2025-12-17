"""
Immutable Audit Trail

Tamper-proof audit logging with cryptographic hashing (SHA-256 chain).
"""

import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.audit_logging import AuditLogger, AuditEventType


class ImmutableAuditTrail:
    """Immutable audit trail with blockchain-style chaining."""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize immutable audit trail."""
        self.audit_logger = audit_logger or AuditLogger()
        self._chain: List[Dict[str, Any]] = []
        self._previous_hash = "0" * 64  # Genesis hash
    
    def create_hash(self, data: Dict[str, Any], previous_hash: str) -> str:
        """
        Create SHA-256 hash of audit entry.
        
        Args:
            data: Audit entry data
            previous_hash: Hash of previous entry
        
        Returns:
            SHA-256 hash string
        """
        entry_string = json.dumps(data, sort_keys=True) + previous_hash
        return hashlib.sha256(entry_string.encode()).hexdigest()
    
    def add_entry(
        self,
        event_type: str,
        user_id: str,
        action: str,
        resource: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add immutable audit entry.
        
        Args:
            event_type: Type of event
            user_id: User ID
            action: Action performed
            resource: Resource affected
            status: Status of action
            details: Additional details
        
        Returns:
            Audit entry with hash
        """
        timestamp = datetime.utcnow().isoformat()
        
        entry_data = {
            "timestamp": timestamp,
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "status": status,
            "details": details or {}
        }
        
        # Create hash including previous hash
        current_hash = self.create_hash(entry_data, self._previous_hash)
        
        entry = {
            **entry_data,
            "hash": current_hash,
            "previous_hash": self._previous_hash,
            "index": len(self._chain)
        }
        
        self._chain.append(entry)
        self._previous_hash = current_hash
        
        # Also log to standard audit logger
        self.audit_logger.log_event(
            event_type=AuditEventType.API_CALL,
            user_id=user_id,
            action="immutable_audit_entry",
            resource="audit_chain",
            status="success",
            details={"hash": current_hash, "index": entry["index"]}
        )
        
        return entry
    
    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify integrity of audit chain.
        
        Returns:
            Verification result with any tampering detected
        """
        if not self._chain:
            return {"valid": True, "message": "Empty chain"}
        
        previous_hash = "0" * 64
        
        for i, entry in enumerate(self._chain):
            # Verify previous hash matches
            if entry["previous_hash"] != previous_hash:
                return {
                    "valid": False,
                    "message": f"Chain broken at index {i}",
                    "details": {
                        "index": i,
                        "expected_previous_hash": previous_hash,
                        "actual_previous_hash": entry["previous_hash"]
                    }
                }
            
            # Verify current hash
            entry_data = {k: v for k, v in entry.items() if k not in ["hash", "previous_hash", "index"]}
            expected_hash = self.create_hash(entry_data, previous_hash)
            
            if entry["hash"] != expected_hash:
                return {
                    "valid": False,
                    "message": f"Entry tampered at index {i}",
                    "details": {
                        "index": i,
                        "expected_hash": expected_hash,
                        "actual_hash": entry["hash"]
                    }
                }
            
            previous_hash = entry["hash"]
        
        return {
            "valid": True,
            "message": "Audit chain verified successfully",
            "entries": len(self._chain)
        }
    
    def get_entries(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit entries with optional filters.
        
        Args:
            user_id: Filter by user ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
        
        Returns:
            List of matching audit entries
        """
        entries = self._chain
        
        if user_id:
            entries = [e for e in entries if e["user_id"] == user_id]
        
        if start_date:
            entries = [e for e in entries if e["timestamp"] >= start_date]
        
        if end_date:
            entries = [e for e in entries if e["timestamp"] <= end_date]
        
        return entries
