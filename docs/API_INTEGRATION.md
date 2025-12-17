# API Integration Guide

## Quick Start

This guide shows you how to integrate the CPA Firm AI Automation API into your applications.

## Authentication

### 1. Obtain an Access Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "Demo123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 2. Use the Token

Include the token in the Authorization header for all API requests:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Core API Endpoints

### Process Invoice

Automatically extract and validate invoice data.

```bash
curl -X POST http://localhost:8000/api/invoice/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_text": "ACME Corp\nInvoice #12345\nDate: 01/15/2024\nTotal: $1,250.00"
  }'
```

Response:
```json
{
  "invoice": {
    "invoice_id": "12345",
    "vendor_name": "ACME Corp",
    "total_amount": 1250.00,
    "invoice_date": "2024-01-15",
    "confidence_score": 0.95
  },
  "is_valid": true,
  "category": "office_supplies",
  "gl_account": "6100"
}
```

### Categorize Expense

Automatically categorize expenses using AI.

```bash
curl -X POST http://localhost:8000/api/expense/categorize \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Microsoft 365 subscription",
    "vendor": "Microsoft",
    "amount": 150.00,
    "date": "2024-01-15"
  }'
```

Response:
```json
{
  "category": "software",
  "confidence": 0.89,
  "gl_account": "6800",
  "needs_review": false
}
```

### Detect Anomalies

Identify unusual patterns in transaction data.

```bash
curl -X POST http://localhost:8000/api/audit/detect-anomalies \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {
        "amount": 100,
        "vendor": "Vendor A",
        "date": "2024-01-15"
      },
      {
        "amount": 15000,
        "vendor": "Suspicious Vendor",
        "date": "2024-01-16"
      }
    ]
  }'
```

Response:
```json
{
  "total_transactions": 2,
  "anomalies_detected": 1,
  "anomalies": [
    {
      "amount": 15000,
      "anomaly_score": 0.95,
      "is_anomaly": true
    }
  ],
  "summary": {
    "anomaly_rate": 50.0
  }
}
```

### Reconcile Transactions

Match bank transactions with book entries.

```bash
curl -X POST http://localhost:8000/api/reconcile/transactions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bank_transactions": [
      {
        "amount": 1000,
        "date": "2024-01-15",
        "description": "ACME Corp"
      }
    ],
    "book_transactions": [
      {
        "amount": 1000,
        "date": "2024-01-15",
        "description": "ACME Corporation"
      }
    ]
  }'
```

Response:
```json
{
  "total_bank_transactions": 1,
  "total_book_transactions": 1,
  "matched": 1,
  "match_rate": 100.0,
  "matches": [
    {
      "bank_transaction": {...},
      "book_transaction": {...},
      "match_score": 0.95,
      "status": "matched"
    }
  ]
}
```

## Python Client Example

```python
import requests

class CPAFirmClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = None
        self.login(username, password)
    
    def login(self, username, password):
        """Authenticate and get access token."""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
    
    def process_invoice(self, invoice_text):
        """Process an invoice."""
        response = requests.post(
            f"{self.base_url}/api/invoice/process",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"invoice_text": invoice_text}
        )
        response.raise_for_status()
        return response.json()
    
    def categorize_expense(self, description, vendor, amount, date):
        """Categorize an expense."""
        response = requests.post(
            f"{self.base_url}/api/expense/categorize",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "description": description,
                "vendor": vendor,
                "amount": amount,
                "date": date
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = CPAFirmClient("http://localhost:8000", "demo", "Demo123!")

# Process invoice
invoice_result = client.process_invoice("""
    ACME Corp
    Invoice #12345
    Total: $1,250.00
""")
print(f"Invoice total: ${invoice_result['invoice']['total_amount']}")

# Categorize expense
expense_result = client.categorize_expense(
    description="Office supplies",
    vendor="Staples",
    amount=245.50,
    date="2024-01-15"
)
print(f"Category: {expense_result['category']}")
```

## JavaScript Client Example

```javascript
class CPAFirmClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.token = null;
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await response.json();
        this.token = data.access_token;
    }
    
    async processInvoice(invoiceText) {
        const response = await fetch(`${this.baseUrl}/api/invoice/process`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({invoice_text: invoiceText})
        });
        return await response.json();
    }
    
    async categorizeExpense(description, vendor, amount, date) {
        const response = await fetch(`${this.baseUrl}/api/expense/categorize`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({description, vendor, amount, date})
        });
        return await response.json();
    }
}

// Usage
const client = new CPAFirmClient('http://localhost:8000');
await client.login('demo', 'Demo123!');

const invoice = await client.processInvoice('ACME Corp\nTotal: $1,250.00');
console.log(`Invoice total: $${invoice.invoice.total_amount}`);
```

## Rate Limits

- Login: 5 requests per minute
- Invoice processing: 20 requests per minute
- Expense categorization: 50 requests per minute
- Anomaly detection: 10 requests per minute
- General read operations: 100 requests per minute

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Invalid or missing authentication
- `403 Forbidden`: Insufficient permissions
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Example error response:
```json
{
  "detail": "Invalid authentication credentials"
}
```

## Best Practices

1. **Token Management**
   - Store tokens securely
   - Refresh tokens before expiration
   - Use separate tokens for different services

2. **Error Handling**
   - Implement retry logic with exponential backoff
   - Log errors for debugging
   - Handle rate limits gracefully

3. **Performance**
   - Batch requests when possible
   - Cache frequently accessed data
   - Use async/await for concurrent requests

4. **Security**
   - Always use HTTPS in production
   - Validate input data before sending
   - Never log sensitive information
   - Rotate API credentials regularly

## Support

For questions or issues:
- GitHub Issues: https://github.com/HHR-CPA/vigilant-octo-engine/issues
- Email: support@cpafirm.com
- Documentation: https://github.com/HHR-CPA/vigilant-octo-engine/wiki
