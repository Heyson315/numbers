"""
Audit Logging Module

Provides comprehensive audit trail functionality for tracking all operations
on sensitive financial data in compliance with CPA firm requirements.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pythonjsonlogger import jsonlogger
from enum import Enum


class AuditEventType(Enum):
    """Types of auditable events."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    PERMISSION_CHANGE = "permission_change"
    SYSTEM_CONFIG = "system_config"
    API_CALL = "api_call"
    SECURITY_ALERT = "security_alert"
    FAILED_AUTH = "failed_auth"


class AuditLogger:
    """Manages audit logging for all system operations."""

    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize audit logger.

        Args:
            log_path: Path to audit log file
        """
        self.log_path = log_path or os.getenv('AUDIT_LOG_PATH', './logs/audit.log')
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        # Create structured JSON logger
        self.logger = logging.getLogger('audit_logger')
        self.logger.setLevel(logging.INFO)

        # Configure JSON formatter
        log_handler = logging.FileHandler(self.log_path)
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(event_type)s %(user_id)s %(action)s %(resource)s %(status)s %(message)s'
        )
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler)

        # Also log to console for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        action: str,
        resource: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            user_id: User performing the action
            action: Description of action taken
            resource: Resource affected
            status: Success or failure status
            details: Additional event details
            ip_address: IP address of user
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO' if status == 'success' else 'WARNING',
            'event_type': event_type.value,
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'status': status,
            'ip_address': ip_address or 'unknown',
            'message': f"{user_id} performed {action} on {resource} - {status}"
        }

        if details:
            log_entry['details'] = details

        self.logger.info(json.dumps(log_entry))

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "read",
        ip_address: Optional[str] = None
    ) -> None:
        """Log data access event."""
        self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action=action,
            resource=f"{resource_type}:{resource_id}",
            status="success",
            ip_address=ip_address
        )

    def log_security_alert(
        self,
        user_id: str,
        alert_type: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> None:
        """Log security alert."""
        self.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            user_id=user_id,
            action=alert_type,
            resource="security",
            status="alert",
            details=details,
            ip_address=ip_address
        )

    def log_failed_auth(
        self,
        user_id: str,
        reason: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log failed authentication attempt."""
        self.log_event(
            event_type=AuditEventType.FAILED_AUTH,
            user_id=user_id,
            action="authentication",
            resource="login",
            status="failed",
            details={'reason': reason},
            ip_address=ip_address
        )

    def query_audit_log(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None
    ) -> List[Dict[str, Any]]:
        """
        Query audit log with filters.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            user_id: Filter by user
            event_type: Filter by event type

        Returns:
            List of matching audit log entries
        """
        results = []

        if not os.path.exists(self.log_path):
            return results

        with open(self.log_path, 'r') as log_file:
            for line in log_file:
                try:
                    entry = json.loads(line)

                    # Apply filters
                    if start_date and datetime.fromisoformat(entry['timestamp']) < start_date:
                        continue

                    if end_date and datetime.fromisoformat(entry['timestamp']) > end_date:
                        continue

                    if user_id and entry.get('user_id') != user_id:
                        continue

                    if event_type and entry.get('event_type') != event_type.value:
                        continue

                    results.append(entry)

                except (json.JSONDecodeError, KeyError):
                    continue

        return results

    def generate_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
        output_format: str = 'json'
    ) -> str:
        """
        Generate audit report for a time period.

        Args:
            start_date: Report start date
            end_date: Report end date
            output_format: Format of report (json, csv)

        Returns:
            Report as string
        """
        entries = self.query_audit_log(start_date=start_date, end_date=end_date)

        if output_format == 'json':
            return json.dumps({
                'report_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_events': len(entries),
                'events': entries
            }, indent=2)

        elif output_format == 'csv':
            if not entries:
                return "No audit entries found"

            # Create CSV header
            keys = entries[0].keys()
            csv_lines = [','.join(keys)]

            # Add data rows
            for entry in entries:
                values = [str(entry.get(key, '')) for key in keys]
                csv_lines.append(','.join(values))

            return '\n'.join(csv_lines)

        return "Unsupported format"


class ComplianceMonitor:
    """Monitors system activity for compliance violations."""

    def __init__(self, audit_logger: AuditLogger):
        """
        Initialize compliance monitor.

        Args:
            audit_logger: AuditLogger instance
        """
        self.audit_logger = audit_logger
        self.violation_threshold = {
            'failed_auth': 5,  # Max failed auth attempts
            'data_export': 10,  # Max exports per day per user
        }

    def check_failed_auth_attempts(
        self,
        user_id: str,
        time_window_minutes: int = 30
    ) -> bool:
        """
        Check if user has exceeded failed auth attempts.

        Args:
            user_id: User ID to check
            time_window_minutes: Time window for checking

        Returns:
            True if threshold exceeded, False otherwise
        """
        start_time = datetime.utcnow()
        start_time = start_time.replace(
            minute=start_time.minute - time_window_minutes
        )

        entries = self.audit_logger.query_audit_log(
            start_date=start_time,
            user_id=user_id,
            event_type=AuditEventType.FAILED_AUTH
        )

        if len(entries) >= self.violation_threshold['failed_auth']:
            self.audit_logger.log_security_alert(
                user_id=user_id,
                alert_type="excessive_failed_auth",
                details={
                    'attempts': len(entries),
                    'threshold': self.violation_threshold['failed_auth']
                }
            )
            return True

        return False

    def verify_data_retention(self, data_age_days: int) -> bool:
        """
        Verify data retention policy compliance.

        Args:
            data_age_days: Age of data in days

        Returns:
            True if within retention policy, False otherwise
        """
        retention_years = int(os.getenv('DATA_RETENTION_YEARS', '7'))
        max_age_days = retention_years * 365

        return data_age_days <= max_age_days
