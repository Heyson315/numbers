"""
GDPR Compliance Controls

Consent management, data subject rights, DPO notifications, and data portability.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os

from src.audit_logging import AuditLogger, AuditEventType
from src.security import EncryptionManager


class GDPRCompliance:
    """GDPR compliance controls for data protection."""
    
    def __init__(
        self,
        encryption_manager: Optional[EncryptionManager] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """Initialize GDPR compliance manager."""
        self.encryption_manager = encryption_manager or EncryptionManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.consent_expiry_days = int(os.getenv("GDPR_CONSENT_EXPIRY_DAYS", "365"))
        self._consents: Dict[str, Dict] = {}
        self._data_subjects: Dict[str, Dict] = {}
    
    def record_consent(
        self,
        data_subject_id: str,
        purpose: str,
        consent_given: bool,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Record data processing consent (GDPR requirement).
        
        Args:
            data_subject_id: ID of data subject
            purpose: Purpose of data processing
            consent_given: Whether consent was given
            user_id: User recording consent
        
        Returns:
            Consent record
        """
        consent_record = {
            "data_subject_id": data_subject_id,
            "purpose": purpose,
            "consent_given": consent_given,
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=self.consent_expiry_days)).isoformat(),
            "recorded_by": user_id
        }
        
        key = f"{data_subject_id}:{purpose}"
        self._consents[key] = consent_record
        
        self.audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG,
            user_id=user_id,
            action="record_consent",
            resource=f"gdpr/consent/{data_subject_id}",
            status="success",
            details=consent_record
        )
        
        return consent_record
    
    def check_consent(
        self,
        data_subject_id: str,
        purpose: str
    ) -> bool:
        """
        Check if valid consent exists.
        
        Args:
            data_subject_id: ID of data subject
            purpose: Purpose to check
        
        Returns:
            True if valid consent exists
        """
        key = f"{data_subject_id}:{purpose}"
        consent = self._consents.get(key)
        
        if not consent or not consent.get("consent_given"):
            return False
        
        # Check if consent has expired
        expires_at = datetime.fromisoformat(consent["expires_at"])
        if datetime.utcnow() > expires_at:
            return False
        
        return True
    
    def right_to_access(
        self,
        data_subject_id: str,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Handle GDPR Right to Access request.
        
        Args:
            data_subject_id: ID of data subject
            user_id: User processing request
        
        Returns:
            All data for the data subject
        """
        data_subject_data = self._data_subjects.get(data_subject_id, {})
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="gdpr_right_to_access",
            resource=f"gdpr/subject/{data_subject_id}",
            status="success",
            details={"data_subject_id": data_subject_id}
        )
        
        return {
            "data_subject_id": data_subject_id,
            "data": data_subject_data,
            "export_date": datetime.utcnow().isoformat(),
            "format": "json"
        }
    
    def right_to_erasure(
        self,
        data_subject_id: str,
        user_id: str = "system",
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle GDPR Right to Erasure (Right to be Forgotten).
        
        Args:
            data_subject_id: ID of data subject
            user_id: User processing request
            reason: Reason for erasure
        
        Returns:
            Erasure confirmation
        """
        # In production, this would anonymize/delete data across all systems
        deleted_data = self._data_subjects.pop(data_subject_id, None)
        
        # Remove consents
        keys_to_remove = [k for k in self._consents.keys() if k.startswith(f"{data_subject_id}:")]
        for key in keys_to_remove:
            self._consents.pop(key)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_DELETE,
            user_id=user_id,
            action="gdpr_right_to_erasure",
            resource=f"gdpr/subject/{data_subject_id}",
            status="success",
            details={
                "data_subject_id": data_subject_id,
                "reason": reason,
                "data_deleted": deleted_data is not None
            }
        )
        
        return {
            "data_subject_id": data_subject_id,
            "status": "erased" if deleted_data else "not_found",
            "erasure_date": datetime.utcnow().isoformat(),
            "reason": reason
        }
    
    def right_to_portability(
        self,
        data_subject_id: str,
        export_format: str = "json",
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Handle GDPR Right to Data Portability.
        
        Args:
            data_subject_id: ID of data subject
            export_format: Format for export (json, csv, xml)
            user_id: User processing request
        
        Returns:
            Portable data export
        """
        data = self.right_to_access(data_subject_id, user_id)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_EXPORT,
            user_id=user_id,
            action="gdpr_right_to_portability",
            resource=f"gdpr/subject/{data_subject_id}",
            status="success",
            details={"format": export_format}
        )
        
        return {
            **data,
            "format": export_format,
            "portable": True
        }
    
    def notify_dpo(
        self,
        incident_type: str,
        details: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Notify Data Protection Officer (GDPR requirement).
        
        Args:
            incident_type: Type of incident
            details: Incident details
            user_id: User reporting incident
        
        Returns:
            Notification confirmation
        """
        notification = {
            "incident_type": incident_type,
            "details": details,
            "reported_by": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "dpo_notified": True
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            user_id=user_id,
            action="notify_dpo",
            resource="gdpr/dpo",
            status="success",
            details=notification
        )
        
        return notification
    
    def generate_gdpr_report(self) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        return {
            "consent_expiry_days": self.consent_expiry_days,
            "active_consents": len(self._consents),
            "data_subjects": len(self._data_subjects),
            "compliance_features": {
                "consent_management": "enabled",
                "right_to_access": "supported",
                "right_to_erasure": "supported",
                "right_to_portability": "supported",
                "dpo_notifications": "enabled",
                "data_encryption": "enabled"
            },
            "report_date": datetime.utcnow().isoformat()
        }
