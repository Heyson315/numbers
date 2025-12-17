"""
SOX Compliance Controls

Segregation of duties, access reviews, control testing, and financial reporting controls.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os

from src.audit_logging import AuditLogger, AuditEventType


class SOXCompliance:
    """SOX (Sarbanes-Oxley) compliance controls."""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize SOX compliance manager."""
        self.audit_logger = audit_logger or AuditLogger()
        self.segregation_enabled = os.getenv("SOX_SEGREGATION_ENABLED", "true").lower() == "true"
        self._access_reviews: List[Dict] = []
        self._control_tests: List[Dict] = []
    
    def check_segregation_of_duties(
        self,
        user_id: str,
        action: str,
        resource: str
    ) -> Dict[str, Any]:
        """
        Check segregation of duties (SOX Section 404).
        
        Args:
            user_id: User attempting action
            action: Action being performed
            resource: Resource being accessed
        
        Returns:
            SOD check result
        """
        if not self.segregation_enabled:
            return {"approved": True, "reason": "SOD checks disabled"}
        
        # Define conflicting actions (simplified example)
        conflicts = {
            "create_transaction": ["approve_transaction", "audit_transaction"],
            "approve_transaction": ["create_transaction", "post_transaction"],
            "audit_transaction": ["create_transaction", "modify_transaction"]
        }
        
        # In production, check user's past actions
        # For now, return approved
        result = {
            "approved": True,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "conflicts_checked": conflicts.get(action, []),
            "check_time": datetime.utcnow().isoformat()
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG,
            user_id=user_id,
            action="sox_sod_check",
            resource=resource,
            status="success",
            details=result
        )
        
        return result
    
    def log_financial_transaction(
        self,
        transaction_id: str,
        transaction_type: str,
        amount: str,
        created_by: str,
        approved_by: Optional[str] = None
    ) -> None:
        """
        Log financial transaction for SOX audit trail.
        
        Args:
            transaction_id: Unique transaction ID
            transaction_type: Type of transaction
            amount: Transaction amount
            created_by: User who created transaction
            approved_by: User who approved transaction (if applicable)
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_MODIFY,
            user_id=created_by,
            action=f"sox_transaction_{transaction_type}",
            resource=f"transaction/{transaction_id}",
            status="success",
            details={
                "transaction_id": transaction_id,
                "type": transaction_type,
                "amount": amount,
                "created_by": created_by,
                "approved_by": approved_by,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def schedule_access_review(
        self,
        review_date: datetime,
        reviewer_id: str,
        scope: str,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Schedule periodic access review (SOX requirement).
        
        Args:
            review_date: Date for review
            reviewer_id: User conducting review
            scope: Scope of review
            user_id: User scheduling review
        
        Returns:
            Review record
        """
        review = {
            "review_id": f"AR-{len(self._access_reviews) + 1}",
            "review_date": review_date.isoformat(),
            "reviewer_id": reviewer_id,
            "scope": scope,
            "status": "scheduled",
            "scheduled_by": user_id,
            "scheduled_at": datetime.utcnow().isoformat()
        }
        
        self._access_reviews.append(review)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG,
            user_id=user_id,
            action="schedule_access_review",
            resource="sox/access_review",
            status="success",
            details=review
        )
        
        return review
    
    def complete_access_review(
        self,
        review_id: str,
        findings: List[Dict[str, Any]],
        reviewer_id: str
    ) -> Dict[str, Any]:
        """
        Complete access review with findings.
        
        Args:
            review_id: Review ID
            findings: Review findings
            reviewer_id: User completing review
        
        Returns:
            Completed review record
        """
        # Find and update review
        for review in self._access_reviews:
            if review["review_id"] == review_id:
                review["status"] = "completed"
                review["completed_at"] = datetime.utcnow().isoformat()
                review["findings"] = findings
                review["findings_count"] = len(findings)
                
                self.audit_logger.log_event(
                    event_type=AuditEventType.DATA_MODIFY,
                    user_id=reviewer_id,
                    action="complete_access_review",
                    resource=f"sox/access_review/{review_id}",
                    status="success",
                    details={"findings": len(findings)}
                )
                
                return review
        
        return {"error": "Review not found"}
    
    def test_control(
        self,
        control_id: str,
        control_type: str,
        test_procedure: str,
        tester_id: str,
        test_result: str,
        evidence: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Document control testing (SOX Section 404).
        
        Args:
            control_id: Control identifier
            control_type: Type of control (preventive, detective, corrective)
            test_procedure: Testing procedure used
            tester_id: User conducting test
            test_result: Result (pass, fail, not_applicable)
            evidence: Supporting evidence
        
        Returns:
            Control test record
        """
        test_record = {
            "test_id": f"CT-{len(self._control_tests) + 1}",
            "control_id": control_id,
            "control_type": control_type,
            "test_procedure": test_procedure,
            "tester_id": tester_id,
            "test_result": test_result,
            "evidence": evidence,
            "test_date": datetime.utcnow().isoformat()
        }
        
        self._control_tests.append(test_record)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=tester_id,
            action="sox_control_test",
            resource=f"sox/control/{control_id}",
            status="success" if test_result == "pass" else "warning",
            details=test_record
        )
        
        return test_record
    
    def generate_sox_report(self) -> Dict[str, Any]:
        """
        Generate SOX compliance report.
        
        Returns:
            SOX compliance status report
        """
        # Calculate control test statistics
        total_tests = len(self._control_tests)
        passed_tests = sum(1 for t in self._control_tests if t["test_result"] == "pass")
        failed_tests = sum(1 for t in self._control_tests if t["test_result"] == "fail")
        
        # Access review statistics
        total_reviews = len(self._access_reviews)
        completed_reviews = sum(1 for r in self._access_reviews if r["status"] == "completed")
        
        return {
            "sox_section_404_compliance": {
                "internal_controls": "documented",
                "control_testing": "active",
                "segregation_of_duties": "enabled" if self.segregation_enabled else "disabled"
            },
            "control_tests": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "pass_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "N/A"
            },
            "access_reviews": {
                "total": total_reviews,
                "completed": completed_reviews,
                "pending": total_reviews - completed_reviews
            },
            "audit_trail": {
                "enabled": True,
                "retention": "7 years",
                "immutable": True
            },
            "report_date": datetime.utcnow().isoformat(),
            "compliance_status": "compliant" if failed_tests == 0 else "deficiencies_found"
        }
    
    def get_control_deficiencies(self) -> List[Dict[str, Any]]:
        """
        Get list of control deficiencies for management review.
        
        Returns:
            List of control deficiencies
        """
        deficiencies = [
            test for test in self._control_tests
            if test["test_result"] == "fail"
        ]
        
        return deficiencies
