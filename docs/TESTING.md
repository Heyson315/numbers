# Testing Guide for CPA Firm Automation

This document provides comprehensive guidance for running and contributing tests to this project.

## 🎯 Overview

This project uses pytest as the testing framework with comprehensive test coverage across:
- **Security** - Encryption, authentication, access control
- **AI/ML** - Invoice processing, expense categorization, anomaly detection
- **API** - REST endpoints, rate limiting, CORS
- **Performance** - Scalability and optimization validation

## 📋 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Virtual environment** (recommended)
3. **Dependencies** installed

### Installation

```bash
# Clone the repository
git clone https://github.com/HHR-CPA/vigilant-octo-engine.git
cd vigilant-octo-engine

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install test dependencies (if not in requirements.txt)
pip install pytest pytest-cov pytest-asyncio httpx
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_security.py -v

# Run specific test class
pytest tests/test_security.py::TestEncryptionManager -v

# Run specific test
pytest tests/test_security.py::TestEncryptionManager::test_encrypt_decrypt_data -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Open coverage report in browser
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
start htmlcov/index.html  # On Windows
```

## 📊 Test Structure

```
tests/
├── __init__.py
├── test_anomaly_detection.py   # AI anomaly detection tests (5 tests)
├── test_api.py                  # REST API tests (16 tests)
├── test_expense_categorization.py  # ML expense tests (5 tests)
├── test_invoice_processing.py   # Invoice processing tests (3 tests)
├── test_performance.py          # Performance regression tests (11 tests)
└── test_security.py             # Security tests (9 tests)
```

### Current Test Count: **49 tests passing**

## 🔐 Environment Setup

Tests require environment variables for security components. These are automatically set by pytest fixtures, but you can override them:

```bash
# Create .env file (optional for testing)
cp .env.example .env

# Key environment variables for tests
export ENCRYPTION_KEY="test_key_for_encryption_1234567890"
export SECRET_KEY="test-secret-key-change-in-production"
```

**Note:** Tests use safe default values, so `.env` is optional for running tests.

## 🧪 Test Categories

### 1. Security Tests (`test_security.py`)

Tests encryption, authentication, and access control:

```bash
pytest tests/test_security.py -v
```

**Key Tests:**
- `test_encrypt_decrypt_data` - Data encryption/decryption
- `test_password_hashing` - Password security
- `test_jwt_token_creation` - JWT authentication
- `test_permission_checking` - RBAC validation
- `test_store_retrieve_secure_data` - Secure file handling

### 2. API Tests (`test_api.py`)

Tests REST endpoints, rate limiting, and error handling:

```bash
pytest tests/test_api.py -v
```

**Key Tests:**
- `test_health` - Health check endpoint
- `test_auth_required` - Authentication enforcement
- `test_jwt_and_rbac` - Role-based access control
- `test_rate_limiting` - API rate limits
- `test_cors` - CORS configuration
- `test_no_sensitive_data_in_logs` - Security logging

### 3. AI/ML Tests

#### Anomaly Detection (`test_anomaly_detection.py`)

```bash
pytest tests/test_anomaly_detection.py -v
```

**Key Tests:**
- `test_detect_transaction_anomalies` - Outlier detection
- `test_detect_duplicate_transactions` - Duplicate finding
- `test_benford_law_violations` - Fraud detection
- `test_calculate_transaction_risk` - Risk scoring

#### Expense Categorization (`test_expense_categorization.py`)

```bash
pytest tests/test_expense_categorization.py -v
```

**Key Tests:**
- `test_categorize_office_supplies` - Category classification
- `test_suggest_gl_account` - GL account mapping
- `test_fuzzy_match_transactions` - Smart reconciliation

#### Invoice Processing (`test_invoice_processing.py`)

```bash
pytest tests/test_invoice_processing.py -v
```

**Key Tests:**
- `test_extract_invoice_data` - Data extraction
- `test_validate_invoice` - Validation logic
- `test_categorize_expense` - Expense categorization

### 4. Performance Tests (`test_performance.py`)

Tests to ensure performance requirements are met:

```bash
pytest tests/test_performance.py -v
```

**Key Tests:**
- `test_transaction_matching_performance` - Reconciliation speed
- `test_duplicate_detection_performance` - Detection efficiency
- `test_invoice_processing_performance` - Processing speed
- `test_transaction_matching_scales_linearly` - Scalability

## 🎨 Writing Tests

### Test Structure

Follow these conventions when writing tests:

```python
"""
Description of test module.
"""

import pytest
from src.module import ClassToTest


class TestClassName:
    """Test class description."""
    
    def test_specific_functionality(self):
        """Test description."""
        # Arrange
        instance = ClassToTest()
        input_data = "test data"
        
        # Act
        result = instance.method(input_data)
        
        # Assert
        assert result == expected_value
```

### Fixtures

Use pytest fixtures for reusable test data:

```python
@pytest.fixture
def sample_transactions():
    """Provide sample transaction data."""
    return [
        {'amount': 100.0, 'date': '2024-01-01', 'vendor': 'Acme Corp'},
        {'amount': 250.0, 'date': '2024-01-02', 'vendor': 'Tech Inc'}
    ]

def test_with_fixture(sample_transactions):
    """Test using fixture."""
    assert len(sample_transactions) == 2
```

