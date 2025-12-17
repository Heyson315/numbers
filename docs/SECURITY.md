# Security Guidelines

## Overview

This document outlines security best practices for deploying and maintaining the CPA Firm AI Automation system.

## Authentication & Authorization

### JWT Token Management

1. **Token Expiration**
   - Default: 24 hours
   - Production recommendation: 1-8 hours
   - Implement refresh token mechanism

2. **Token Storage**
   - Never store tokens in localStorage (XSS vulnerable)
   - Use httpOnly cookies for web applications
   - Store securely in keychain/keystore for mobile apps

3. **Token Revocation**
   - Implement token blacklist for logged-out users
   - Use short expiration times
   - Rotate signing keys regularly

### Role-Based Access Control (RBAC)

```python
# Define roles and permissions
ROLES = {
    'admin': ['read', 'write', 'delete', 'audit', 'manage_users'],
    'accountant': ['read', 'write', 'audit'],
    'auditor': ['read', 'audit'],
    'viewer': ['read']
}
```

## Data Encryption

### Encryption at Rest

1. **Database Encryption**
   ```bash
   # PostgreSQL with encryption
   DATABASE_URL=postgresql://user:pass@localhost/db?sslmode=require
   ```

2. **File System Encryption**
   - Use encrypted volumes (e.g., LUKS, BitLocker)
   - Set proper file permissions (600 for sensitive files)
   - Encrypt backups

### Encryption in Transit

1. **HTTPS/TLS**
   ```python
   # Enable SSL in production
   uvicorn.run(
       app,
       host="0.0.0.0",
       port=8000,
       ssl_keyfile="./certs/key.pem",
       ssl_certfile="./certs/cert.pem"
   )
   ```

2. **Certificate Management**
   - Use Let's Encrypt for free SSL certificates
   - Implement certificate rotation
   - Monitor certificate expiration

## API Security

### Rate Limiting

```python
# Configure rate limits
@limiter.limit("5/minute")  # Login endpoints
@limiter.limit("20/minute")  # Data processing
@limiter.limit("100/minute") # Read operations
```

### Input Validation

1. **Sanitization**
   - Remove SQL injection characters
   - Validate file uploads
   - Check file size limits
   - Verify content types

2. **Validation Rules**
   ```python
   class InvoiceRequest(BaseModel):
       invoice_text: str = Field(..., min_length=10, max_length=10000)
       vendor_name: Optional[str] = Field(None, max_length=100)
   ```

## Audit Logging

### What to Log

1. **Authentication Events**
   - Successful logins
   - Failed login attempts
   - Logout events
   - Password changes

2. **Data Access**
   - Read operations on sensitive data
   - Data modifications
   - Data exports
   - Data deletions

3. **Security Events**
   - Failed authorization attempts
   - Rate limit violations
   - Suspicious patterns
   - Configuration changes

### Log Retention

```bash
# Recommended retention periods
AUDIT_LOG_RETENTION_DAYS=365  # 1 year minimum
DATA_RETENTION_YEARS=7        # Financial data (IRS requirement)
```

## Compliance

### Regulatory Requirements

1. **SOX Compliance** (Sarbanes-Oxley)
   - Maintain audit trails
   - Access controls
   - Change management

2. **GDPR** (if handling EU data)
   - Data protection by design
   - Right to be forgotten
   - Data portability

3. **PCI DSS** (if handling payment cards)
   - Network segmentation
   - Encryption of cardholder data
   - Regular security testing

## Security Checklist

### Pre-Deployment

- [ ] Generate secure random keys for production
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall rules
- [ ] Set up database encryption
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Implement backup strategy
- [ ] Set up monitoring and alerting
- [ ] Document security procedures
- [ ] Conduct security assessment

### Regular Maintenance

- [ ] Weekly log reviews
- [ ] Monthly dependency updates
- [ ] Quarterly security audits
- [ ] Annual penetration testing
- [ ] Regular backup testing
- [ ] Access review and cleanup

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [AICPA SOC 2](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report.html)
