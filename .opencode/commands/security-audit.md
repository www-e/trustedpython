# Security Audit

Run a comprehensive security audit using parallel agents:

1. **security-auditor**: Full OWASP Top 10 review
2. **security-scanner**: Scan specific files for vulnerabilities

Areas to check:
- Authentication flows (NextAuth, tRPC middleware)
- Input validation on all API endpoints
- SQL injection prevention in Prisma queries
- XSS prevention in UI components
- CSRF protection on forms
- Secure handling of payment webhooks
- Role-based access control enforcement
- Secret management (env variables)

Report findings with severity levels:
- 🔴 Critical (must fix immediately)
- 🟠 High (fix before next release)
- 🟡 Medium (fix in upcoming sprint)
- 🟢 Low (nice to have)

Provide specific file locations and code examples for each issue.