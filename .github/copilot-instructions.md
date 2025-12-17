
# Copilot Instructions for vigilant-octo-engine

## Project Overview
- **Purpose**: Automate CPA firm workflows (invoice processing, expense categorization, audit logging, anomaly detection, reconciliation) with AI/ML and enterprise security.
- **Architecture**: Monorepo with Python FastAPI backend (`src/`) + React TypeScript frontend (`frontend/`)
- **Tech Stack**: 
  - Backend: Python 3.8+, FastAPI, scikit-learn, pandas, cryptography, JWT, pytest
  - Frontend: React 18, TypeScript, Vite, React Router, Vitest
- **Key Directories**:
  - `src/`: Core Python modules (API, security, audit, invoice, expense, anomaly detection)
  - `frontend/src/`: React app with pages, services, hooks, components
  - `tests/`: Backend pytest suite (22+ tests)
  - `logs/`, `models/`, `secure_data/`: Runtime data (git-ignored)

## Architecture & Data Flow
- **API Layer**: `src/api.py` exposes 8 REST endpoints under `/api/*`, all protected by JWT (except health check). Each endpoint enforces rate limiting (5-100 req/min), logs to audit trail, and validates input via Pydantic models.
- **Security Layer**: `src/security.py` provides three core classes:
  - `EncryptionManager`: AES-256 + PBKDF2 for encrypting dicts/strings before storage
  - `AccessControl`: JWT creation/validation, password hashing (bcrypt), RBAC (admin, accountant, auditor, viewer)
  - `SecureDataHandler`: File encryption/decryption for sensitive uploads
- **Audit Layer**: `src/audit_logging.py` logs 13 event types (AuditEventType enum) as structured JSON. Use `audit_logger.log_event(event_type=AuditEventType.X, user_id=..., details=...)` for all sensitive operations.
- **AI/ML Modules**:
  - `InvoiceProcessor` (src/invoice_processing.py): Extract invoice data via regex/NLP, validate completeness, categorize expenses, batch process
  - `ExpenseCategorizer` (src/expense_categorization.py): TF-IDF + Naive Bayes for 14-category classification, GL mapping, tax deductibility
  - `AnomalyDetector`, `FraudRiskScorer` (src/anomaly_detection.py): Isolation Forest, Benford's Law, duplicate/round-number detection
  - `SmartReconciliation` (src/expense_categorization.py): Fuzzy matching for bank/book transactions
- **Frontend**: React SPA with `AuthContext` for JWT token management, `apiClient.ts` for typed API calls, `ProtectedRoute` for auth guard. All services (`invoiceService.ts`, etc.) consume backend API.

## Security & Compliance (Critical)
- **Encryption Flow**: Always encrypt before storage: `encrypted = encryption_manager.encrypt_dict({"field": value})` → store → retrieve → `decrypted = encryption_manager.decrypt_dict(encrypted)`. Encrypted data lives in `secure_data/`.
- **API Authentication**: 
  - All endpoints except `/api/health` require `Authorization: Bearer <jwt>` header
  - Create tokens: `access_control.create_access_token(user_id=..., role=...)` (24h expiry)
  - Validate: `verify_token(credentials: HTTPAuthorizationCredentials)` dependency in `src/api.py`
  - Demo credentials in code: `demo`/`demo123` (viewer), `admin`/`admin123` (admin), `accountant`/`acc123` (accountant), `auditor`/`aud123` (auditor)
- **Role-Based Access**: Check permissions via `access_control.check_permission(token, required_permission)`. Roles: admin (all), accountant (read/write/audit), auditor (read/audit), viewer (read only).
- **Audit Logging**: Log every sensitive operation using `audit_logger.log_event(event_type=AuditEventType.X, user_id=..., resource=..., action=..., details=...)`. 13 event types in `AuditEventType` enum (USER_LOGIN, DATA_ACCESS, DATA_MODIFY, SECURITY_ALERT, etc.).
- **Rate Limiting**: Enforced via `@limiter.limit("X/minute")` decorator. Limits: login (5/min), data processing (20/min), reads (100/min).
- **Input Validation**: All API endpoints use Pydantic models (e.g., `InvoiceRequest`, `ExpenseRequest`). Add validation with `Field(..., min_length=X, max_length=Y)`.
- **Environment Secrets**: Never commit `.env`. Use `.env.example` template. Production requires strong `SECRET_KEY` and `ENCRYPTION_KEY` (generate via `Fernet.generate_key()`).
- **Compliance**: SOX, GDPR, IRS-ready. Audit logs retained 365+ days (`AUDIT_LOG_RETENTION_DAYS`). See `docs/SECURITY.md` for full checklist.

