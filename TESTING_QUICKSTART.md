# Testing Quick Start Guide

Welcome to testing the CPA Firm Automation project! This guide will get you running tests in **5 minutes**.

## ⚡ Quick Setup

### 1. Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone https://github.com/HHR-CPA/vigilant-octo-engine.git
cd vigilant-octo-engine

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Tests (1 minute)

```bash
# Run all tests
pytest tests/ -v
```

**Expected Result:**
```
======================= 49 passed, 21 warnings in 1.88s ========================
```

## ✅ What to Test

### Core Functionality

```bash
# Test security features
pytest tests/test_security.py -v

# Test API endpoints
pytest tests/test_api.py -v

# Test AI/ML features
pytest tests/test_anomaly_detection.py -v
pytest tests/test_expense_categorization.py -v
pytest tests/test_invoice_processing.py -v

# Test performance
pytest tests/test_performance.py -v
```

### With Coverage Report

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🚨 Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
pip install httpx pytest pytest-cov
```

### Issue: Permission Denied

```bash
# Solution: Create required directories
mkdir -p logs models secure_data
chmod 700 secure_data  # Unix/Linux/Mac only
```

### Issue: Tests Failing

1. Make sure you're in the project root directory
2. Ensure virtual environment is activated
3. Check Python version: `python --version` (should be 3.8+)
4. Clear cache: `pytest --cache-clear`

## 📊 Test Status

Current test suite status:
- **Total Tests:** 49
- **Passing:** 49 (100%)
- **Security Tests:** 9
- **API Tests:** 16  
- **AI/ML Tests:** 13
- **Performance Tests:** 11

## 🆘 Get Help

- **Full Documentation:** [docs/TESTING.md](docs/TESTING.md)
- **Issues:** [GitHub Issues](https://github.com/HHR-CPA/vigilant-octo-engine/issues)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

## 🎯 Next Steps

1. ✅ Tests passing? Great! Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. 📝 Found a bug? Open an issue
3. 🔧 Want to contribute? See [docs/TESTING.md](docs/TESTING.md)
4. 🚀 Build something? Check [README.md](README.md) for API usage

---

**That's it! You're ready to test. Happy testing! 🎉**
