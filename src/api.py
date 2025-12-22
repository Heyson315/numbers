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
from src.integrations.quickbooks_routes import qb_router
from src.integrations import M365_AVAILABLE, m365_router

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

# Include QuickBooks routes
app.include_router(qb_router, prefix="/api")

# Include Microsoft 365 routes (SharePoint, OneDrive, Power BI, Power Automate)
if M365_AVAILABLE and m365_router:
    app.include_router(m365_router, prefix="/api")

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


# Run server
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="./certs/key.pem",  # Add SSL certificates in production
        ssl_certfile="./certs/cert.pem"
    )
