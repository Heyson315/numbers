# AI Solutions for CPA Firm Automation

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Security](https://img.shields.io/badge/security-enabled-green.svg)](docs/SECURITY.md)
[![Tests](https://img.shields.io/badge/tests-49%20passing-brightgreen.svg)](docs/TESTING.md)
[![Coverage](https://img.shields.io/badge/coverage-80%25%2B-brightgreen.svg)](docs/TESTING.md)

A comprehensive AI-powered solution for automating finance, audit, and accounting tasks in CPA firm environments with enterprise-grade security controls.

## 🎯 Features

### AI-Powered Automation
- **Invoice Processing**: Automatically extract and validate data from invoices using NLP and pattern recognition
- **Expense Categorization**: ML-powered expense classification with GL account suggestions
- **Audit Trail Automation**: Comprehensive audit logging with anomaly detection
- **Financial Reconciliation**: Fuzzy matching for bank and book transaction reconciliation
- **Fraud Detection**: Multi-layered anomaly detection including Benford's Law analysis

### Security & Compliance
- **Data Encryption**: AES-256 encryption for sensitive financial data
- **Access Control**: Role-based permissions with JWT authentication
- **Audit Logging**: Comprehensive activity tracking for compliance
- **Secure API**: Rate-limited REST API with HTTPS support
- **Input Sanitization**: Protection against injection attacks
- **Data Retention**: Configurable retention policies for regulatory compliance

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Security Best Practices](#security-best-practices)
- [Architecture](#architecture)
- [Testing](#testing)
- [Contributing](#contributing)

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Step-by-Step Installation

1. **Clone the repository**
```bash
git clone https://github.com/HHR-CPA/vigilant-octo-engine.git
cd vigilant-octo-engine
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize secure storage directories**
```bash
mkdir -p logs models secure_data
chmod 700 secure_data  # Restrict access on Unix systems
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following:

```bash
# Security Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ENCRYPTION_KEY=your-encryption-key-here-change-in-production

# Database Configuration
DATABASE_URL=sqlite:///./cpa_finance.db

# Audit Logging
AUDIT_LOG_PATH=./logs/audit.log
AUDIT_LOG_RETENTION_DAYS=365

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RATE_LIMIT=100/minute
```

**⚠️ Important**: 
- Generate secure random keys for production
- Never commit `.env` to version control
- Use PostgreSQL for production environments
- Enable HTTPS with valid SSL certificates

## 📖 Usage

### Starting the API Server

```bash
python src/api.py
```

The API will be available at `http://localhost:8000`

### Using the AI Modules

#### Invoice Processing

```python
from src.invoice_processing import InvoiceProcessor

processor = InvoiceProcessor()

invoice_text = """
ACME Corp
Invoice #INV-2024-001
Date: 01/15/2024
Total: $1,250.00
"""

invoice = processor.extract_invoice_data(invoice_text)
is_valid, errors = processor.validate_invoice(invoice)
category = processor.categorize_expense(invoice)

print(f"Category: {category}")
print(f"Valid: {is_valid}")
```

#### Expense Categorization

```python
from src.expense_categorization import ExpenseCategorizer

categorizer = ExpenseCategorizer()

category, confidence = categorizer.categorize(
    description="Microsoft Office 365 Subscription",
    vendor="Microsoft",
    amount=150.00
)

gl_account = categorizer.suggest_gl_account(category)

print(f"Category: {category} (Confidence: {confidence:.2%})")
print(f"GL Account: {gl_account}")
```

#### Anomaly Detection

```python
from src.anomaly_detection import AnomalyDetector
import pandas as pd

detector = AnomalyDetector()

transactions = pd.DataFrame({
    'amount': [100, 150, 120, 5000, 110],
    'vendor': ['A', 'B', 'A', 'C', 'B'],
    'date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19']
})

results = detector.detect_transaction_anomalies(transactions)
anomalies = results[results['is_anomaly']]

print(f"Detected {len(anomalies)} anomalies")
```

#### Secure Data Handling

```python
from src.security import EncryptionManager, AccessControl

# Encryption
encryption = EncryptionManager()
sensitive_data = {"account": "123456", "balance": 50000}
encrypted = encryption.encrypt_dict(sensitive_data)
decrypted = encryption.decrypt_dict(encrypted)

# Authentication
access_control = AccessControl()
token = access_control.create_access_token({"user": "john", "role": "accountant"})
user_data = access_control.verify_token(token)
```

## 🔌 API Documentation

### Authentication

All API endpoints (except `/api/health`) require authentication using JWT tokens.

**Login**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "Demo123!"}'
```

**Use Token**
```bash
curl -X POST http://localhost:8000/api/invoice/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invoice_text": "..."}'
```

### Main Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/login` | POST | Authenticate and get token | No |
| `/api/invoice/process` | POST | Process invoice | Yes |
| `/api/expense/categorize` | POST | Categorize expense | Yes |
| `/api/audit/detect-anomalies` | POST | Detect anomalies | Yes (Auditor) |
| `/api/audit/generate-report` | POST | Generate audit report | Yes (Auditor) |
| `/api/reconcile/transactions` | POST | Reconcile transactions | Yes |
| `/api/health` | GET | Health check | No |

Full API documentation available at `http://localhost:8000/docs` when server is running.

## 🔒 Security Best Practices

### For Production Deployment

1. **Environment Security**
   - Use strong, randomly generated keys
   - Store secrets in secure vault (e.g., AWS Secrets Manager, HashiCorp Vault)
   - Enable HTTPS with valid SSL certificates
   - Use PostgreSQL instead of SQLite

2. **Access Control**
   - Implement multi-factor authentication (MFA)
   - Use role-based access control (RBAC)
   - Regularly rotate API keys and tokens
   - Monitor failed authentication attempts

3. **Data Protection**
   - Encrypt data at rest and in transit
   - Implement data retention policies
   - Regular security audits
   - Secure file upload validation

4. **Network Security**
   - Use firewall rules to restrict access
   - Implement rate limiting
   - Enable CORS only for trusted domains
   - Use VPN or private network for sensitive operations

5. **Audit & Compliance**
   - Enable comprehensive audit logging
   - Regular review of audit logs
   - Maintain logs for required retention period
   - Implement automated alerting for suspicious activities

### Recommended Tools & Libraries

#### Security & Encryption
- **cryptography**: Industry-standard encryption library
- **python-jose**: JWT implementation
- **passlib**: Password hashing with bcrypt

#### AI/ML for Finance
- **scikit-learn**: Machine learning algorithms
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing

#### API & Web
- **FastAPI**: Modern, fast web framework
- **uvicorn**: ASGI server
- **slowapi**: Rate limiting

#### Audit & Logging
- **python-json-logger**: Structured logging
- **SQLAlchemy**: Database ORM with security features

#### Data Validation
- **pydantic**: Data validation using Python type annotations
- **cerberus**: Lightweight data validation

## 🏗️ Architecture

```
vigilant-octo-engine/
├── src/
│   ├── __init__.py
│   ├── api.py                      # REST API with security
│   ├── security.py                 # Encryption, access control
│   ├── audit_logging.py            # Audit trail management
│   ├── invoice_processing.py       # AI invoice automation
│   ├── expense_categorization.py   # ML expense categorization
│   └── anomaly_detection.py        # Fraud detection
├── tests/
│   ├── test_security.py
│   ├── test_invoice_processing.py
│   ├── test_expense_categorization.py
│   └── test_anomaly_detection.py
├── logs/                           # Audit logs
├── models/                         # AI models cache
├── secure_data/                    # Encrypted data storage
├── requirements.txt                # Dependencies
├── .env.example                    # Configuration template
└── README.md
```

## 🖥️ Frontend (React + Vite)

An accompanying frontend lives in `frontend/` for interactive use of the secured API.

### Development Setup
```bash
cd frontend
npm install
npm run dev
```
Served at `http://localhost:5173` with proxying of `/api/*` to the backend (configured in `vite.config.ts`).

### Key Frontend Files
- `frontend/package.json` – scripts (`dev`, `build`, `test`) and dependencies.
- `frontend/src/types.ts` – Typed interfaces mirroring backend responses.
- `frontend/src/apiClient.ts` – Thin fetch wrapper; always sends `Content-Type: application/json` and attaches JWT via `Authorization` header.
- `frontend/src/AuthContext.tsx` – In‑memory auth state (token not persisted to localStorage for security).
- `frontend/src/ProtectedRoute.tsx` – Redirects unauthenticated users to `/login`.
- Pages: `Invoice`, `Expense`, `Anomaly`, `Audit`, `Dashboard`, `Login` under `frontend/src/pages/`.
 - Components: Reusable UI in `frontend/src/components/` (`Navbar`, `LoadingSpinner`, `ErrorBoundary`).
 - Hooks: `frontend/src/hooks/` (`useAuth`, `useApi`, `usePolling`) abstract auth & polling logic.
 - Services: Thin domain wrappers in `frontend/src/services/` (e.g. `invoiceService.ts`).
 - Utils: Formatting helpers in `frontend/src/utils/` (`formatCurrency`, `parseDate`).
 - Configuration: ESLint (`.eslintrc.cjs`), Prettier (`.prettierrc`), EditorConfig (`.editorconfig`) and env files (`.env.development`, `.env.production`).

### Security Considerations
- Tokens are kept only in React state (avoid XSS/localStorage persistence).
- CORS updated to allow `http://localhost:5173` for development only (see `src/api.py`).
- Do not add arbitrary origins—review before deployment.

### Testing (Frontend)
Vitest + Testing Library for component and client tests:
```bash
npm run test
```
Example tests in `frontend/src/__tests__/` validate API client request structure and protected routing.
 Additional test environment uses jsdom (configured in `vite.config.ts`).

### Building
```bash
npm run build
```
Outputs production assets to `frontend/dist/` (serve behind HTTPS; ensure secure headers).

### Linting & Formatting
```bash
npm run lint     # ESLint (zero warnings policy for CI)
npm run type-check  # TypeScript compile check without emit
npm run format   # Prettier format all changed files
```

### Environment Variables
Frontend uses Vite prefixed vars:
```
VITE_API_BASE_URL=http://localhost:8000/api   # dev
VITE_API_BASE_URL=/api                        # production (reverse proxy)
VITE_APP_ENV=development|production
```
Never expose secrets—only non-sensitive config belongs in Vite prefixed variables.

### Recommended Hardening (Production)
- Enable HTTPS & HSTS at reverse proxy layer.
- Add Content Security Policy (CSP) disallowing inline scripts; move any inline styles to CSS.
- Use Subresource Integrity (SRI) for third‑party scripts (if any).
- Prefer ephemeral memory token storage (already implemented) and short JWT lifetimes with silent refresh.
- Implement backend rate limiting (already via `slowapi`) and enforce per‑origin CORS.

### SharePoint / M365 Integration (Optional Roadmap)
If embedding in SharePoint, wrap built assets in SPFx web part or host as Teams tab:
- Acquire Azure AD token via MSAL and pass through to backend.
- Use Graph for user profile enrichment while keeping financial data strictly backend-bound.
- Store only minimal invoice metadata in SharePoint Lists; keep sensitive payloads encrypted server-side.

### Folder Summary
```
frontend/
├── .eslintrc.cjs
├── .prettierrc
├── .editorconfig
├── .env.development
├── .env.production
├── package.json
├── vite.config.ts
├── src/
│   ├── apiClient.ts
│   ├── AuthContext.tsx
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorBoundary.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   └── usePolling.ts
│   ├── services/
│   │   ├── invoiceService.ts
│   │   ├── expenseService.ts
│   │   ├── anomalyService.ts
│   │   ├── reconciliationService.ts
│   │   └── auditService.ts
│   ├── utils/
│   │   ├── formatCurrency.ts
│   │   └── parseDate.ts
│   ├── pages/
│   │   ├── Invoice.tsx
│   │   ├── Expense.tsx
│   │   ├── Anomaly.tsx
│   │   ├── Audit.tsx
│   │   ├── Dashboard.tsx
│   │   └── Login.tsx
│   ├── __tests__/
│   │   ├── apiClient.test.ts
│   │   ├── ProtectedRoute.test.tsx
│   │   └── services.test.ts
│   ├── types.ts
│   ├── ProtectedRoute.tsx
│   ├── setupTests.ts
│   ├── App.tsx
│   └── main.tsx
└── index.html
```

### Extending
- Add new API endpoint: implement backend route, then create typed wrapper in `apiClient.ts` and interface in `types.ts`.
- Keep mappings 1:1 with backend response fields; prefer explicit interfaces over `any`.

---

## 🧪 Testing

**Quick Start:** See [TESTING_QUICKSTART.md](TESTING_QUICKSTART.md) for a 5-minute setup guide.

**Full Documentation:** [docs/TESTING.md](docs/TESTING.md)

### Current Test Status
- ✅ **49 tests passing** (100%)
- ✅ Security tests: 9
- ✅ API tests: 16
- ✅ AI/ML tests: 13
- ✅ Performance tests: 11

### Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_security.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Categories

| Category | File | Tests | Description |
|----------|------|-------|-------------|
| Security | `test_security.py` | 9 | Encryption, auth, access control |
| API | `test_api.py` | 16 | REST endpoints, rate limiting |
| Anomaly Detection | `test_anomaly_detection.py` | 5 | Fraud detection, outliers |
| Expense Categorization | `test_expense_categorization.py` | 5 | ML classification, reconciliation |
| Invoice Processing | `test_invoice_processing.py` | 3 | Data extraction, validation |
| Performance | `test_performance.py` | 11 | Scalability, regression |

### For Contributors

When contributing, ensure:
- All tests pass locally
- Add tests for new features
- Maintain >80% code coverage
- Follow testing conventions in [docs/TESTING.md](docs/TESTING.md)

## 📊 Use Cases

### 1. Automated Invoice Processing
- Extract data from PDF/image invoices
- Validate invoice information
- Categorize expenses automatically
- Suggest GL accounts for posting

### 2. Expense Management
- Categorize expenses using AI
- Identify tax-deductible expenses
- Detect policy violations
- Generate spending reports

### 3. Audit & Compliance
- Detect duplicate transactions
- Identify unusual patterns
- Benford's Law analysis for fraud detection
- Comprehensive audit trail

### 4. Financial Reconciliation
- Match bank transactions with books
- Identify discrepancies
- Automated reconciliation suggestions
- Exception reporting

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**For developers using GitHub Copilot or AI assistants:** This repository includes [Copilot instructions](.github/copilot-instructions.md) that provide context about our architecture, security practices, and coding conventions. Review these instructions to better understand the codebase.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided as-is for CPA firms to automate financial processes. Users are responsible for:
- Ensuring compliance with applicable regulations
- Implementing appropriate security measures
- Regular security audits and updates
- Data backup and disaster recovery
- Consulting with legal and compliance teams

## 📞 Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Contact: support@cpafirm.com
- Documentation: [GitHub Wiki](https://github.com/HHR-CPA/vigilant-octo-engine/wiki)

## 🔄 Roadmap

- [x] Integration with QuickBooks Online (OAuth 2.0 + PKCE)
- [x] Integration with Microsoft 365 (OneDrive/SharePoint)
- [x] Financial analysis engine (ratios, trial balance, reconciliation)
- [x] HIPAA/GDPR/SOX compliance framework
- [x] Immutable audit trail with blockchain-style chaining
- [ ] OCR for invoice scanning
- [ ] Advanced ML models (deep learning)
- [ ] Mobile app for expense submission
- [ ] Multi-currency support
- [ ] Automated tax form generation

## 🆕 New Features

### Enterprise Integrations
- **QuickBooks Online**: Full OAuth 2.0 integration with PKCE, trial balance sync, journal entries, invoices
- **Microsoft 365**: Azure AD authentication, OneDrive file sync, SharePoint list integration
- **GAAP/IFRS Validation**: Automated compliance checking for financial data

### Financial Analysis Engine
- **Trial Balance Analysis**: Variance detection, period comparisons, budget vs actual
- **Financial Ratios**: Liquidity, profitability, leverage, and efficiency ratios
- **Adjusting Entries**: ML-powered suggestions for accruals, prepayments, depreciation
- **Pattern Recognition**: Seasonality detection, spending trends, anomaly identification
- **Enhanced Reconciliation**: Fuzzy matching for bank/book transactions

### Compliance Framework
- **RBAC**: Enhanced role-based access control with granular permissions (Admin, Auditor, Accountant, Viewer)
- **HIPAA**: PHI encryption, access logging, breach detection, 6-year retention
- **GDPR**: Consent management, Right to Access/Erasure/Portability, DPO notifications
- **SOX**: Segregation of duties, control testing, access reviews, financial transaction logging
- **Immutable Audit Trail**: SHA-256 blockchain-style chaining with tamper detection
- **Data Retention**: Configurable policies (SOX 7-year, HIPAA 6-year)

### Getting Started with Integrations

See [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) for detailed setup instructions.

**Quick Setup:**

1. Configure QuickBooks OAuth:
```bash
QBO_CLIENT_ID=your-client-id
QBO_CLIENT_SECRET=your-client-secret
QBO_REDIRECT_URI=https://your-app.com/api/quickbooks/auth/callback
```

2. Configure Microsoft 365:
```bash
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

3. Enable compliance features:
```bash
HIPAA_AUDIT_LOG_RETENTION_DAYS=2190
GDPR_CONSENT_EXPIRY_DAYS=365
SOX_SEGREGATION_ENABLED=true
```

### Compliance Features

See [docs/COMPLIANCE.md](docs/COMPLIANCE.md) for complete compliance documentation.

**Example Usage:**

```python
# HIPAA PHI encryption
from src.compliance import HIPAACompliance
hipaa = HIPAACompliance()
encrypted_phi = hipaa.encrypt_phi(phi_data, user_id="doctor@hospital.com")

# GDPR data subject rights
from src.compliance import GDPRCompliance
gdpr = GDPRCompliance()
data_export = gdpr.right_to_access(data_subject_id="user@example.com")

# SOX control testing
from src.compliance import SOXCompliance
sox = SOXCompliance()
test_result = sox.test_control(control_id="CTRL-001", test_result="pass")
```

---

**Built with ❤️ for CPA firms seeking to automate and secure their financial operations.**