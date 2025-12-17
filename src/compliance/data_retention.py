"""
Data Retention Manager

Configurable retention policies (SOX 7-year, HIPAA 6-year).
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from src.audit_logging import AuditLogger, AuditEventType


class RetentionPolicy(Enum):
    """Compliance-based retention policies."""
    SOX = 7 * 365  # 7 years in days
    HIPAA = 6 * 365  # 6 years in days
    GDPR = 365  # 1 year minimum
    DEFAULT = 7 * 365  # Default 7 years


class DataRetentionManager:
    """Manage data retention policies."""
    
    def __init__(
        self,
        default_retention_days: Optional[int] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize retention manager.
        
        Args:
            default_retention_days: Default retention period in days
            audit_logger: Audit logger
        """
        self.default_retention_days = default_retention_days or int(
            os.getenv("DATA_RETENTION_YEARS", "7")
        ) * 365
        self.audit_logger = audit_logger or AuditLogger()
        self._retention_policies: Dict[str, int] = {}
    
    def set_policy(
        self,
        data_type: str,
        retention_days: int,
        user_id: str = "system"
    ) -> None:
        """
        Set retention policy for data type.
        
        Args:
            data_type: Type of data (e.g., 'financial_records', 'audit_logs')
            retention_days: Retention period in days
            user_id: User setting the policy
        """
        self._retention_policies[data_type] = retention_days
        
        self.audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG,
            user_id=user_id,
            action="set_retention_policy",
            resource=f"retention/{data_type}",
            status="success",
            details={"retention_days": retention_days}
        )
    
    def get_policy(self, data_type: str) -> int:
        """Get retention policy for data type (in days)."""
        return self._retention_policies.get(data_type, self.default_retention_days)
    
    def should_retain(
        self,
        data_type: str,
        created_date: datetime
    ) -> bool:
        """
        Check if data should be retained.
        
        Args:
            data_type: Type of data
            created_date: Date data was created
        
        Returns:
            True if data should be retained
        """
        retention_days = self.get_policy(data_type)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return created_date >= cutoff_date
    
    def find_expired_data(
        self,
        data_records: List[Dict],
        data_type: str
    ) -> List[Dict]:
        """
        Find data records that have expired.
        
        Args:
            data_records: List of data records with 'created_at' field
            data_type: Type of data
        
        Returns:
            List of expired records
        """
        retention_days = self.get_policy(data_type)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        expired = [
            record for record in data_records
            if datetime.fromisoformat(record.get("created_at", "")) < cutoff_date
        ]
        
        return expired
    
    def apply_retention_policy(
        self,
        data_type: str,
        records: List[Dict],
        user_id: str = "system",
        dry_run: bool = True
    ) -> Dict:
        """
        Apply retention policy to data records.
        
        Args:
            data_type: Type of data
            records: List of data records
            user_id: User applying policy
            dry_run: If True, only report what would be deleted
        
        Returns:
            Result of retention policy application
        """
        expired = self.find_expired_data(records, data_type)
        
        result = {
            "data_type": data_type,
            "total_records": len(records),
            "expired_records": len(expired),
            "retention_days": self.get_policy(data_type),
            "dry_run": dry_run,
            "deleted": [] if dry_run else [r.get("id") for r in expired]
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_DELETE if not dry_run else AuditEventType.SYSTEM_CONFIG,
            user_id=user_id,
            action="apply_retention_policy",
            resource=f"retention/{data_type}",
            status="success",
            details=result
        )
        
        return result
    
    def get_compliance_report(self) -> Dict:
        """
        Generate compliance report for retention policies.
        
        Returns:
            Compliance report
        """
        return {
            "default_retention_days": self.default_retention_days,
            "policies": {
                data_type: days
                for data_type, days in self._retention_policies.items()
            },
            "compliance_standards": {
                "SOX": f"{RetentionPolicy.SOX.value} days (7 years)",
                "HIPAA": f"{RetentionPolicy.HIPAA.value} days (6 years)",
                "GDPR": f"{RetentionPolicy.GDPR.value} days minimum"
            },
            "report_date": datetime.utcnow().isoformat()
        }
