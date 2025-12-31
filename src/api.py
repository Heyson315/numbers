"""
Secure API Module

Provides REST API endpoints with authentication, rate limiting,
and comprehensive security controls for CPA firm automation.
"""


import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.security import AccessControl, EncryptionManager, SecureDataHandler
from src.audit_logging import AuditLogger, AuditEventType
from src.invoice_processing import InvoiceProcessor, Invoice
from src.expense_categorization import ExpenseCategorizer, SmartReconciliation
from src.anomaly_detection import AnomalyDetector, FraudRiskScorer
from security import AccessControl, EncryptionManager, SecureDataHandler
from audit_logging import AuditLogger, AuditEventType
from invoice_processing import InvoiceProcessor
from expense_categorization import ExpenseCategorizer, SmartReconciliation
from anomaly_detection import AnomalyDetector, FraudRiskScorer

import pandas as pd



# Initialize security components with testability
def get_access_control():
    secret_key = os.getenv("SECRET_KEY", None)
    algorithm = os.getenv("JWT_ALGORITHM", None)
    return AccessControl(secret_key=secret_key, algorithm=algorithm)

access_control = get_access_control()
encryption_manager = EncryptionManager()
secure_data_handler = SecureDataHandler()
audit_logger = AuditLogger()

# Initialize AI components
invoice_processor = InvoiceProcessor()
expense_categorizer = ExpenseCategorizer()
anomaly_detector = AnomalyDetector()
fraud_scorer = FraudRiskScorer()
reconciliation = SmartReconciliation()