## Developer Workflows
- **Setup**: 
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1  # Windows PowerShell
  pip install -r requirements.txt
  cp .env.example .env  # Edit with your values
  mkdir logs, models, secure_data -Force
  ```
- **Run Backend**: `python src/api.py` → http://localhost:8000 (FastAPI + Uvicorn)
- **Run Frontend**: `cd frontend; npm install; npm run dev` → http://localhost:5173 (Vite)
- **Testing**: 
  - All tests: `pytest tests/ -v` (22 tests, 100% pass rate)
  - Single module: `pytest tests/test_security.py -v`
  - Coverage: `pytest tests/ --cov=src --cov-report=html` → `htmlcov/index.html`
- **Code Quality**:
  - Lint: `bandit -r src/` (security), `flake8 src/` (style)
  - Security scan: `safety check`, `pip-audit`
  - Format: `black src/ tests/` (auto-format)
- **Frontend Testing**: `cd frontend; npm test` (Vitest), `npm run test:coverage`
- **Environment**: All secrets via `.env`. Never log `SECRET_KEY`, `ENCRYPTION_KEY`, or JWT tokens. Use `python-json-logger` for structured logs.

## Project Conventions
- **Imports**: Always use absolute imports from `src.` (e.g., `from src.security import EncryptionManager`)
- **Logging**: Use `python-json-logger` for structured logs. Never log secrets, passwords, tokens, or PII. Log format: `{"timestamp": "...", "level": "INFO", "message": "...", "user_id": "..."}`.
- **Testing**: 
  - Place tests in `tests/test_<module>.py` matching `src/<module>.py`
  - Use descriptive names: `test_encrypt_decrypt_data`, `test_validate_invoice`
  - All new features require tests (maintain 100% pass rate)
- **API Patterns**:
  - All authenticated endpoints use `credentials: HTTPAuthorizationCredentials = Depends(security)` + `verify_token(credentials)`
  - Rate limit: `@limiter.limit("20/minute")` decorator before endpoint
  - Audit log: `audit_logger.log_event(event_type=AuditEventType.API_CALL, user_id=user_id, resource="endpoint_name", details={...})`
  - Example endpoint structure:
    ```python
    @app.post("/api/resource/action")
    @limiter.limit("20/minute")
    async def resource_action(
        request: Request,
        data: ResourceRequest,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        user_id = verify_token(credentials)
        audit_logger.log_event(event_type=AuditEventType.API_CALL, user_id=user_id, resource="resource_action", details=data.dict())
        # ... implementation
        return {"result": ...}
    ```
- **Frontend Patterns**:
  - Use `useAuth()` hook for token/role access: `const { token, role } = useAuth();`
  - API calls via services: `invoiceService.process(data, token)` (never call `apiClient` directly from components)
  - Protected routes: Wrap in `<ProtectedRoute><YourPage /></ProtectedRoute>`
  - Type imports from `types.ts` for API contracts

## Integration & Extensibility
- **External APIs**: Integrate new endpoints in `src/api.py` and document in README.
- **Models**: Place new ML models in `models/` and load via `src/` modules.
- **Config**: Add new env vars to `.env.example` and document in README.

## Examples & References

## Documentation & Support
- **Quick Reference**: See `QUICK_REFERENCE.md` for commands and workflow.
- **API Docs**: `docs/API_INTEGRATION.md` for endpoint usage and client examples.
- **Security**: `docs/SECURITY.md` for technical guidelines and compliance.
- **Recommended Tools**: `docs/RECOMMENDED_TOOLS.md` for approved libraries.
- **Support**: Open GitHub issue or email support@cpafirm.com

For questions or unclear conventions, see `README.md` and `docs/SECURITY.md`, or open an issue.
