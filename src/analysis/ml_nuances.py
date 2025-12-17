"""
Financial Pattern Recognition

ML models for detecting financial patterns and anomalies.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from src.audit_logging import AuditLogger, AuditEventType


class FinancialPatternRecognizer:
    """ML-based financial pattern recognition."""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """Initialize pattern recognizer."""
        self.audit_logger = audit_logger or AuditLogger()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
    
    def detect_patterns(
        self,
        transactions: List[Dict[str, Any]],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Detect financial patterns in transactions.
        
        Args:
            transactions: List of transaction dictionaries
            user_id: User ID for audit logging
        
        Returns:
            Detected patterns and insights
        """
        df = pd.DataFrame(transactions)
        
        if df.empty or 'amount' not in df.columns:
            return {"patterns": [], "insights": []}
        
        patterns = []
        insights = []
        
        # Detect seasonality
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.month
            monthly_avg = df.groupby('month')['amount'].mean()
            
            # High variance months
            high_months = monthly_avg[monthly_avg > monthly_avg.mean() * 1.5]
            if not high_months.empty:
                patterns.append({
                    "type": "seasonality",
                    "description": "Higher transaction volumes detected in specific months",
                    "months": high_months.index.tolist()
                })
        
        # Detect transaction clustering
        amounts = df['amount'].values
        if len(amounts) > 10:
            # Find common transaction amounts
            rounded = (amounts / 100).astype(int) * 100
            common_amounts = pd.Series(rounded).value_counts().head(5)
            
            patterns.append({
                "type": "common_amounts",
                "description": "Frequently recurring transaction amounts",
                "amounts": common_amounts.index.tolist()
            })
        
        # Spending trend analysis
        if 'date' in df.columns and len(df) > 30:
            df = df.sort_values('date')
            df['rolling_avg'] = df['amount'].rolling(window=7).mean()
            
            recent_avg = df['rolling_avg'].tail(7).mean()
            overall_avg = df['rolling_avg'].mean()
            
            if recent_avg > overall_avg * 1.2:
                insights.append({
                    "type": "increasing_trend",
                    "message": "Transaction amounts trending upward",
                    "increase_pct": f"{((recent_avg / overall_avg - 1) * 100):.1f}%"
                })
            elif recent_avg < overall_avg * 0.8:
                insights.append({
                    "type": "decreasing_trend",
                    "message": "Transaction amounts trending downward",
                    "decrease_pct": f"{((1 - recent_avg / overall_avg) * 100):.1f}%"
                })
        
        result = {
            "patterns": patterns,
            "insights": insights,
            "transaction_count": len(df)
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="detect_financial_patterns",
            resource="pattern_recognition",
            status="success",
            details={"patterns": len(patterns), "insights": len(insights)}
        )
        
        return result
    
    def predict_category(
        self,
        description: str,
        amount: float,
        historical_data: List[Dict[str, Any]],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Predict transaction category using ML.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            historical_data: Historical transaction data for training
            user_id: User ID for audit logging
        
        Returns:
            Predicted category and confidence
        """
        # Simplified ML prediction (in production, use more sophisticated model)
        df = pd.DataFrame(historical_data)
        
        if df.empty or 'category' not in df.columns:
            return {"category": "Unknown", "confidence": 0.0}
        
        # Find similar transactions
        similar = df[df['description'].str.contains(description[:10], case=False, na=False)]
        
        if not similar.empty:
            category = similar['category'].mode()[0]
            confidence = len(similar) / len(df)
            
            return {
                "category": category,
                "confidence": min(confidence, 1.0),
                "method": "pattern_matching"
            }
        
        # Fallback to most common category
        return {
            "category": df['category'].mode()[0] if not df.empty else "Unknown",
            "confidence": 0.5,
            "method": "fallback"
        }
