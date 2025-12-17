"""
Adjusting Entry Suggester

ML-based automated adjusting entry suggestions.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.audit_logging import AuditLogger, AuditEventType


class AdjustingEntrySuggester:
    """Suggest adjusting entries using ML pattern recognition."""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize suggester."""
        self.audit_logger = audit_logger or AuditLogger()
    
    def suggest_accrual_entries(
        self,
        transactions: List[Dict[str, Any]],
        period_end: date,
        user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """
        Suggest accrual adjusting entries.
        
        Args:
            transactions: List of transactions
            period_end: Period end date
            user_id: User ID for audit logging
        
        Returns:
            List of suggested adjusting entries
        """
        suggestions = []
        
        # Analyze recurring expenses that may need accrual
        df = pd.DataFrame(transactions)
        if df.empty:
            return suggestions
        
        # Find recurring expenses
        if 'description' in df.columns and 'amount' in df.columns:
            recurring = df.groupby('description')['amount'].agg(['count', 'mean', 'std']).reset_index()
            recurring = recurring[recurring['count'] >= 3]  # At least 3 occurrences
            
            for _, row in recurring.iterrows():
                if row['std'] / row['mean'] < 0.2:  # Low variance indicates recurring
                    suggestions.append({
                        "type": "accrual",
                        "description": f"Accrued {row['description']}",
                        "estimated_amount": str(Decimal(str(row['mean'])).quantize(Decimal("0.01"))),
                        "confidence": "high",
                        "reason": "Recurring expense pattern detected"
                    })
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="suggest_accrual_entries",
            resource="adjusting_entries",
            status="success",
            details={"suggestions": len(suggestions)}
        )
        
        return suggestions
    
    def suggest_prepayment_entries(
        self,
        prepaid_accounts: List[Dict[str, Any]],
        period_end: date,
        user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """Suggest prepayment adjusting entries."""
        suggestions = []
        
        for account in prepaid_accounts:
            balance = Decimal(str(account.get("balance", 0)))
            months_remaining = account.get("months_remaining", 12)
            
            if balance > 0 and months_remaining > 0:
                monthly_expense = balance / Decimal(str(months_remaining))
                suggestions.append({
                    "type": "prepayment_amortization",
                    "account": account.get("account_name"),
                    "debit_account": "Expense",
                    "credit_account": "Prepaid",
                    "amount": str(monthly_expense.quantize(Decimal("0.01"))),
                    "confidence": "high",
                    "reason": "Prepayment amortization"
                })
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="suggest_prepayment_entries",
            resource="adjusting_entries",
            status="success",
            details={"suggestions": len(suggestions)}
        )
        
        return suggestions
    
    def suggest_depreciation_entries(
        self,
        fixed_assets: List[Dict[str, Any]],
        user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """Suggest depreciation adjusting entries."""
        suggestions = []
        
        for asset in fixed_assets:
            cost = Decimal(str(asset.get("cost", 0)))
            salvage_value = Decimal(str(asset.get("salvage_value", 0)))
            useful_life_years = asset.get("useful_life_years", 5)
            
            if cost > 0 and useful_life_years > 0:
                annual_depreciation = (cost - salvage_value) / Decimal(str(useful_life_years))
                monthly_depreciation = annual_depreciation / Decimal("12")
                
                suggestions.append({
                    "type": "depreciation",
                    "asset": asset.get("asset_name"),
                    "debit_account": "Depreciation Expense",
                    "credit_account": "Accumulated Depreciation",
                    "monthly_amount": str(monthly_depreciation.quantize(Decimal("0.01"))),
                    "annual_amount": str(annual_depreciation.quantize(Decimal("0.01"))),
                    "confidence": "high",
                    "reason": "Straight-line depreciation"
                })
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="suggest_depreciation_entries",
            resource="adjusting_entries",
            status="success",
            details={"suggestions": len(suggestions)}
        )
        
        return suggestions