### Testing Security

**DO NOT** commit real credentials or sensitive data:

```python
# ❌ BAD
def test_with_real_password():
    password = "my_real_password_123"  # Never do this!

# ✅ GOOD
def test_with_fake_password():
    password = "test_password_for_testing_only"
```

### Testing API Endpoints

Use FastAPI's TestClient:

```python
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_endpoint():
    """Test API endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()
```

## 🚀 Continuous Integration

Tests run automatically on:
- **Pull Requests** to main branch
- **Pushes** to main/develop branches

### CI Workflow

The CI pipeline (`.github/workflows/ci.yml`) runs:

1. **Backend Tests**
   - Install Python dependencies
   - Run pytest with coverage
   - Run security linting (bandit)
   - Run security audit (pip-audit)

2. **Frontend Tests** (in `frontend/`)
   - Install Node.js dependencies
   - Run ESLint
   - Run TypeScript type checking
   - Run Vitest tests

3. **Security Scans**
   - TruffleHog secret scanning
   - Dependency vulnerability checking

### Expected Results

All tests must pass before merging:
- ✅ 49/49 backend tests passing
- ✅ No security vulnerabilities
- ✅ Coverage > 80%

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors

```
ModuleNotFoundError: No module named 'src'
```

**Solution:** Ensure you're in the project root directory and dependencies are installed:

```bash
cd /path/to/vigilant-octo-engine
pip install -r requirements.txt
```

#### 2. Missing Dependencies

```
ModuleNotFoundError: No module named 'httpx'
```

**Solution:** Install missing packages:

```bash
pip install httpx pytest pytest-cov pytest-asyncio
```

#### 3. Environment Variable Errors

```
KeyError: 'ENCRYPTION_KEY'
```

**Solution:** Tests should auto-set these, but you can set manually:

```bash
export ENCRYPTION_KEY="test_key_for_encryption_1234567890"
export SECRET_KEY="test-secret-key"
```

#### 4. Permission Errors (Unix/Linux/Mac)

```
PermissionError: [Errno 13] Permission denied: './secure_data'
```

**Solution:** Ensure directories exist and have correct permissions:

```bash
mkdir -p logs models secure_data
chmod 700 secure_data
```

#### 5. Port Already in Use (API Tests)

```
OSError: [Errno 98] Address already in use
```

**Solution:** Kill process on port 8000 or use TestClient (which doesn't need a port):

```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

### Verbose Output

For debugging, use verbose and traceback options:

```bash
# Show full output
pytest tests/ -v -s

# Show detailed traceback
pytest tests/ -v --tb=long

# Show local variables in traceback
pytest tests/ -v --tb=long --showlocals
```

## 📝 Best Practices

### 1. Test Naming

- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<specific_behavior>`

### 2. Test Isolation

Each test should be independent:

```python
# ✅ GOOD - Each test creates its own instance
def test_something():
    instance = ClassToTest()
    # test logic

def test_something_else():
    instance = ClassToTest()  # Fresh instance
    # test logic

# ❌ BAD - Shared state between tests
instance = ClassToTest()  # Module-level!

def test_something():
    instance.modify()  # Affects other tests

def test_something_else():
    instance.read()  # Depends on previous test
```

### 3. Assertions

Use descriptive assertions:

```python
# ✅ GOOD
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert "result" in data, "Response missing 'result' field"

# ❌ BAD
assert response.status_code == 200
assert "result" in data
```

### 4. Test Coverage

Aim for >80% coverage:

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

Focus on:
- ✅ Critical security functions
- ✅ Business logic
- ✅ Error handling
- ❌ Skip: simple getters/setters

## 🤝 Contributing Tests

### Adding New Tests

1. **Identify the module** to test
2. **Create or update** corresponding test file
3. **Write test class and methods** following conventions
4. **Run tests locally** to ensure they pass
5. **Check coverage** to ensure new code is tested
6. **Submit pull request** with test changes

### Pull Request Checklist

- [ ] All existing tests pass
- [ ] New tests added for new features
- [ ] Coverage maintained or improved
- [ ] No secrets or sensitive data committed
- [ ] Tests follow naming conventions
- [ ] CI pipeline passes

### Example Contribution

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Add your code and tests
# Edit src/new_module.py
# Edit tests/test_new_module.py

# 3. Run tests locally
pytest tests/ -v

# 4. Check coverage
pytest tests/ --cov=src --cov-report=html

# 5. Commit and push
git add src/new_module.py tests/test_new_module.py
git commit -m "Add new feature with tests"
git push origin feature/new-feature

# 6. Open pull request on GitHub
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
- [Project README](../README.md)
- [Security Guidelines](./SECURITY.md)
- [API Documentation](./API_INTEGRATION.md)

## 🔗 Related Documentation

- [README.md](../README.md) - Project overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](./SECURITY.md) - Security best practices
- [API_INTEGRATION.md](./API_INTEGRATION.md) - API documentation

## 📧 Support

For testing questions or issues:
- Open an issue on [GitHub](https://github.com/HHR-CPA/vigilant-octo-engine/issues)
- Check existing issues and discussions
- Email support: support@cpafirm.com (Note: Replace with actual support email for production use)

---

**Happy Testing! 🎉**

Remember: Good tests make good software. Thank you for contributing!
