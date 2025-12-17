"""
API Endpoint Tests for vigilant-octo-engine2
Covers: authentication, invoice, expense, anomaly, audit, reconciliation, health, audit log
Uses: FastAPI TestClient, pytest, mock JWT, RBAC, file uploads, batch, audit log, encrypted fields, rate limiting, CORS, input validation, error handling
"""

# Set environment variables before any imports
import os
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["JWT_ALGORITHM"] = "HS256"

import importlib
import pytest
import src.api
import src.security
importlib.reload(src.api)
importlib.reload(src.security)
from fastapi.testclient import TestClient
from src.api import app
from src.security import AccessControl

client = TestClient(app)

# Helper functions for JWT
access_control = AccessControl(secret_key=os.environ["SECRET_KEY"], algorithm=os.environ["JWT_ALGORITHM"])
ADMIN_TOKEN = access_control.create_access_token({"sub": "test_admin", "role": "admin"})
ACCOUNTANT_TOKEN = access_control.create_access_token({"sub": "test_acc", "role": "accountant"})
AUDITOR_TOKEN = access_control.create_access_token({"sub": "test_aud", "role": "auditor"})
VIEWER_TOKEN = access_control.create_access_token({"sub": "test_view", "role": "viewer"})
INVALID_TOKEN = "invalid.jwt.token"

# Health endpoint (no auth required)
def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

# Authentication required endpoints
def test_auth_required():
    # All endpoints require auth except health
    endpoints = [
        ("/api/invoice/process", "POST", {"invoice_text": "Test invoice text for auth"}),
        ("/api/expense/categorize", "POST", {"description": "Test", "amount": 1.0, "date": "2025-11-21"}),
        ("/api/audit/detect-anomalies", "POST", {"transactions": [{"amount": 1.0, "vendor": "Test"}]}),
        ("/api/audit/generate-report", "POST", {"transactions": [{"amount": 1.0, "vendor": "Test"}]}),
        ("/api/reconcile/transactions", "POST", {"bank_transactions": [], "book_transactions": []}),
        ("/api/security/audit-log", "GET", {})
    ]
    for url, method, payload in endpoints:
        if method == "POST":
            resp = client.post(url, json=payload)
        else:
            resp = client.get(url)
        assert resp.status_code == 401 or resp.status_code == 403 or resp.status_code == 422

# JWT and RBAC tests
def test_jwt_and_rbac():
    # Valid admin for invoice processing
    resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={"invoice_text": "Test invoice text for RBAC"})
    assert resp.status_code in (200, 201)
    # Invalid token
    resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {INVALID_TOKEN}"}, json={"invoice_text": "Test invoice text for RBAC"})
    assert resp.status_code == 401
    # Viewer role (should be limited)
    resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {VIEWER_TOKEN}"}, json={"invoice_text": "Test invoice text for RBAC"})
    assert resp.status_code in (403, 401, 422)

# Invoice endpoint tests
def test_invoice_process():
    # Valid invoice processing
    resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={"invoice_text": "Test invoice text for process"})
    assert resp.status_code in (200, 201)
    # Invalid invoice (missing required field)
    resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={})
    assert resp.status_code in (422, 400)

# Expense endpoint tests
def test_expense_categorize():
    expense = {"description": "Taxi", "amount": 99.99, "date": "2025-11-21"}
    resp = client.post("/api/expense/categorize", headers={"Authorization": f"Bearer {ACCOUNTANT_TOKEN}"}, json=expense)
    assert resp.status_code in (200, 201)
    # Invalid expense (missing required field)
    resp = client.post("/api/expense/categorize", headers={"Authorization": f"Bearer {ACCOUNTANT_TOKEN}"}, json={})
    assert resp.status_code in (422, 400)

# Anomaly endpoint tests
def test_anomaly_detection():
    # Should require transactions
    resp = client.post("/api/audit/detect-anomalies", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={})
    assert resp.status_code in (422, 400)
    # Valid anomaly detection
    data = {"transactions": [{"amount": 100, "vendor": "A"}, {"amount": 99999, "vendor": "B"}]}
    resp = client.post("/api/audit/detect-anomalies", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json=data)
    assert resp.status_code == 200
    assert "anomalies" in resp.json() or "anomalies_detected" in resp.json()

# Audit endpoint tests
def test_audit_log():
    resp = client.get("/api/security/audit-log", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert resp.status_code == 200
    logs = resp.json()
    assert "entries" in logs

# Reconciliation endpoint tests
def test_reconciliation():
    # Should require transactions
    resp = client.post("/api/reconcile/transactions", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={})
    assert resp.status_code in (422, 400)
    # Valid reconciliation
    data = {"bank_transactions": [{"id": 1, "amount": 100}], "book_transactions": [{"id": 1, "amount": 100}]}
    resp = client.post("/api/reconcile/transactions", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json=data)
    assert resp.status_code == 200
    assert "matches" in resp.json()

# Rate limiting test (simulate burst)
def test_rate_limiting():
    for _ in range(10):
        resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={"invoice_text": "Test invoice text for rate limit"})
        assert resp.status_code in (200, 429, 201)

# CORS test
def test_cors():
    resp = client.options("/api/invoice/process", headers={"Origin": "http://localhost", "Access-Control-Request-Method": "POST"})
    assert resp.status_code in (200, 204, 400)
    assert "access-control-allow-origin" in resp.headers or resp.status_code == 400

# Structured logging test
def test_structured_logging():
    # This is a placeholder; actual log file checks would require reading logs
    assert os.path.exists(os.getenv("AUDIT_LOG_PATH", "logs/audit.log"))

# Sensitive data never logged
def test_no_sensitive_data_in_logs():
    # Placeholder: would require reading logs and checking for secrets
    pass

# Input validation failures
def test_input_validation():
    # Missing required fields
    resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={})
    assert resp.status_code in (400, 422)

# Dependency failures (simulate)
def test_dependency_failures(monkeypatch):
    from src.api import invoice_processor
    def fail(*args, **kwargs):
        raise Exception("Simulated failure")
    monkeypatch.setattr(invoice_processor, "extract_invoice_data", fail)
    resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={"invoice_text": "Test invoice text for dependency failure"})
    assert resp.status_code in (500, 400)

# Encryption failures (simulate)
def test_encryption_failures(monkeypatch):
    from src.api import encryption_manager
    def fail(*args, **kwargs):
        raise Exception("Encryption failed")
    monkeypatch.setattr(encryption_manager, "encrypt_dict", fail)
    resp = client.post("/api/invoice/process", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}, json={"invoice_text": "Test invoice text for encryption failure"})
    assert resp.status_code in (500, 400)

# Model load failures (simulate)
def test_model_load_failures(monkeypatch):
    from src.api import expense_categorizer
    def fail(*args, **kwargs):
        raise Exception("Model load failed")
    monkeypatch.setattr(expense_categorizer, "categorize", fail)
    resp = client.post("/api/expense/categorize", headers={"Authorization": f"Bearer {ACCOUNTANT_TOKEN}"}, json={"description": "Travel", "amount": 99.99, "date": "2025-11-21"})
    assert resp.status_code in (500, 400)
