"""
Trial Balance Analysis

Variance detection and analysis for trial balance reports.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import date
import pandas as pd

from src.audit_logging import AuditLogger, AuditEventType


class TrialBalanceAnalyzer:
    """Analyze trial balance with variance detection."""
    
    def __init__(
        self,
        materiality_threshold: Optional[Decimal] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize trial balance analyzer.
        
        Args:
            materiality_threshold: Materiality threshold for variance detection (default: 0.05 = 5%)
            audit_logger: Audit logger
        """
        self.materiality_threshold = materiality_threshold or Decimal("0.05")
        self.audit_logger = audit_logger or AuditLogger()
    
    def analyze_trial_balance(
        self,
        trial_balance: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Analyze trial balance for accuracy and balance.
        
        Args:
            trial_balance: Trial balance data with accounts, debits, credits
            user_id: User ID for audit logging
        
        Returns:
            Analysis results with any issues detected
        """
        accounts = trial_balance.get("accounts", [])
        total_debits = Decimal(str(trial_balance.get("total_debits", 0)))
        total_credits = Decimal(str(trial_balance.get("total_credits", 0)))
        
        issues = []
        warnings = []
        
        # Check if debits equal credits
        difference = abs(total_debits - total_credits)
        if difference > Decimal("0.01"):
            issues.append({
                "type": "out_of_balance",
                "severity": "critical",
                "message": f"Trial balance is out of balance by {difference}",
                "debits": str(total_debits),
                "credits": str(total_credits),
                "difference": str(difference)
            })
        
        # Check for zero balance accounts
        zero_balance_accounts = [
            acc for acc in accounts
            if Decimal(str(acc.get("debit", 0))) == 0 and Decimal(str(acc.get("credit", 0))) == 0
        ]
        
        if zero_balance_accounts:
            warnings.append({
                "type": "zero_balance_accounts",
                "severity": "low",
                "message": f"Found {len(zero_balance_accounts)} accounts with zero balance",
                "accounts": [acc.get("account_name") for acc in zero_balance_accounts[:10]]
            })
        
        # Check for unusually large accounts (> 50% of total)
        large_threshold = total_debits * Decimal("0.5")
        for acc in accounts:
            acc_balance = max(Decimal(str(acc.get("debit", 0))), Decimal(str(acc.get("credit", 0))))
            if acc_balance > large_threshold:
                warnings.append({
                    "type": "large_account_balance",
                    "severity": "medium",
                    "message": f"Account {acc.get('account_name')} represents >50% of total",
                    "account": acc.get("account_name"),
                    "balance": str(acc_balance),
                    "percentage": str((acc_balance / total_debits * 100).quantize(Decimal("0.01")))
                })
        
        result = {
            "is_balanced": len(issues) == 0,
            "total_debits": str(total_debits),
            "total_credits": str(total_credits),
            "difference": str(difference),
            "account_count": len(accounts),
            "issues": issues,
            "warnings": warnings,
            "analysis_date": date.today().isoformat()
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="analyze_trial_balance",
            resource="trial_balance",
            status="success" if result["is_balanced"] else "warning",
            details={"issues": len(issues), "warnings": len(warnings)}
        )
        
        return result
    
    def compare_periods(
        self,
        current_period: Dict[str, Any],
        prior_period: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Compare trial balance between periods.
        
        Args:
            current_period: Current period trial balance
            prior_period: Prior period trial balance
            user_id: User ID for audit logging
        
        Returns:
            Period comparison results with variances
        """
        current_accounts = {acc["account_name"]: acc for acc in current_period.get("accounts", [])}
        prior_accounts = {acc["account_name"]: acc for acc in prior_period.get("accounts", [])}
        
        variances = []
        
        for acc_name, current_acc in current_accounts.items():
            prior_acc = prior_accounts.get(acc_name)
            
            if not prior_acc:
                # New account
                variances.append({
                    "account": acc_name,
                    "variance_type": "new_account",
                    "current_balance": str(current_acc.get("debit", 0) or current_acc.get("credit", 0)),
                    "prior_balance": "0",
                    "variance": "N/A"
                })
                continue
            
            # Calculate variance
            current_balance = Decimal(str(current_acc.get("debit", 0) or current_acc.get("credit", 0)))
            prior_balance = Decimal(str(prior_acc.get("debit", 0) or prior_acc.get("credit", 0)))
            
            if prior_balance != 0:
                variance_pct = ((current_balance - prior_balance) / prior_balance) * 100
                
                # Check if variance exceeds materiality threshold
                if abs(variance_pct) > (self.materiality_threshold * 100):
                    variances.append({
                        "account": acc_name,
                        "variance_type": "material_change",
                        "current_balance": str(current_balance),
                        "prior_balance": str(prior_balance),
                        "variance_amount": str(current_balance - prior_balance),
                        "variance_pct": str(variance_pct.quantize(Decimal("0.01")))
                    })
        
        result = {
            "current_period_date": current_period.get("report_date"),
            "prior_period_date": prior_period.get("report_date"),
            "material_variances": variances,
            "variance_count": len(variances),
            "materiality_threshold": str(self.materiality_threshold * 100) + "%"
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="compare_trial_balance_periods",
            resource="trial_balance",
            status="success",
            details={"variances": len(variances)}
        )
        
        return result
    
    def budget_vs_actual(
        self,
        actual: Dict[str, Any],
        budget: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Compare actual vs budget.
        
        Args:
            actual: Actual trial balance
            budget: Budget trial balance
            user_id: User ID for audit logging
        
        Returns:
            Budget variance analysis
        """
        actual_accounts = {acc["account_name"]: acc for acc in actual.get("accounts", [])}
        budget_accounts = {acc["account_name"]: acc for acc in budget.get("accounts", [])}
        
        variances = []
        
        for acc_name, actual_acc in actual_accounts.items():
            budget_acc = budget_accounts.get(acc_name)
            
            if not budget_acc:
                continue
            
            actual_balance = Decimal(str(actual_acc.get("debit", 0) or actual_acc.get("credit", 0)))
            budget_balance = Decimal(str(budget_acc.get("debit", 0) or budget_acc.get("credit", 0)))
            
            if budget_balance != 0:
                variance_pct = ((actual_balance - budget_balance) / budget_balance) * 100
                variance_status = "favorable" if variance_pct < 0 else "unfavorable"
                
                variances.append({
                    "account": acc_name,
                    "actual": str(actual_balance),
                    "budget": str(budget_balance),
                    "variance_amount": str(actual_balance - budget_balance),
                    "variance_pct": str(variance_pct.quantize(Decimal("0.01"))),
                    "status": variance_status
                })
        
        result = {
            "total_variances": len(variances),
            "variances": sorted(variances, key=lambda x: abs(Decimal(x["variance_pct"])), reverse=True),
            "analysis_date": date.today().isoformat()
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="budget_vs_actual_analysis",
            resource="trial_balance",
            status="success",
            details={"variances": len(variances)}
        )
        
        return result
