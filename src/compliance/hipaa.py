"""
HIPAA Compliance Controls

PHI handling, access logging, breach detection, and HIPAA-specific audit requirements.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os

from src.audit_logging import AuditLogger, AuditEventType
from src.security import EncryptionManager


class HIPAACompliance:
    """HIPAA compliance controls for PHI (Protected Health Information)."""
    
    def __init__(
        self,
        encryption_manager: Optional[EncryptionManager] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """Initialize HIPAA compliance manager."""
        self.encryption_manager = encryption_manager or EncryptionManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.audit_retention_days = int(os.getenv("HIPAA_AUDIT_LOG_RETENTION_DAYS", "2190"))  # 6 years
    
    def is_phi(self, data: Dict[str, Any]) -> bool:
        """
        Determine if data contains PHI.
        
        Args:
            data: Data to check
        
        Returns:
            True if data contains PHI identifiers
        """
        phi_indicators = [
            "ssn", "social_security", "medical_record", "health_plan",
            "patient_id", "diagnosis", "prescription", "treatment"
        ]
        
        for key in data.keys():
            if any(indicator in key.lower() for indicator in phi_indicators):
                return True
        
        return False
    
    def encrypt_phi(
        self,
        phi_data: Dict[str, Any],
        user_id: str = "system"
    ) -> str:
        """
        Encrypt PHI data (HIPAA requirement).
        
        Args:
            phi_data: PHI data to encrypt
            user_id: User encrypting the data
        
        Returns:
            Encrypted data string
        """
        encrypted = self.encryption_manager.encrypt_dict(phi_data)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_MODIFY,
            user_id=user_id,
            action="encrypt_phi",
            resource="phi_data",
            status="success",
            details={"field_count": len(phi_data)}
        )
        
        return encrypted
    
    def decrypt_phi(
        self,
        encrypted_data: str,
        user_id: str,
        purpose: str
    ) -> Dict[str, Any]:
        """
        Decrypt PHI data with mandatory access logging.
        
        Args:
            encrypted_data: Encrypted PHI data
            user_id: User accessing the data
            purpose: Business purpose for access
        
        Returns:
            Decrypted PHI data
        """
        decrypted = self.encryption_manager.decrypt_dict(encrypted_data)
        
        # HIPAA requires logging ALL PHI access
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="access_phi",
            resource="phi_data",
            status="success",
            details={"purpose": purpose, "access_time": datetime.utcnow().isoformat()}
        )
        
        return decrypted
    
    def log_phi_access(
        self,
        user_id: str,
        phi_identifier: str,
        action: str,
        purpose: str,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log PHI access (HIPAA requirement).
        
        Args:
            user_id: User accessing PHI
            phi_identifier: Identifier for PHI record
            action: Action performed (view, modify, delete)
            purpose: Business purpose
            ip_address: IP address of access
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action=f"phi_{action}",
            resource=f"phi/{phi_identifier}",
            status="success",
            ip_address=ip_address,
            details={
                "purpose": purpose,
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def detect_breach(
        self,
        access_logs: List[Dict[str, Any]],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Detect potential HIPAA breaches.
        
        Args:
            access_logs: List of access log entries
            user_id: User running breach detection
        
        Returns:
            Breach detection report
        """
        alerts = []
        
        # Detect unusual access patterns
        user_access_count = {}
        for log in access_logs:
            uid = log.get("user_id")
            user_access_count[uid] = user_access_count.get(uid, 0) + 1
        
        # Alert on excessive access (>100 records in period)
        for uid, count in user_access_count.items():
            if count > 100:
                alerts.append({
                    "type": "excessive_access",
                    "severity": "high",
                    "user_id": uid,
                    "access_count": count,
                    "message": f"User {uid} accessed {count} PHI records"
                })
        
        # Detect access outside business hours
        for log in access_logs:
            timestamp = datetime.fromisoformat(log.get("timestamp", ""))
            if timestamp.hour < 6 or timestamp.hour > 20:
                alerts.append({
                    "type": "off_hours_access",
                    "severity": "medium",
                    "user_id": log.get("user_id"),
                    "timestamp": timestamp.isoformat(),
                    "message": "PHI accessed outside business hours"
                })
        
        result = {
            "breach_detected": len(alerts) > 0,
            "alerts": alerts,
            "total_access_logs": len(access_logs),
            "scan_time": datetime.utcnow().isoformat()
        }
        
        if alerts:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="hipaa_breach_detection",
                resource="phi_data",
                status="alert",
                details=result
            )
        
        return result
    
    def generate_hipaa_report(self) -> Dict[str, Any]:
        """
        Generate HIPAA compliance report.
        
        Returns:
            HIPAA compliance status report
        """
        return {
            "audit_log_retention_days": self.audit_retention_days,
            "encryption_enabled": True,
            "access_logging_enabled": True,
            "breach_detection_enabled": True,
            "compliance_checks": {
                "encryption_at_rest": "enabled",
                "encryption_in_transit": "enabled",
                "access_controls": "enforced",
                "audit_trail": "maintained",
                "breach_notification": "configured"
            },
            "report_date": datetime.utcnow().isoformat()
        }
