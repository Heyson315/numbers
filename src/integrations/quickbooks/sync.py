"""
QuickBooks Sync Module

Two-way synchronization for trial balance, journal entries, and invoices.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
import asyncio

from src.audit_logging import AuditLogger, AuditEventType
from .client import QuickBooksClient
from .models import QBOInvoice, QBOJournalEntry, QBOTrialBalance


class QuickBooksSync:
    """Handle two-way synchronization with QuickBooks Online."""
    
    def __init__(
        self,
        client: QuickBooksClient,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize sync manager.
        
        Args:
            client: QuickBooksClient instance
            audit_logger: Audit logger for sync operations
        """
        self.client = client
        self.audit_logger = audit_logger or AuditLogger()
    
    async def sync_trial_balance(
        self,
        start_date: str,
        end_date: str,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Sync trial balance from QuickBooks.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            user_id: User ID for audit logging
        
        Returns:
            Sync result with trial balance data
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="sync_trial_balance",
            resource="quickbooks",
            status="initiated",
            details={"start_date": start_date, "end_date": end_date}
        )
        
        try:
            trial_balance = await self.client.get_trial_balance(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            result = {
                "status": "success",
                "trial_balance": trial_balance.dict(),
                "synced_at": datetime.utcnow().isoformat(),
                "account_count": len(trial_balance.accounts)
            }
            
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=user_id,
                action="sync_trial_balance",
                resource="quickbooks",
                status="success",
                details=result
            )
            
            return result
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action="sync_trial_balance",
                resource="quickbooks",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def sync_journal_entries(
        self,
        start_date: str,
        end_date: str,
        direction: str = "pull",
        entries: Optional[List[QBOJournalEntry]] = None,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Sync journal entries (pull from QBO or push to QBO).
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            direction: 'pull' (from QBO) or 'push' (to QBO)
            entries: Journal entries to push (if direction='push')
            user_id: User ID for audit logging
        
        Returns:
            Sync result
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_MODIFY if direction == "push" else AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action=f"sync_journal_entries_{direction}",
            resource="quickbooks",
            status="initiated",
            details={"start_date": start_date, "end_date": end_date}
        )
        
        try:
            if direction == "pull":
                # Pull journal entries from QBO
                journal_entries = await self.client.get_journal_entries(
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                result = {
                    "status": "success",
                    "direction": "pull",
                    "entries": [je.dict() for je in journal_entries],
                    "count": len(journal_entries),
                    "synced_at": datetime.utcnow().isoformat()
                }
                
            elif direction == "push" and entries:
                # Push journal entries to QBO
                created_entries = []
                errors = []
                
                for entry in entries:
                    try:
                        created = await self.client.create_journal_entry(entry, user_id)
                        created_entries.append(created.dict())
                    except Exception as e:
                        errors.append({"entry": entry.dict(), "error": str(e)})
                
                result = {
                    "status": "success" if not errors else "partial",
                    "direction": "push",
                    "created_count": len(created_entries),
                    "error_count": len(errors),
                    "created_entries": created_entries,
                    "errors": errors,
                    "synced_at": datetime.utcnow().isoformat()
                }
            else:
                raise ValueError("Invalid direction or missing entries for push")
            
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_MODIFY if direction == "push" else AuditEventType.DATA_ACCESS,
                user_id=user_id,
                action=f"sync_journal_entries_{direction}",
                resource="quickbooks",
                status="success",
                details={"count": result.get("count") or result.get("created_count")}
            )
            
            return result
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action=f"sync_journal_entries_{direction}",
                resource="quickbooks",
                status="error",
                details={"error": str(e)}
            )
            raise
    
    async def sync_invoices(
        self,
        start_date: str,
        end_date: str,
        direction: str = "pull",
        invoices: Optional[List[QBOInvoice]] = None,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Sync invoices (pull from QBO or push to QBO).
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            direction: 'pull' (from QBO) or 'push' (to QBO)
            invoices: Invoices to push (if direction='push')
            user_id: User ID for audit logging
        
        Returns:
            Sync result
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_MODIFY if direction == "push" else AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action=f"sync_invoices_{direction}",
            resource="quickbooks",
            status="initiated",
            details={"start_date": start_date, "end_date": end_date}
        )
        
        try:
            if direction == "pull":
                # Pull invoices from QBO
                qbo_invoices = await self.client.get_invoices(
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                result = {
                    "status": "success",
                    "direction": "pull",
                    "invoices": [inv.dict() for inv in qbo_invoices],
                    "count": len(qbo_invoices),
                    "synced_at": datetime.utcnow().isoformat()
                }
                
            elif direction == "push" and invoices:
                # Push invoices to QBO
                created_invoices = []
                errors = []
                
                for invoice in invoices:
                    try:
                        created = await self.client.create_invoice(invoice, user_id)
                        created_invoices.append(created.dict())
                    except Exception as e:
                        errors.append({"invoice": invoice.dict(), "error": str(e)})
                
                result = {
                    "status": "success" if not errors else "partial",
                    "direction": "push",
                    "created_count": len(created_invoices),
                    "error_count": len(errors),
                    "created_invoices": created_invoices,
                    "errors": errors,
                    "synced_at": datetime.utcnow().isoformat()
                }
            else:
                raise ValueError("Invalid direction or missing invoices for push")
            
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_MODIFY if direction == "push" else AuditEventType.DATA_ACCESS,
                user_id=user_id,
                action=f"sync_invoices_{direction}",
                resource="quickbooks",
                status="success",
                details={"count": result.get("count") or result.get("created_count")}
            )
            
            return result
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user_id,
                action=f"sync_invoices_{direction}",
                resource="quickbooks",
                status="error",
                details={"error": str(e)}
            )
            raise
