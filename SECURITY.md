# Security Policy

## Reporting a Vulnerability

We take the security of this CPA firm automation system seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues to:
- **Email:** security@cpafirm.com (replace with actual contact)
- **GitHub Security Advisory:** Use the "Security" tab → "Report a vulnerability"

### What to Include

Please provide:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact assessment
4. Suggested remediation (if any)
5. Your contact information for follow-up

### Response Timeline

- **Initial Response:** Within 48 hours
- **Triage & Assessment:** Within 5 business days
- **Fix & Disclosure:** Coordinated with reporter (typically 30-90 days)

### Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

### Security Best Practices

For deployment security, please review:
- [Security Guidelines](docs/SECURITY.md)
- [Audit Report](AUDIT_REPORT.md)
- Production deployment checklist below

## Production Deployment Checklist

Before deploying to production, ensure:

### Authentication & Authorization
- [ ] Replace demo credentials with database-backed authentication
- [ ] Enable multi-factor authentication (MFA)
- [ ] Implement password complexity requirements
- [ ] Configure JWT token expiration (≤ 8 hours recommended)
- [ ] Set up token refresh mechanism

### Data Protection
- [ ] Generate strong encryption keys (32+ bytes random)
- [ ] Store secrets in secure vault (AWS Secrets Manager, HashiCorp Vault)
- [ ] Enable database encryption at rest
- [ ] Configure TLS/SSL certificates (Let's Encrypt or commercial CA)
- [ ] Implement field-level encryption for SSNs/TINs

### Network Security
- [ ] Configure firewall rules (restrict to known IPs)
- [ ] Enable CORS only for trusted domains
- [ ] Use reverse proxy (nginx/Apache) with rate limiting
- [ ] Implement DDoS protection (Cloudflare, AWS Shield)
- [ ] Disable debug mode (`DEBUG=False`)

### Monitoring & Logging
- [ ] Configure audit log retention (365+ days)
- [ ] Set up log aggregation (ELK stack, Splunk)
- [ ] Enable security alerts (failed auth, anomalies)
- [ ] Implement uptime monitoring
- [ ] Configure backup and disaster recovery

### Compliance
- [ ] Document data retention policies (IRS: 7 years)
- [ ] Implement GDPR right-to-erasure API
- [ ] Configure data classification labels
- [ ] Schedule annual security audits
- [ ] Obtain SOC 2 certification (if selling to enterprises)

### Dependency Security
- [ ] Run `pip-audit` before each deployment
- [ ] Pin dependencies in `requirements.lock`
- [ ] Enable Dependabot or Renovate for automated updates
- [ ] Review licenses for compliance

### Testing
- [ ] Run all tests (`pytest tests/ -v`)
- [ ] Perform penetration testing
- [ ] Conduct code review for security issues
- [ ] Test disaster recovery procedures

## Known Security Considerations

### Demo Credentials (CRITICAL)
⚠️ **WARNING:** The default installation includes hardcoded demo credentials:
- Username: `demo`
- Password: `Demo123!`

**This MUST be removed before production deployment.** See `src/api.py:128`.

### Dependency Vulnerabilities
Current known vulnerabilities (as of audit date):
- `ecdsa` 0.19.1: GHSA-wj6h-64fc-37mp (review alternatives)
- `pip` < 25.3: GHSA-4xh5-x5gv-qwph (upgrade to 25.3+)

Run `pip-audit` regularly to check for new vulnerabilities.

### CPA-Specific Risks
This system handles sensitive financial data and PII. Additional considerations:
- **IRS Pub 1075:** Secure Federal Tax Information (FTI)
- **SOX Compliance:** Audit trail and access controls
- **GDPR:** Right to erasure and data portability
- **State Regulations:** Varies by jurisdiction

## Security Features

This system includes:
- ✅ AES-256 encryption at rest
- ✅ JWT authentication with expiration
- ✅ Role-based access control (RBAC)
- ✅ Comprehensive audit logging
- ✅ Rate limiting (brute force protection)
- ✅ Input validation (Pydantic models)
- ✅ SQL injection protection (SQLAlchemy ORM)

## Contact

For security questions or concerns:
- Open a GitHub issue with `security` label (non-sensitive)
- Email: security@cpafirm.com (sensitive)
- GitHub Security Advisory (vulnerabilities)

## Acknowledgments

We appreciate responsible disclosure from security researchers. Contributors will be acknowledged in release notes (with permission).
