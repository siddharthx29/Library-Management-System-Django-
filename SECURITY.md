# Security Policy

## Supported Versions

The following table lists the security support status for versions of this project:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

The development team takes security seriously. If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not create a public issue** on GitHub.
2. Send an email describing the vulnerability, affected components, steps to reproduce, and potential impact to `security-advisory@institution-library.example.org` (or contact the repository maintainers directly through private GitHub Advisory channels).
3. Please include detailed proof-of-concept steps, relevant environment details, and suggested remedies if available.

### Disclosure Policy

- You will receive an acknowledgement of your report within 48 business hours.
- A private fix will be developed, reviewed, and tested.
- Once a patched version is published, a security advisory will be released detailing the mitigation.

## Security Practices in this Codebase

- **Authentication & Authorization**: Role-based access control with server-side validation.
- **Data Protection**: Sensitive environment variables are separated from source code.
- **SQL Injection Prevention**: All queries use Django's ORM parameterized query engine and transaction locks (`select_for_update`).
- **Cross-Site Scripting (XSS)**: Strict template auto-escaping and sanitized output.
- **Cross-Site Request Forgery (CSRF)**: CSRF tokens strictly enforced on all state-changing endpoints.
- **Security Headers**: Standard defense-in-depth headers configured (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).
