# Compliance Controls Documentation

Comprehensive documentation for HIPAA, GDPR, and SOX compliance controls.

## Table of Contents

- [HIPAA Compliance](#hipaa-compliance)
- [GDPR Compliance](#gdpr-compliance)
- [SOX Compliance](#sox-compliance)
- [RBAC & Access Control](#rbac--access-control)
- [Audit Trail](#audit-trail)
- [Data Retention](#data-retention)

## HIPAA Compliance

### Overview

Health Insurance Portability and Accountability Act (HIPAA) compliance controls for handling Protected Health Information (PHI).

### PHI Identification

The system automatically identifies PHI based on field names:
- SSN/Social Security Number
- Medical Record Number
- Health Plan Number
- Patient ID
- Diagnosis codes
- Prescription information
- Treatment records

### Encryption Requirements

**At Rest**: All PHI is encrypted using AES-256 encryption before storage.

```python
from src.compliance import HIPAACompliance

hipaa = HIPAACompliance()

# Encrypt PHI data
phi_data = {
    "patient_id": "P12345",
    "ssn": "123-45-6789",
    "diagnosis": "Type 2 Diabetes"
}

encrypted_phi = hipaa.encrypt_phi(phi_data, user_id="doctor@hospital.com")
```

**In Transit**: All API communications use HTTPS/TLS 1.2+.

### Access Logging

**Requirement**: All PHI access must be logged with:
- User ID
- Timestamp
- Business purpose
- Data accessed
- IP address

```python
# Logging is automatic when decrypting PHI
decrypted_data = hipaa.decrypt_phi(
    encrypted_data=encrypted_phi,
    user_id="nurse@hospital.com",
    purpose="Patient care - medication review"
)

# Manual logging for other PHI access
hipaa.log_phi_access(
    user_id="doctor@hospital.com",
    phi_identifier="P12345",
    action="view",
    purpose="Treatment consultation",
    ip_address="192.168.1.100"
)
```

### Breach Detection

Automated breach detection monitors for:
- Excessive access (>100 records in short period)
- Off-hours access (before 6 AM or after 8 PM)
- Access from unusual locations
- Unauthorized access attempts

```python
# Run breach detection
access_logs = [...]  # List of access log entries
breach_report = hipaa.detect_breach(access_logs, user_id="security_officer")

if breach_report["breach_detected"]:
    print(f"⚠️ {len(breach_report['alerts'])} potential breaches detected")
    for alert in breach_report["alerts"]:
        print(f"  - {alert['type']}: {alert['message']}")
```

### Audit Log Retention

**Requirement**: 6 years minimum

Configuration in `.env`:
```bash
HIPAA_AUDIT_LOG_RETENTION_DAYS=2190  # 6 years
```

### Compliance Report

```python
# Generate HIPAA compliance report
report = hipaa.generate_hipaa_report()

print(json.dumps(report, indent=2))
```

Output:
```json
{
  "audit_log_retention_days": 2190,
  "encryption_enabled": true,
  "access_logging_enabled": true,
  "breach_detection_enabled": true,
  "compliance_checks": {
    "encryption_at_rest": "enabled",
    "encryption_in_transit": "enabled",
    "access_controls": "enforced",
    "audit_trail": "maintained",
    "breach_notification": "configured"
  },
  "report_date": "2024-01-15T10:00:00Z"
}
```

## GDPR Compliance

### Overview

General Data Protection Regulation (GDPR) compliance controls for personal data protection.

### Consent Management

**Requirement**: Explicit consent for data processing with expiration.

```python
from src.compliance import GDPRCompliance

gdpr = GDPRCompliance()

# Record consent
consent = gdpr.record_consent(
    data_subject_id="user@example.com",
    purpose="Marketing communications",
    consent_given=True,
    user_id="admin@company.com"
)

# Check consent validity
has_consent = gdpr.check_consent(
    data_subject_id="user@example.com",
    purpose="Marketing communications"
)
```

Configuration:
```bash
GDPR_CONSENT_EXPIRY_DAYS=365  # Consent expires after 1 year
```

### Right to Access (Article 15)

**Requirement**: Data subjects can request all their personal data.

API Endpoint:
```bash
GET /api/compliance/gdpr/data-subject/{data_subject_id}
Authorization: Bearer ADMIN_OR_AUDITOR_TOKEN
```

Python:
```python
# Export all data for a data subject
data_export = gdpr.right_to_access(
    data_subject_id="user@example.com",
    user_id="dpo@company.com"
)

print(f"Exported {len(data_export['data'])} records")
```

### Right to Erasure (Article 17)

**Requirement**: Data subjects can request deletion of their data.

API Endpoint:
```bash
DELETE /api/compliance/gdpr/data-subject/{data_subject_id}
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "reason": "User requested deletion under GDPR Article 17"
}
```

Python:
```python
# Delete/anonymize all data for a data subject
result = gdpr.right_to_erasure(
    data_subject_id="user@example.com",
    user_id="dpo@company.com",
    reason="User requested deletion"
)

print(f"Status: {result['status']}, Date: {result['erasure_date']}")
```

### Right to Data Portability (Article 20)

**Requirement**: Data subjects can export their data in machine-readable format.

```python
# Export data in portable format
portable_data = gdpr.right_to_portability(
    data_subject_id="user@example.com",
    export_format="json",  # Supports: json, csv, xml
    user_id="user@example.com"
)

# Save to file
with open("my_data_export.json", "w") as f:
    json.dump(portable_data, f, indent=2)
```

### Data Protection Officer (DPO) Notifications

**Requirement**: Notify DPO of data breaches within 72 hours.

```python
# Notify DPO of incident
notification = gdpr.notify_dpo(
    incident_type="data_breach",
    details={
        "affected_users": 150,
        "data_type": "email_addresses",
        "breach_date": "2024-01-15T03:00:00Z",
        "discovery_date": "2024-01-15T09:00:00Z"
    },
    user_id="security_officer@company.com"
)
```

### Compliance Report

```python
report = gdpr.generate_gdpr_report()

print(json.dumps(report, indent=2))
```

## SOX Compliance

### Overview

Sarbanes-Oxley Act (SOX) compliance controls for financial reporting and internal controls.

### Segregation of Duties (Section 404)

**Requirement**: Prevent same person from creating and approving transactions.

```python
from src.compliance import SOXCompliance

sox = SOXCompliance()

# Check segregation of duties before allowing action
sod_check = sox.check_segregation_of_duties(
    user_id="accountant@company.com",
    action="approve_transaction",
    resource="transaction/TXN-2024-001"
)

if not sod_check["approved"]:
    raise Exception("SOD violation: User cannot approve own transactions")
```

Configuration:
```bash
SOX_SEGREGATION_ENABLED=true
```

### Financial Transaction Logging

**Requirement**: Complete audit trail for all financial transactions.

```python
# Log financial transaction
sox.log_financial_transaction(
    transaction_id="TXN-2024-001",
    transaction_type="journal_entry",
    amount="5000.00",
    created_by="accountant@company.com",
    approved_by="controller@company.com"
)
```

### Access Reviews (Section 404)

**Requirement**: Periodic review of user access rights.

```python
from datetime import datetime, timedelta

# Schedule quarterly access review
review = sox.schedule_access_review(
    review_date=datetime.utcnow() + timedelta(days=90),
    reviewer_id="auditor@company.com",
    scope="All financial system users",
    user_id="it_admin@company.com"
)

# Complete access review
findings = [
    {
        "user": "temp_contractor@company.com",
        "issue": "Access not revoked after contract ended",
        "severity": "high"
    }
]

completed_review = sox.complete_access_review(
    review_id=review["review_id"],
    findings=findings,
    reviewer_id="auditor@company.com"
)
```

### Control Testing

**Requirement**: Regular testing of internal controls.

```python
# Document control test
test_result = sox.test_control(
    control_id="CTRL-2024-001",
    control_type="preventive",
    test_procedure="Verified segregation of duties in approval process",
    tester_id="auditor@company.com",
    test_result="pass",
    evidence={
        "sample_size": 25,
        "exceptions": 0,
        "test_date": "2024-01-15"
    }
)
```

### Compliance Report

```python
report = sox.generate_sox_report()

print(json.dumps(report, indent=2))
```

Output includes:
- Internal control status
- Control test statistics
- Access review completion
- Segregation of duties status
- Deficiencies found

API Endpoint:
```bash
GET /api/compliance/sox/controls
Authorization: Bearer AUDITOR_TOKEN
```

## RBAC & Access Control

### Role Hierarchy

```
Admin > Auditor > Accountant > Viewer
```

### Permissions Matrix

| Permission | Admin | Auditor | Accountant | Viewer |
|-----------|-------|---------|------------|--------|
| Read Financial Data | ✓ | ✓ | ✓ | ✓ |
| Write Financial Data | ✓ | | ✓ | |
| Create Journal Entries | ✓ | | ✓ | |
| Create Invoices | ✓ | | ✓ | |
| Read Audit Logs | ✓ | ✓ | ✓ | |
| Export Audit Logs | ✓ | ✓ | | |
| Manage Users | ✓ | | | |
| Manage Roles | ✓ | | | |
| System Configuration | ✓ | | | |
| Audit Review | ✓ | ✓ | | |

### Usage

```python
from src.compliance import RBACManager, Permission, Role

rbac = RBACManager()

# Assign role
rbac.assign_role("user@example.com", Role.ACCOUNTANT, assigned_by="admin@company.com")

# Check permission
has_permission = rbac.has_permission("user@example.com", Permission.WRITE_FINANCIALS)

# Check access with audit logging
access_granted = rbac.check_access(
    user_id="user@example.com",
    required_permission=Permission.WRITE_JOURNAL_ENTRIES,
    resource="journal_entry/JE-2024-001"
)
```

## Audit Trail

### Immutable Audit Logging

All audit entries are cryptographically linked using SHA-256 hashing (blockchain-style).

```python
from src.compliance import ImmutableAuditTrail

audit_trail = ImmutableAuditTrail()

# Add entry
entry = audit_trail.add_entry(
    event_type="data_modify",
    user_id="user@example.com",
    action="update_transaction",
    resource="transaction/TXN-2024-001",
    status="success",
    details={"amount_changed": "from 1000 to 1500"}
)

print(f"Entry hash: {entry['hash']}")
print(f"Previous hash: {entry['previous_hash']}")

# Verify chain integrity
verification = audit_trail.verify_chain()
if verification["valid"]:
    print("✓ Audit chain verified - no tampering detected")
else:
    print(f"⚠️ Chain broken: {verification['message']}")
```

### Retrieve Audit Entries

```python
# Get all entries for a user
user_entries = audit_trail.get_entries(user_id="user@example.com")

# Get entries for date range
date_entries = audit_trail.get_entries(
    start_date="2024-01-01T00:00:00Z",
    end_date="2024-01-31T23:59:59Z"
)
```

## Data Retention

### Retention Policies

```python
from src.compliance import DataRetentionManager, RetentionPolicy

retention_mgr = DataRetentionManager()

# Set retention policy
retention_mgr.set_policy(
    data_type="financial_records",
    retention_days=RetentionPolicy.SOX.value,  # 7 years
    user_id="admin@company.com"
)

# Apply retention policy (dry run)
result = retention_mgr.apply_retention_policy(
    data_type="financial_records",
    records=all_financial_records,
    user_id="admin@company.com",
    dry_run=True
)

print(f"Would delete {result['expired_records']} of {result['total_records']} records")

# Apply retention policy (actual deletion)
if input("Proceed with deletion? (yes/no): ") == "yes":
    result = retention_mgr.apply_retention_policy(
        data_type="financial_records",
        records=all_financial_records,
        user_id="admin@company.com",
        dry_run=False
    )
```

### Standard Retention Periods

| Regulation | Data Type | Retention Period |
|-----------|-----------|------------------|
| SOX | Financial Records | 7 years |
| HIPAA | PHI/Health Records | 6 years |
| GDPR | Personal Data | 1 year minimum |
| IRS | Tax Records | 7 years |

## Compliance Checklist

### Daily
- [ ] Monitor audit logs for suspicious activity
- [ ] Review failed authentication attempts
- [ ] Check system health and encryption status

### Weekly
- [ ] Review user access permissions
- [ ] Run breach detection scans
- [ ] Verify backup integrity

### Monthly
- [ ] Generate compliance reports (HIPAA, GDPR, SOX)
- [ ] Review and test internal controls
- [ ] Update consent records

### Quarterly
- [ ] Conduct access reviews
- [ ] Test disaster recovery procedures
- [ ] Review and update retention policies
- [ ] Security awareness training

### Annually
- [ ] Full SOX 404 compliance audit
- [ ] HIPAA risk assessment
- [ ] GDPR data protection impact assessment
- [ ] Penetration testing
- [ ] Update security policies

## Support

For compliance questions:
- Compliance Officer: compliance@cpafirm.com
- DPO (GDPR): dpo@cpafirm.com
- Security Officer: security@cpafirm.com