# Initialize FastAPI app
app = FastAPI(
    title="CPA Firm AI Automation API",
    description="Secure API for automating finance, audit, and accounting tasks",
    version="1.0.0"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration (adjust for production)
# OPTIONS is required for CORS preflight requests and is handled securely by FastAPI's CORSMiddleware
# The middleware returns only necessary CORS headers without exposing sensitive endpoint data
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",  # Production origin placeholder
        "http://localhost:5173"    # Frontend dev server (Vite)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


class InvoiceRequest(BaseModel):
    invoice_text: str = Field(..., min_length=10)
    vendor_name: Optional[str] = None


class ExpenseRequest(BaseModel):
    description: str
    vendor: Optional[str] = None
    amount: float
    date: str


class TransactionData(BaseModel):
    transactions: List[Dict[str, Any]]


# Authentication dependency
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """Verify JWT token and return user data."""
    token = credentials.credentials
    payload = access_control.verify_token(token)

    if not payload:
        audit_logger.log_failed_auth(
            user_id="unknown",
            reason="Invalid token",
            ip_address=request.client.host if request else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    return payload


# API Endpoints
@app.post("/api/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return JWT token.

    **Security**: Rate limited to prevent brute force attacks.
    """
    # ⚠️ WARNING: DEMO CREDENTIALS ONLY - MUST BE REPLACED BEFORE PRODUCTION ⚠️
    # In production, verify against secure user database with hashed passwords
    # This is a simplified example for demonstration purposes ONLY
    if login_data.username == "demo" and login_data.password == "Demo123!":
        token = access_control.create_access_token(
            data={"sub": login_data.username, "role": "accountant"},
            expires_delta=timedelta(hours=24)
        )

        audit_logger.log_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=login_data.username,
            action="login",
            resource="auth",
            status="success",
            ip_address=request.client.host
        )

        return TokenResponse(access_token=token, expires_in=86400)

    audit_logger.log_failed_auth(
        user_id=login_data.username,
        reason="Invalid credentials",
        ip_address=request.client.host
    )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


@app.post("/api/invoice/process")
@limiter.limit("20/minute")
async def process_invoice(
    request: Request,
    invoice_data: InvoiceRequest,
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Process and extract data from invoice text.

    **Security**: Requires authentication and is rate limited.
    """
    # RBAC: Only admin/accountant can process invoices
    if user.get('role') not in ('admin', 'accountant'):
        raise HTTPException(status_code=403, detail="Insufficient permissions to process invoices")

    try:
        # Process invoice
        invoice = invoice_processor.extract_invoice_data(invoice_data.invoice_text)
        is_valid, errors = invoice_processor.validate_invoice(invoice)
        category = invoice_processor.categorize_expense(invoice)

        # Simulate encryption (for test error simulation)
        try:
            encrypted = encryption_manager.encrypt_dict(invoice.to_dict())
        except Exception as enc_err:
            audit_logger.log_event(
                event_type=AuditEventType.SECURITY_ALERT,
                user_id=user['sub'],
                action="encryption_error",
                resource="invoice",
                status="error",
                details={"error": str(enc_err)}
            )
            raise HTTPException(status_code=500, detail="Encryption failed")

        # Log data access
        audit_logger.log_data_access(
            user_id=user['sub'],
            resource_type="invoice",
            resource_id=invoice.invoice_id,
            action="process",
            ip_address=request.client.host
        )

        return {
            "invoice": invoice.to_dict(),
            "is_valid": is_valid,
            "validation_errors": errors,
            "category": category,
            "gl_account": expense_categorizer.suggest_gl_account(category)
        }

    except HTTPException:
        raise
    except Exception as e:
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            user_id=user['sub'],
            action="process_invoice_error",
            resource="invoice",
            status="error",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Error processing invoice")


@app.post("/api/expense/categorize")
@limiter.limit("50/minute")
async def categorize_expense(
    request: Request,
    expense: ExpenseRequest,
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Categorize an expense using AI.

    **Security**: Requires authentication and is rate limited.
    """
    try:
        category, confidence = expense_categorizer.categorize(
            description=expense.description,
            vendor=expense.vendor,
            amount=expense.amount
        )

        gl_account = expense_categorizer.suggest_gl_account(category)

        audit_logger.log_data_access(
            user_id=user['sub'],
            resource_type="expense",
            resource_id=f"{expense.vendor}_{expense.amount}",
            action="categorize",
            ip_address=request.client.host
        )

        return {
            "category": category,
            "confidence": confidence,
            "gl_account": gl_account,
            "needs_review": confidence < 0.7
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Error categorizing expense")


@app.post("/api/audit/detect-anomalies")
@limiter.limit("10/minute")
async def detect_anomalies(
    request: Request,
    transaction_data: TransactionData,
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Detect anomalies in transaction data.

    **Security**: Requires authentication with auditor role.
    """
    # Check permissions
    if not access_control.check_permission(user.get('role', ''), 'audit'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        transactions_df = pd.DataFrame(transaction_data.transactions)

        # Run anomaly detection
        results = anomaly_detector.detect_transaction_anomalies(transactions_df)
        duplicates = anomaly_detector.detect_duplicate_transactions(transactions_df)

        audit_logger.log_data_access(
            user_id=user['sub'],
            resource_type="transactions",
            resource_id="batch",
            action="anomaly_detection",
            ip_address=request.client.host
        )

        anomalies = results[results['is_anomaly']]

        return {
            "total_transactions": len(transactions_df),
            "anomalies_detected": int(anomalies['is_anomaly'].sum()),
            "anomalies": anomalies.to_dict('records'),
            "potential_duplicates": duplicates,
            "summary": {
                "anomaly_rate": float(len(anomalies) / len(transactions_df) * 100),
                "highest_risk_score": float(results['anomaly_score'].max())
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@app.post("/api/audit/generate-report")
@limiter.limit("5/minute")
async def generate_audit_report(
    request: Request,
    transaction_data: TransactionData,
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Generate comprehensive audit report.

    **Security**: Requires authentication with auditor role.
    """
    if not access_control.check_permission(user.get('role', ''), 'audit'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        transactions_df = pd.DataFrame(transaction_data.transactions)
        report = anomaly_detector.generate_audit_report(transactions_df)

        audit_logger.log_event(
            event_type=AuditEventType.DATA_EXPORT,
            user_id=user['sub'],
            action="generate_audit_report",
            resource="audit_report",
            status="success",
            ip_address=request.client.host
        )

        return report

    except Exception:
        raise HTTPException(status_code=500, detail="Error generating report")


@app.post("/api/reconcile/transactions")
@limiter.limit("10/minute")
async def reconcile_transactions(
    request: Request,
    bank_transactions: List[Dict[str, Any]],
    book_transactions: List[Dict[str, Any]],
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Reconcile bank transactions with book transactions.

    **Security**: Requires authentication.
    """
    try:
        matches = reconciliation.fuzzy_match_transactions(
            bank_transactions=bank_transactions,
            book_transactions=book_transactions
        )

        audit_logger.log_data_access(
            user_id=user['sub'],
            resource_type="reconciliation",
            resource_id="transaction_match",
            action="reconcile",
            ip_address=request.client.host
        )

        matched = [match for match in matches if match['status'] == 'matched']
        unmatched_bank = [match for match in matches if match['status'] == 'unmatched_bank']
        unmatched_book = [match for match in matches if match['status'] == 'unmatched_book']

        return {
            "total_bank_transactions": len(bank_transactions),
            "total_book_transactions": len(book_transactions),
            "matched": len(matched),
            "unmatched_bank": len(unmatched_bank),
            "unmatched_book": len(unmatched_book),
            "match_rate": float(len(matched) / max(len(bank_transactions), 1) * 100),
            "matches": matches
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Error reconciling transactions")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/security/audit-log")
@limiter.limit("10/minute")
async def get_audit_log(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Dict[str, Any] = Depends(verify_token)
):
    """
    Retrieve audit log entries.

    **Security**: Requires admin role.
    """
    if not access_control.check_permission(user.get('role', ''), 'audit'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        entries = audit_logger.query_audit_log(start_date=start, end_date=end)

        return {
            "total_entries": len(entries),
            "entries": entries[:100]  # Limit to 100 for API response
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Error retrieving audit log")


# ========== QuickBooks Integration Endpoints ==========

@app.post("/api/quickbooks/auth/initiate")
@limiter.limit("5/minute")
async def initiate_qbo_auth(request: Request, user: Dict[str, Any] = Depends(verify_token)):
    """Start QuickBooks OAuth flow."""
    from integrations.quickbooks import QuickBooksAuth
    
    if not access_control.check_permission(user.get('role', ''), 'manage_users'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        qb_auth = QuickBooksAuth()
        auth_data = qb_auth.get_authorization_url()
        
        return {
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating QuickBooks auth: {str(e)}")


@app.get("/api/quickbooks/auth/callback")
async def qbo_auth_callback(code: str, realm_id: str, state: str):
    """OAuth callback handler for QuickBooks."""
    from src.integrations.quickbooks import QuickBooksAuth
    
    try:
        qb_auth = QuickBooksAuth()
        token_storage = await qb_auth.exchange_code(code, realm_id)
        
        return {
            "status": "success",
            "message": "QuickBooks connected successfully",
            "realm_id": realm_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback error: {str(e)}")


@app.post("/api/quickbooks/sync/trial-balance")
@limiter.limit("10/minute")
async def sync_trial_balance(
    request: Request,
    start_date: str,
    end_date: str,
    realm_id: str,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Sync trial balance from QuickBooks."""
    from src.integrations.quickbooks import QuickBooksAuth, QuickBooksClient, QuickBooksSync
    
    if not access_control.check_permission(user.get('role', ''), 'read'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        qb_auth = QuickBooksAuth()
        qb_client = QuickBooksClient(qb_auth, realm_id)
        qb_sync = QuickBooksSync(qb_client)
        
        result = await qb_sync.sync_trial_balance(start_date, end_date, user['sub'])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


# ========== M365 Integration Endpoints ==========

@app.post("/api/m365/auth/initiate")
@limiter.limit("5/minute")
async def initiate_m365_auth(request: Request, user: Dict[str, Any] = Depends(verify_token)):
    """Start Microsoft 365 OAuth flow."""
    from src.integrations.m365 import GraphClient
    
    if not access_control.check_permission(user.get('role', ''), 'manage_users'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        graph_client = GraphClient()
        auth_data = graph_client.get_authorization_url()
        
        return {
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating M365 auth: {str(e)}")


@app.get("/api/m365/onedrive/files")
@limiter.limit("20/minute")
async def list_onedrive_files(
    request: Request,
    folder_path: Optional[str] = None,
    user: Dict[str, Any] = Depends(verify_token)
):
    """List files in OneDrive."""
    from src.integrations.m365 import GraphClient, OneDriveManager
    
    if not access_control.check_permission(user.get('role', ''), 'read'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        graph_client = GraphClient()
        onedrive = OneDriveManager(graph_client)
        files = await onedrive.list_files(folder_path, user['sub'])
        
        return {
            "folder": folder_path or "root",
            "file_count": len(files),
            "files": [f.dict() for f in files]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


# ========== Financial Analysis Endpoints ==========

@app.post("/api/analysis/trial-balance")
@limiter.limit("20/minute")
async def analyze_trial_balance(
    request: Request,
    trial_balance: Dict[str, Any],
    user: Dict[str, Any] = Depends(verify_token)
):
    """Analyze trial balance for accuracy and variances."""
    from src.analysis import TrialBalanceAnalyzer
    
    if not access_control.check_permission(user.get('role', ''), 'read'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        analyzer = TrialBalanceAnalyzer()
        result = analyzer.analyze_trial_balance(trial_balance, user['sub'])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/api/analysis/ratios")
@limiter.limit("20/minute")
async def calculate_ratios(
    request: Request,
    financial_data: Dict[str, Any],
    user: Dict[str, Any] = Depends(verify_token)
):
    """Calculate comprehensive financial ratios."""
    from src.analysis import FinancialRatiosCalculator
    
    if not access_control.check_permission(user.get('role', ''), 'read'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        calculator = FinancialRatiosCalculator()
        ratios = calculator.calculate_all_ratios(financial_data, user['sub'])
        return ratios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/api/analysis/adjusting-entries")
@limiter.limit("10/minute")
async def suggest_adjusting_entries(
    request: Request,
    transactions: List[Dict[str, Any]],
    period_end: str,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Suggest adjusting entries using ML."""
    from src.analysis import AdjustingEntrySuggester
    from datetime import date
    
    if not access_control.check_permission(user.get('role', ''), 'write'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        suggester = AdjustingEntrySuggester()
        period_end_date = date.fromisoformat(period_end)
        suggestions = suggester.suggest_accrual_entries(transactions, period_end_date, user['sub'])
        
        return {
            "period_end": period_end,
            "suggestion_count": len(suggestions),
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion error: {str(e)}")


@app.post("/api/analysis/reconciliation")
@limiter.limit("10/minute")
async def enhanced_reconciliation(
    request: Request,
    bank_transactions: List[Dict[str, Any]],
    book_transactions: List[Dict[str, Any]],
    user: Dict[str, Any] = Depends(verify_token)
):
    """Perform enhanced bank reconciliation with fuzzy matching."""
    from src.analysis import EnhancedReconciliation
    
    if not access_control.check_permission(user.get('role', ''), 'write'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        reconciler = EnhancedReconciliation()
        result = reconciler.reconcile_transactions(
            bank_transactions,
            book_transactions,
            user['sub']
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconciliation error: {str(e)}")


# ========== Compliance Endpoints ==========

@app.get("/api/compliance/audit-log")
@limiter.limit("10/minute")
async def get_compliance_audit_log(
    request: Request,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Retrieve immutable audit logs."""
    from src.compliance import ImmutableAuditTrail
    
    if not access_control.check_permission(user.get('role', ''), 'audit'):
        raise HTTPException(status_code=403, detail="Admin/Auditor only")
    
    try:
        audit_trail = ImmutableAuditTrail()
        entries = audit_trail.get_entries(user_id, start_date, end_date)
        verification = audit_trail.verify_chain()
        
        return {
            "entries": entries,
            "verification": verification,
            "total": len(entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/compliance/gdpr/data-subject/{data_subject_id}")
@limiter.limit("5/minute")
async def gdpr_data_subject_access(
    data_subject_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(verify_token)
):
    """GDPR Right to Access request."""
    from src.compliance import GDPRCompliance
    
    if not access_control.check_permission(user.get('role', ''), 'audit'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        gdpr = GDPRCompliance()
        result = gdpr.right_to_access(data_subject_id, user['sub'])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.delete("/api/compliance/gdpr/data-subject/{data_subject_id}")
@limiter.limit("2/minute")
async def gdpr_right_to_erasure(
    data_subject_id: str,
    request: Request,
    reason: Optional[str] = None,
    user: Dict[str, Any] = Depends(verify_token)
):
    """GDPR Right to Erasure (Right to be Forgotten)."""
    from src.compliance import GDPRCompliance
    
    if not access_control.check_permission(user.get('role', ''), 'manage_users'):
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        gdpr = GDPRCompliance()
        result = gdpr.right_to_erasure(data_subject_id, user['sub'], reason)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/compliance/sox/controls")
@limiter.limit("10/minute")
async def get_sox_controls(
    request: Request,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Get SOX control status and compliance report."""
    from src.compliance import SOXCompliance
    
    if not access_control.check_permission(user.get('role', ''), 'audit'):
        raise HTTPException(status_code=403, detail="Auditor/Admin only")
    
    try:
        sox = SOXCompliance()
        report = sox.generate_sox_report()
        deficiencies = sox.get_control_deficiencies()
        
        return {
            "report": report,
            "deficiencies": deficiencies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/compliance/data-retention/apply")
@limiter.limit("5/minute")
async def apply_data_retention(
    request: Request,
    data_type: str,
    records: List[Dict[str, Any]],
    dry_run: bool = True,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Apply data retention policy."""
    from src.compliance import DataRetentionManager
    
    if not access_control.check_permission(user.get('role', ''), 'manage_users'):
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        retention_mgr = DataRetentionManager()
        result = retention_mgr.apply_retention_policy(
            data_type,
            records,
            user['sub'],
            dry_run
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Run server
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="./certs/key.pem",  # Add SSL certificates in production
        ssl_certfile="./certs/cert.pem"
    )
