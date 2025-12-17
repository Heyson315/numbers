"""
Financial Ratios Calculator

Comprehensive financial ratio calculations (liquidity, profitability, leverage, efficiency).
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import date

from src.audit_logging import AuditLogger, AuditEventType


class FinancialRatiosCalculator:
    """Calculate comprehensive financial ratios."""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize ratios calculator."""
        self.audit_logger = audit_logger or AuditLogger()
    
    def calculate_all_ratios(
        self,
        financial_data: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Calculate all financial ratios.
        
        Args:
            financial_data: Dictionary with financial statement data
            user_id: User ID for audit logging
        
        Returns:
            Dictionary with all calculated ratios
        """
        liquidity = self.calculate_liquidity_ratios(financial_data)
        profitability = self.calculate_profitability_ratios(financial_data)
        leverage = self.calculate_leverage_ratios(financial_data)
        efficiency = self.calculate_efficiency_ratios(financial_data)
        
        result = {
            "liquidity_ratios": liquidity,
            "profitability_ratios": profitability,
            "leverage_ratios": leverage,
            "efficiency_ratios": efficiency,
            "calculation_date": date.today().isoformat()
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="calculate_financial_ratios",
            resource="financial_ratios",
            status="success"
        )
        
        return result
    
    def calculate_liquidity_ratios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate liquidity ratios."""
        current_assets = Decimal(str(data.get("current_assets", 0)))
        current_liabilities = Decimal(str(data.get("current_liabilities", 0)))
        inventory = Decimal(str(data.get("inventory", 0)))
        cash = Decimal(str(data.get("cash", 0)))
        
        ratios = {}
        
        # Current Ratio
        if current_liabilities > 0:
            ratios["current_ratio"] = str((current_assets / current_liabilities).quantize(Decimal("0.01")))
        
        # Quick Ratio (Acid-Test)
        if current_liabilities > 0:
            quick_assets = current_assets - inventory
            ratios["quick_ratio"] = str((quick_assets / current_liabilities).quantize(Decimal("0.01")))
        
        # Cash Ratio
        if current_liabilities > 0:
            ratios["cash_ratio"] = str((cash / current_liabilities).quantize(Decimal("0.01")))
        
        return ratios
    
    def calculate_profitability_ratios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate profitability ratios."""
        net_income = Decimal(str(data.get("net_income", 0)))
        revenue = Decimal(str(data.get("revenue", 0)))
        total_assets = Decimal(str(data.get("total_assets", 0)))
        total_equity = Decimal(str(data.get("total_equity", 0)))
        
        ratios = {}
        
        # Net Profit Margin
        if revenue > 0:
            ratios["net_profit_margin"] = str(((net_income / revenue) * 100).quantize(Decimal("0.01")))
        
        # Return on Assets (ROA)
        if total_assets > 0:
            ratios["return_on_assets"] = str(((net_income / total_assets) * 100).quantize(Decimal("0.01")))
        
        # Return on Equity (ROE)
        if total_equity > 0:
            ratios["return_on_equity"] = str(((net_income / total_equity) * 100).quantize(Decimal("0.01")))
        
        return ratios
    
    def calculate_leverage_ratios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate leverage/solvency ratios."""
        total_debt = Decimal(str(data.get("total_debt", 0)))
        total_assets = Decimal(str(data.get("total_assets", 0)))
        total_equity = Decimal(str(data.get("total_equity", 0)))
        ebit = Decimal(str(data.get("ebit", 0)))
        interest_expense = Decimal(str(data.get("interest_expense", 0)))
        
        ratios = {}
        
        # Debt-to-Assets Ratio
        if total_assets > 0:
            ratios["debt_to_assets"] = str((total_debt / total_assets).quantize(Decimal("0.01")))
        
        # Debt-to-Equity Ratio
        if total_equity > 0:
            ratios["debt_to_equity"] = str((total_debt / total_equity).quantize(Decimal("0.01")))
        
        # Interest Coverage Ratio
        if interest_expense > 0:
            ratios["interest_coverage"] = str((ebit / interest_expense).quantize(Decimal("0.01")))
        
        return ratios
    
    def calculate_efficiency_ratios(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate efficiency/activity ratios."""
        revenue = Decimal(str(data.get("revenue", 0)))
        total_assets = Decimal(str(data.get("total_assets", 0)))
        accounts_receivable = Decimal(str(data.get("accounts_receivable", 0)))
        inventory = Decimal(str(data.get("inventory", 0)))
        cogs = Decimal(str(data.get("cost_of_goods_sold", 0)))
        
        ratios = {}
        
        # Asset Turnover
        if total_assets > 0:
            ratios["asset_turnover"] = str((revenue / total_assets).quantize(Decimal("0.01")))
        
        # Receivables Turnover
        if accounts_receivable > 0:
            ratios["receivables_turnover"] = str((revenue / accounts_receivable).quantize(Decimal("0.01")))
            # Days Sales Outstanding
            ratios["days_sales_outstanding"] = str((Decimal("365") / (revenue / accounts_receivable)).quantize(Decimal("0.01")))
        
        # Inventory Turnover
        if inventory > 0 and cogs > 0:
            ratios["inventory_turnover"] = str((cogs / inventory).quantize(Decimal("0.01")))
            # Days Inventory Outstanding
            ratios["days_inventory_outstanding"] = str((Decimal("365") / (cogs / inventory)).quantize(Decimal("0.01")))
        
        return ratios
