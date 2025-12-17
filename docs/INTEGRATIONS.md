# Integration Guide

Comprehensive guide for integrating with QuickBooks Online and Microsoft 365 (OneDrive/SharePoint).

## Table of Contents

- [QuickBooks Online Integration](#quickbooks-online-integration)
- [Microsoft 365 Integration](#microsoft-365-integration)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## QuickBooks Online Integration

### Prerequisites

1. **QuickBooks Developer Account**: Register at [developer.intuit.com](https://developer.intuit.com)
2. **Create App**: Create a new app in the QuickBooks Developer Portal
3. **Get Credentials**: Obtain Client ID and Client Secret

### Configuration

Add to your `.env` file:

```bash
QBO_CLIENT_ID=your-client-id-here
QBO_CLIENT_SECRET=your-client-secret-here
QBO_REDIRECT_URI=https://your-app.com/api/quickbooks/auth/callback
QBO_ENVIRONMENT=sandbox  # Use 'production' for live
QBO_REALM_ID=your-company-id  # Optional, can be obtained during OAuth
```

### OAuth 2.0 Flow

#### Step 1: Initiate Authorization

```bash
POST /api/quickbooks/auth/initiate
Authorization: Bearer YOUR_JWT_TOKEN
```

Response:
```json
{
  "authorization_url": "https://appcenter.intuit.com/connect/oauth2?...",
  "state": "random-state-string"
}
```

#### Step 2: User Authorization

Redirect user to `authorization_url`. After approval, QuickBooks redirects to your callback URL with:
- `code`: Authorization code
- `realm_id`: Company ID
- `state`: CSRF protection token

#### Step 3: Token Exchange (Automatic)

The callback handler automatically exchanges the code for tokens and stores them encrypted.

### API Operations

#### Sync Trial Balance

```bash
POST /api/quickbooks/sync/trial-balance
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "realm_id": "your-company-id"
}
```

#### Get Chart of Accounts

```python
from src.integrations.quickbooks import QuickBooksAuth, QuickBooksClient

qb_auth = QuickBooksAuth()
qb_client = QuickBooksClient(qb_auth, realm_id="your-realm-id")
accounts = await qb_client.get_accounts(user_id="your-user-id")

for account in accounts:
    print(f"{account.name}: {account.current_balance}")
```

#### Create Journal Entry

```python
from src.integrations.quickbooks import QBOJournalEntry, QBOLine
from decimal import Decimal
from datetime import date

journal_entry = QBOJournalEntry(
    txn_date=date.today(),
    line=[
        QBOLine(amount=Decimal("1000.00"), account_ref={"value": "1"}),
        QBOLine(amount=Decimal("-1000.00"), account_ref={"value": "2"})
    ]
)

created_entry = await qb_client.create_journal_entry(journal_entry, user_id="your-user-id")
```

### Compliance Validation

```python
from src.integrations.quickbooks import GAAPValidator, IFRSValidator

# US GAAP Validation
gaap_validator = GAAPValidator()
is_valid, errors = gaap_validator.validate_journal_entry(journal_entry)

# IFRS Validation
ifrs_validator = IFRSValidator()
is_valid, errors = ifrs_validator.validate_journal_entry(journal_entry)
```

## Microsoft 365 Integration

### Prerequisites

1. **Azure AD Application**: Register app in [Azure Portal](https://portal.azure.com)
2. **API Permissions**: Grant permissions:
   - `Files.ReadWrite.All`
   - `Sites.ReadWrite.All`
   - `User.Read`
3. **Authentication**: Configure redirect URI

### Configuration

Add to your `.env` file:

```bash
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
M365_REDIRECT_URI=https://your-app.com/api/m365/auth/callback
SHAREPOINT_SITE_ID=your-site-id
ONEDRIVE_ROOT_FOLDER=FinancialDocuments
```

### OAuth 2.0 Flow

#### Step 1: Initiate Authorization

```bash
POST /api/m365/auth/initiate
Authorization: Bearer YOUR_JWT_TOKEN
```

#### Step 2: User Consent

User grants permissions via Microsoft login page.

#### Step 3: Token Storage

Tokens are automatically encrypted and stored securely.

### OneDrive Operations

#### List Files

```bash
GET /api/m365/onedrive/files?folder_path=FinancialDocuments
Authorization: Bearer YOUR_JWT_TOKEN
```

#### Upload File

```python
from src.integrations.m365 import GraphClient, OneDriveManager

graph_client = GraphClient()
onedrive = OneDriveManager(graph_client)

with open("invoice.pdf", "rb") as f:
    content = f.read()

uploaded_file = await onedrive.upload_file(
    file_name="invoice_2024.pdf",
    content=content,
    folder_path="Invoices",
    user_id="your-user-id",
    encrypt=True  # Encrypt before upload
)
```

#### Download File

```python
file_content = await onedrive.download_file(
    file_id="file-id-from-list",
    user_id="your-user-id",
    decrypt=True  # Decrypt after download
)

with open("downloaded_invoice.pdf", "wb") as f:
    f.write(file_content)
```

#### Delta Sync

```python
# First sync - gets all files
changed_files, delta_token = await onedrive.get_delta_changes(
    folder_path="FinancialDocuments",
    user_id="your-user-id"
)

# Subsequent syncs - only gets changes since last sync
new_changes, new_token = await onedrive.get_delta_changes(
    folder_path="FinancialDocuments",
    user_id="your-user-id"
)
```

### SharePoint Operations

#### List SharePoint Lists

```python
from src.integrations.m365 import GraphClient, SharePointManager

graph_client = GraphClient()
sharepoint = SharePointManager(graph_client, site_id="your-site-id")

lists = await sharepoint.get_lists(user_id="your-user-id")
for sp_list in lists:
    print(f"{sp_list.display_name}: {sp_list.id}")
```

#### Sync Financial Documents

```python
documents = [
    {
        "Title": "Invoice 2024-001",
        "Amount": 5000.00,
        "Date": "2024-01-15",
        "Vendor": "Acme Corp"
    },
    {
        "Title": "Invoice 2024-002",
        "Amount": 3500.00,
        "Date": "2024-01-20",
        "Vendor": "Widget Inc"
    }
]

result = await sharepoint.sync_financial_documents(
    list_id="your-list-id",
    documents=documents,
    user_id="your-user-id"
)

print(f"Created: {result['created_count']}, Errors: {result['error_count']}")
```

### Webhooks

```python
# Create webhook for real-time notifications
webhook = await onedrive.create_webhook(
    notification_url="https://your-app.com/webhooks/onedrive",
    folder_path="FinancialDocuments",
    user_id="your-user-id"
)

print(f"Webhook ID: {webhook.id}, Expires: {webhook.expiration_datetime}")
```

## Security Considerations

### Token Security

- All tokens are encrypted at rest using AES-256 encryption
- Tokens are automatically refreshed before expiration
- Refresh tokens are stored separately from access tokens
- Token revocation supported for both integrations

### Data Encryption

- All financial documents uploaded to OneDrive can be encrypted
- Use `encrypt=True` parameter when uploading sensitive files
- Encrypted files have `.encrypted` extension
- Decryption happens automatically on download with proper permissions

### Audit Logging

All integration operations are logged with:
- User ID
- Action performed
- Resource accessed
- Timestamp
- Success/failure status
- IP address (when available)

Example audit log entry:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "api_call",
  "user_id": "user@example.com",
  "action": "upload_to_onedrive",
  "resource": "onedrive/FinancialDocuments/invoice_2024.pdf",
  "status": "success",
  "details": {
    "size": 524288,
    "encrypted": true
  }
}
```

### Rate Limiting

- QuickBooks: 500 requests/minute (enforced automatically)
- Microsoft Graph: Per-user throttling (handled with retry/backoff)
- API endpoints have additional rate limits (see API documentation)

## Troubleshooting

### QuickBooks Issues

#### Token Expired
**Error**: `401 Unauthorized`
**Solution**: Tokens are automatically refreshed. If issue persists, re-authenticate.

#### Invalid Realm ID
**Error**: `Realm ID not found`
**Solution**: Ensure `realm_id` matches your QuickBooks company ID from OAuth callback.

#### Rate Limit Exceeded
**Error**: `429 Too Many Requests`
**Solution**: Requests are automatically throttled to 500/minute. Wait and retry.

### Microsoft 365 Issues

#### Insufficient Permissions
**Error**: `403 Forbidden`
**Solution**: Verify API permissions in Azure Portal. May require admin consent.

#### File Too Large
**Error**: `File size exceeds maximum`
**Solution**: Default limit is 50 MB. Use Microsoft Graph's resumable upload for larger files.

#### Delta Token Invalid
**Error**: `Invalid delta token`
**Solution**: Delta tokens expire after 30 days. Perform full sync to get new token.

### General Issues

#### Encryption Key Missing
**Error**: `Encryption key not configured`
**Solution**: Generate and set `ENCRYPTION_KEY` in `.env`:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### Audit Logs Not Appearing
**Solution**: Check `AUDIT_LOG_PATH` in `.env` and ensure directory exists.

## Support

For integration support:
- GitHub Issues: [github.com/your-repo/issues](https://github.com/your-repo/issues)
- Email: integrations@cpafirm.com
- Documentation: [github.com/your-repo/wiki](https://github.com/your-repo/wiki)
