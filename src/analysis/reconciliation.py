"""
Enhanced Bank Reconciliation

Advanced reconciliation with fuzzy matching and AI-assisted suggestions.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from src.audit_logging import AuditLogger, AuditEventType


class EnhancedReconciliation:
    """Enhanced bank reconciliation with fuzzy matching."""
    
    def __init__(
        self,
        amount_tolerance: Optional[Decimal] = None,
        date_tolerance_days: int = 3,
        description_match_threshold: float = 0.8,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize reconciliation engine.
        
        Args:
            amount_tolerance: Amount matching tolerance (default: 0.01)
            date_tolerance_days: Days tolerance for date matching
            description_match_threshold: Minimum similarity score for description matching (0-1)
            audit_logger: Audit logger
        """
        self.amount_tolerance = amount_tolerance or Decimal("0.01")
        self.date_tolerance_days = date_tolerance_days
        self.description_match_threshold = description_match_threshold
        self.audit_logger = audit_logger or AuditLogger()
    
    def fuzzy_match_description(self, desc1: str, desc2: str) -> float:
        """
        Calculate fuzzy match score between two descriptions.
        
        Args:
            desc1: First description
            desc2: Second description
        
        Returns:
            Similarity score (0-1)
        """
        return SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
    
    def reconcile_transactions(
        self,
        bank_transactions: List[Dict[str, Any]],
        book_transactions: List[Dict[str, Any]],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Reconcile bank and book transactions with fuzzy matching.
        
        Args:
            bank_transactions: List of bank transactions
            book_transactions: List of book transactions
            user_id: User ID for audit logging
        
        Returns:
            Reconciliation results with matches and discrepancies
        """
        matches = []
        unmatched_bank = []
        unmatched_book = list(book_transactions)  # Start with all book transactions
        
        for bank_txn in bank_transactions:
            bank_amount = Decimal(str(bank_txn.get("amount", 0)))
            bank_date = datetime.fromisoformat(bank_txn.get("date", ""))
            bank_desc = bank_txn.get("description", "")
            
            best_match = None
            best_score = 0.0
            
            for book_txn in unmatched_book:
                book_amount = Decimal(str(book_txn.get("amount", 0)))
                book_date = datetime.fromisoformat(book_txn.get("date", ""))
                book_desc = book_txn.get("description", "")
                
                # Check amount match
                amount_diff = abs(bank_amount - book_amount)
                if amount_diff > self.amount_tolerance:
                    continue
                
                # Check date match
                date_diff = abs((bank_date - book_date).days)
                if date_diff > self.date_tolerance_days:
                    continue
                
                # Check description match
                desc_score = self.fuzzy_match_description(bank_desc, book_desc)
                
                # Calculate overall match score
                match_score = desc_score * 0.6 + (1 - min(amount_diff / self.amount_tolerance, 1)) * 0.3 + (1 - min(date_diff / self.date_tolerance_days, 1)) * 0.1
                
                if match_score > best_score and desc_score >= self.description_match_threshold:
                    best_score = match_score
                    best_match = book_txn
            
            if best_match:
                matches.append({
                    "bank_transaction": bank_txn,
                    "book_transaction": best_match,
                    "match_score": round(best_score, 2),
                    "match_type": "fuzzy" if best_score < 1.0 else "exact"
                })
                unmatched_book.remove(best_match)
            else:
                unmatched_bank.append(bank_txn)
        
        # Calculate reconciliation summary
        total_bank = sum(Decimal(str(t.get("amount", 0))) for t in bank_transactions)
        total_book = sum(Decimal(str(t.get("amount", 0))) for t in book_transactions)
        total_matched = sum(Decimal(str(m["bank_transaction"].get("amount", 0))) for m in matches)
        
        result = {
            "status": "reconciled" if len(unmatched_bank) == 0 and len(unmatched_book) == 0 else "discrepancies",
            "total_transactions": {
                "bank": len(bank_transactions),
                "book": len(book_transactions)
            },
            "matched": {
                "count": len(matches),
                "amount": str(total_matched)
            },
            "unmatched_bank": {
                "count": len(unmatched_bank),
                "transactions": unmatched_bank[:10]  # Limit to first 10
            },
            "unmatched_book": {
                "count": len(unmatched_book),
                "transactions": unmatched_book[:10]  # Limit to first 10
            },
            "summary": {
                "total_bank_amount": str(total_bank),
                "total_book_amount": str(total_book),
                "difference": str(total_bank - total_book)
            }
        }
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="reconcile_transactions",
            resource="reconciliation",
            status="success" if result["status"] == "reconciled" else "warning",
            details={
                "matched": len(matches),
                "unmatched_bank": len(unmatched_bank),
                "unmatched_book": len(unmatched_book)
            }
        )
        
        return result
    
    def suggest_matches(
        self,
        unmatched_transaction: Dict[str, Any],
        potential_matches: List[Dict[str, Any]],
        user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """
        Suggest potential matches for an unmatched transaction.
        
        Args:
            unmatched_transaction: Transaction to match
            potential_matches: List of potential matching transactions
            user_id: User ID for audit logging
        
        Returns:
            List of suggested matches with scores
        """
        txn_amount = Decimal(str(unmatched_transaction.get("amount", 0)))
        txn_date = datetime.fromisoformat(unmatched_transaction.get("date", ""))
        txn_desc = unmatched_transaction.get("description", "")
        
        suggestions = []
        
        for potential in potential_matches:
            pot_amount = Decimal(str(potential.get("amount", 0)))
            pot_date = datetime.fromisoformat(potential.get("date", ""))
            pot_desc = potential.get("description", "")
            
            # Calculate scores
            amount_score = 1 - min(abs(txn_amount - pot_amount) / max(txn_amount, pot_amount), 1)
            date_score = 1 - min(abs((txn_date - pot_date).days) / 30, 1)
            desc_score = self.fuzzy_match_description(txn_desc, pot_desc)
            
            overall_score = desc_score * 0.5 + amount_score * 0.3 + date_score * 0.2
            
            if overall_score >= 0.5:  # Only suggest matches with reasonable confidence
                suggestions.append({
                    "transaction": potential,
                    "confidence": round(overall_score, 2),
                    "scores": {
                        "description": round(desc_score, 2),
                        "amount": round(amount_score, 2),
                        "date": round(date_score, 2)
                    }
                })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            action="suggest_transaction_matches",
            resource="reconciliation",
            status="success",
            details={"suggestions": len(suggestions)}
        )
        
        return suggestions[:5]  # Return top 5 suggestions
