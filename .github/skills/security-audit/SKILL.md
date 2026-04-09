---
name: security-audit
description: "Run a security audit on the Smart Railway backend. Use when reviewing authentication logic, checking for session vulnerabilities, or auditing routes in core/ and routes/."
argument-hint: "Which specific file or domain should I audit first?"
---

# 🛡️ Security Audit Workflow

This skill performs a multi-stage security analysis of the Smart Railway backend, focusing on the authentication layer and API routing security.

## 🎯 Target Areas
- **Authentication Core**: [functions/smart_railway_app_function/core/security.py](functions/smart_railway_app_function/core/security.py) (Hashing, Signing)
- **Middleware**: [functions/smart_railway_app_function/core/session_middleware.py](functions/smart_railway_app_function/core/session_middleware.py) (Decorators)
- **Protected Routes**: [functions/smart_railway_app_function/routes/](functions/smart_railway_app_function/routes/) (Auth/Admin checks)

## 🛠️ Audit Steps

### 1. Static Analysis (SonarQube)
Run SonarQube analysis on the core security components to catch common vulnerabilities:
- Use `sonarqube_analyze_file` on `core/security.py` and `core/session_middleware.py`.
- Use `sonarqube_list_potential_security_issues` to identify Taint Vulnerabilities or Hotspots in [routes/auth.py](functions/smart_railway_app_function/routes/auth.py).

### 2. Authentication Bypass Check
Verify that all administrative and employee routes are correctly decorated:
- Check for `@require_session_admin` or `@require_session_employee` in [routes/admin_employees.py](functions/smart_railway_app_function/routes/admin_employees.py) and [routes/admin_users.py](functions/smart_railway_app_function/routes/admin_users.py).
- Ensure no sensitive data is leaked in the `except` blocks of the route handlers.

### 3. Session Hardening Review
- Verify HMAC cookie signing logic in [core/cookie_signer.py](functions/smart_railway_app_function/core/cookie_signer.py).
- Confirm CSRF protection and Secure/HttpOnly flags are enforced in [core/security_headers.py](functions/smart_railway_app_function/core/security_headers.py).

### 4. Database Safety (ZCQL)
- Audit repositories in `repositories/*.py` to ensure `CriteriaBuilder` is used for all user-supplied inputs.
- Cross-reference with the [ZCQL Safety Instruction](.github/instructions/zcql-safety.instructions.md).

## 📊 Output Requirements
The audit must produce a summary containing:
1. **Critical Vulnerabilities**: Immediate action required.
2. **Security Hotspots**: Potential risks needing manual verification.
3. **Recommended Fixes**: Specific code changes or configuration updates.
4. **Pass/Fail Status**: For each target area defined above.
