# 🔒 Security Implementation Plan
## Smart Railway Ticketing System - Detailed Vulnerability Fixes

**Created:** 2026-04-02  
**Priority:** CRITICAL  
**Estimated Total Time:** 12-16 hours  

---

## Table of Contents

1. [Plan #1: HMAC Cookie Signing](#plan-1-hmac-cookie-signing)
2. [Plan #2: Security Headers Middleware](#plan-2-security-headers-middleware)
3. [Plan #3: CORS Hardening](#plan-3-cors-hardening)
4. [Plan #4: Input Validation Framework](#plan-4-input-validation-framework)
5. [Plan #5: Rate Limiting Enhancement](#plan-5-rate-limiting-enhancement)
6. [Plan #6: Debug Endpoints Protection](#plan-6-debug-endpoints-protection)
7. [Plan #7: HTTPS Enforcement](#plan-7-https-enforcement)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Checklist](#deployment-checklist)

---

## Plan #1: HMAC Cookie Signing

### 🎯 Objective
Implement HMAC (Hash-based Message Authentication Code) signing for session cookies to prevent tampering and session hijacking.

### 📊 Current State
- Session IDs stored in cookies without signature
- Attacker can modify session ID to hijack another user's session
- No integrity verification on cookie value

### ⏱️ Estimated Time: 2-3 hours

### 📋 Implementation Steps

#### Step 1.1: Create Cookie Signing Module

**File:** `functions/smart_railway_app_function/core/cookie_signer.py` (NEW)

```python
"""
Cookie Signing Module - HMAC-based cookie integrity verification
Implements secure cookie signing to prevent tampering.
"""

import hmac
import hashlib
import logging
from typing import Optional

from config import SESSION_SECRET

logger = logging.getLogger(__name__)


class CookieSigner:
    """
    HMAC-based cookie signer for session integrity.
    
    Uses HMAC-SHA256 to sign cookie values, preventing tampering.
    Format: {value}.{signature}
    """
    
    def __init__(self, secret: str):
        """
        Initialize cookie signer with secret key.
        
        Args:
            secret: Secret key for HMAC signing (should be SESSION_SECRET)
        """
        if not secret or len(secret) < 32:
            raise ValueError("Cookie signing requires secret key >= 32 characters")
        
        self.secret = secret.encode('utf-8')
        self.algorithm = hashlib.sha256
    
    def sign(self, value: str) -> str:
        """
        Sign a cookie value with HMAC.
        
        Args:
            value: Plain cookie value (e.g., session ID)
        
        Returns:
            Signed value in format: {value}.{signature}
        
        Example:
            >>> signer = CookieSigner("my-secret")
            >>> signer.sign("12345")
            "12345.a1b2c3d4e5f6..."
        """
        if not value:
            raise ValueError("Cannot sign empty value")
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret,
            value.encode('utf-8'),
            self.algorithm
        ).hexdigest()
        
        # Return value.signature format
        return f"{value}.{signature}"
    
    def unsign(self, signed_value: str) -> Optional[str]:
        """
        Verify and extract original value from signed cookie.
        
        Args:
            signed_value: Signed value in format {value}.{signature}
        
        Returns:
            Original value if signature valid, None if invalid/tampered
        
        Example:
            >>> signer = CookieSigner("my-secret")
            >>> signer.unsign("12345.a1b2c3d4e5f6...")
            "12345"
            >>> signer.unsign("12345.invalid")
            None
        """
        if not signed_value or '.' not in signed_value:
            logger.warning("Invalid signed cookie format (missing separator)")
            return None
        
        # Split value and signature
        parts = signed_value.rsplit('.', 1)
        if len(parts) != 2:
            logger.warning("Invalid signed cookie format (wrong parts count)")
            return None
        
        value, provided_signature = parts
        
        # Generate expected signature
        expected_signature = hmac.new(
            self.secret,
            value.encode('utf-8'),
            self.algorithm
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(expected_signature, provided_signature):
            logger.warning(f"Cookie signature mismatch - possible tampering detected")
            return None
        
        return value
    
    def verify(self, signed_value: str) -> bool:
        """
        Verify if signed value is valid without extracting value.
        
        Args:
            signed_value: Signed cookie value
        
        Returns:
            True if signature valid, False otherwise
        """
        return self.unsign(signed_value) is not None


# Global signer instance (initialized with SESSION_SECRET)
_signer: Optional[CookieSigner] = None


def get_signer() -> CookieSigner:
    """Get global cookie signer instance."""
    global _signer
    if _signer is None:
        _signer = CookieSigner(SESSION_SECRET)
    return _signer


def sign_cookie(value: str) -> str:
    """
    Sign a cookie value (convenience function).
    
    Args:
        value: Plain cookie value
    
    Returns:
        Signed value
    """
    return get_signer().sign(value)


def unsign_cookie(signed_value: str) -> Optional[str]:
    """
    Unsign and verify a cookie value (convenience function).
    
    Args:
        signed_value: Signed cookie value
    
    Returns:
        Original value if valid, None if invalid
    """
    return get_signer().unsign(signed_value)


def verify_cookie(signed_value: str) -> bool:
    """
    Verify cookie signature without extracting value (convenience function).
    
    Args:
        signed_value: Signed cookie value
    
    Returns:
        True if valid, False otherwise
    """
    return get_signer().verify(signed_value)
```

#### Step 1.2: Update Session Service to Use Signing

**File:** `functions/smart_railway_app_function/services/session_service.py`

**Changes:**

```python
# Add import at top
from core.cookie_signer import sign_cookie, unsign_cookie

# Modify create_session function (around line 128)
def create_session(...) -> Tuple[str, str]:
    """
    Create a new session.
    
    Returns:
        Tuple of (session_id, signed_session_id, csrf_token)
    """
    # Generate session ID (existing code)
    session_id = generate_session_id()
    
    # ... (existing session creation code)
    
    # Sign the session ID before returning
    signed_session_id = sign_cookie(session_id)
    
    return signed_session_id, csrf_token  # Return signed version


# Modify validate_session function (around line 205)
def validate_session(signed_session_id: str, ip_address: str, user_agent: str) -> Optional[Dict[str, Any]]:
    """
    Validate session with signature verification.
    
    Args:
        signed_session_id: Signed session ID from cookie
    """
    # Unsign and verify the session ID
    session_id = unsign_cookie(signed_session_id)
    
    if not session_id:
        logger.warning("Invalid session cookie signature - possible tampering")
        return None
    
    # Continue with existing validation logic...
    # Query database using unsigned session_id
    query = f"""
        SELECT Session_ID, User_ID, User_Email, User_Role, 
               IP_Address, User_Agent, CSRF_Token,
               Last_Accessed_At, Expires_At, Is_Active, CREATEDTIME
        FROM {TABLES['sessions']}
        WHERE Session_ID = {session_id}
        AND Is_Active = true
    """
    # ... rest of existing code
```

#### Step 1.3: Update Session Middleware

**File:** `functions/smart_railway_app_function/core/session_middleware.py`

**Changes:**

```python
# No changes needed - middleware calls validate_session which now handles unsigning
# But update the cookie setting in routes

# In _clear_session_cookie function (if needed)
def _clear_session_cookie(response):
    """Clear session cookie (already handles signed values)."""
    response.set_cookie(
        SESSION_COOKIE_NAME,
        '',  # Empty value
        max_age=0,
        # ... rest of config
    )
    return response
```

#### Step 1.4: Update Session Auth Routes

**File:** `functions/smart_railway_app_function/routes/session_auth.py`

**Changes:**

```python
# In session_login function (around line 420)
def session_login():
    # ... existing login logic ...
    
    # Create session (returns signed session ID now)
    signed_session_id, csrf_token = create_session(
        user_id=str(user['ROWID']),
        user_email=user_email,
        user_role=user_role,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Set cookie with SIGNED session ID
    response.set_cookie(
        SESSION_COOKIE_NAME,
        signed_session_id,  # ✅ Now signed
        max_age=SESSION_TIMEOUT_HOURS * 3600,
        httponly=SESSION_COOKIE_HTTPONLY,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path='/'
    )
    
    # Return CSRF token to client
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'data': {
            'csrf_token': csrf_token,
            'user': {...}
        }
    })
```

#### Step 1.5: Add Unit Tests

**File:** `functions/smart_railway_app_function/tests/test_cookie_signing.py` (NEW)

```python
"""
Unit tests for cookie signing module.
"""

import pytest
from core.cookie_signer import CookieSigner, sign_cookie, unsign_cookie


def test_sign_and_unsign():
    """Test basic sign/unsign flow."""
    signer = CookieSigner("test-secret-key-minimum-32-chars-long")
    
    # Sign a value
    signed = signer.sign("12345678901234567890")
    assert '.' in signed
    assert signed.startswith("12345678901234567890.")
    
    # Unsign should return original value
    unsigned = signer.unsign(signed)
    assert unsigned == "12345678901234567890"


def test_tampered_signature_rejected():
    """Test that tampered signatures are rejected."""
    signer = CookieSigner("test-secret-key-minimum-32-chars-long")
    
    signed = signer.sign("12345678901234567890")
    
    # Tamper with signature
    tampered = signed[:-5] + "xxxxx"
    
    # Should return None
    result = signer.unsign(tampered)
    assert result is None


def test_tampered_value_rejected():
    """Test that tampered values are rejected."""
    signer = CookieSigner("test-secret-key-minimum-32-chars-long")
    
    signed = signer.sign("12345678901234567890")
    parts = signed.split('.')
    
    # Tamper with value
    tampered = "99999999999999999999." + parts[1]
    
    # Should return None (signature won't match)
    result = signer.unsign(tampered)
    assert result is None


def test_invalid_format_rejected():
    """Test that invalid formats are rejected."""
    signer = CookieSigner("test-secret-key-minimum-32-chars-long")
    
    # No separator
    assert signer.unsign("12345678901234567890") is None
    
    # Empty value
    assert signer.unsign("") is None
    
    # Only separator
    assert signer.unsign(".") is None


def test_different_secrets_incompatible():
    """Test that different secrets produce different signatures."""
    signer1 = CookieSigner("secret-key-one-minimum-32-chars-long!")
    signer2 = CookieSigner("secret-key-two-minimum-32-chars-long!")
    
    signed1 = signer1.sign("12345678901234567890")
    
    # Signer2 should not be able to unsign signer1's cookies
    result = signer2.unsign(signed1)
    assert result is None
```

### ✅ Success Criteria

- [ ] Cookie signer module created with HMAC-SHA256
- [ ] Session IDs signed before storing in cookies
- [ ] Session IDs unsigned and verified on retrieval
- [ ] Unit tests pass (100% coverage)
- [ ] Tampered cookies rejected with warning logged
- [ ] Manual testing: tampered cookie returns 401

### 🧪 Testing Procedure

```bash
# 1. Run unit tests
cd functions/smart_railway_app_function
python -m pytest tests/test_cookie_signing.py -v

# 2. Manual test - Login and capture cookie
curl -X POST http://localhost:3000/server/smart_railway_app_function/session/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  -c cookies.txt

# 3. View signed cookie
cat cookies.txt | grep railway_sid

# 4. Tamper with cookie (change last 5 chars)
# Edit cookies.txt manually

# 5. Try to use tampered cookie (should fail)
curl -X GET http://localhost:3000/server/smart_railway_app_function/session/verify \
  -b cookies.txt

# Expected: 401 Unauthorized
# Expected log: "Cookie signature mismatch - possible tampering detected"
```

### 🔄 Rollback Strategy

If issues occur:

1. **Keep old code as backup:**
   ```bash
   git branch security-cookie-signing-backup
   ```

2. **Feature flag approach:**
   ```python
   # config.py
   ENABLE_COOKIE_SIGNING = os.getenv('ENABLE_COOKIE_SIGNING', 'true').lower() == 'true'
   
   # session_service.py
   if ENABLE_COOKIE_SIGNING:
       signed_session_id = sign_cookie(session_id)
   else:
       signed_session_id = session_id
   ```

3. **Rollback command:**
   ```bash
   git revert HEAD
   catalyst deploy
   ```

---

## Plan #2: Security Headers Middleware

### 🎯 Objective
Add comprehensive security headers to all HTTP responses to prevent XSS, clickjacking, MIME sniffing, and other attacks.

### 📊 Current State
- No security headers in responses
- Vulnerable to clickjacking (iframe embedding)
- Vulnerable to XSS attacks
- No Content Security Policy

### ⏱️ Estimated Time: 1-2 hours

### 📋 Implementation Steps

#### Step 2.1: Create Security Headers Module

**File:** `functions/smart_railway_app_function/core/security_headers.py` (NEW)

```python
"""
Security Headers Middleware
Adds comprehensive security headers to all HTTP responses.
"""

import os
from flask import request


class SecurityHeaders:
    """
    Security headers configuration and middleware.
    
    Implements OWASP recommended security headers.
    """
    
    def __init__(self, app=None, config=None):
        """
        Initialize security headers middleware.
        
        Args:
            app: Flask app instance (optional)
            config: Custom headers configuration (optional)
        """
        self.config = config or {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Register security headers with Flask app."""
        app.after_request(self.add_security_headers)
    
    def add_security_headers(self, response):
        """
        Add security headers to response.
        
        Headers added:
        - X-Frame-Options: Prevent clickjacking
        - X-Content-Type-Options: Prevent MIME sniffing
        - X-XSS-Protection: Enable XSS filter (legacy)
        - Referrer-Policy: Control referrer information
        - Permissions-Policy: Control browser features
        - Strict-Transport-Security: Enforce HTTPS (if secure)
        - Content-Security-Policy: Prevent XSS and injection attacks
        """
        
        # X-Frame-Options: Prevent clickjacking
        # Options: DENY | SAMEORIGIN | ALLOW-FROM uri
        if 'X-Frame-Options' not in response.headers:
            response.headers['X-Frame-Options'] = self.config.get(
                'x_frame_options', 'DENY'
            )
        
        # X-Content-Type-Options: Prevent MIME sniffing
        if 'X-Content-Type-Options' not in response.headers:
            response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection: Enable browser XSS filter (legacy, but still useful)
        if 'X-XSS-Protection' not in response.headers:
            response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy: Control referrer information
        # Options: no-referrer | no-referrer-when-downgrade | same-origin | 
        #          strict-origin | strict-origin-when-cross-origin
        if 'Referrer-Policy' not in response.headers:
            response.headers['Referrer-Policy'] = self.config.get(
                'referrer_policy', 'strict-origin-when-cross-origin'
            )
        
        # Permissions-Policy: Control browser features (replaces Feature-Policy)
        if 'Permissions-Policy' not in response.headers:
            permissions = self.config.get('permissions_policy', 
                'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
            )
            response.headers['Permissions-Policy'] = permissions
        
        # Strict-Transport-Security: Enforce HTTPS
        # Only add if connection is secure or behind HTTPS proxy
        is_secure = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
        is_production = os.getenv('APP_ENVIRONMENT') == 'production'
        
        if is_secure and is_production and 'Strict-Transport-Security' not in response.headers:
            # max-age: how long to remember HTTPS-only (1 year = 31536000)
            # includeSubDomains: apply to all subdomains
            # preload: submit to browser HSTS preload list
            hsts = self.config.get('hsts', 'max-age=31536000; includeSubDomains')
            response.headers['Strict-Transport-Security'] = hsts
        
        # Content-Security-Policy: Prevent XSS and injection attacks
        if 'Content-Security-Policy' not in response.headers:
            csp = self._build_csp()
            response.headers['Content-Security-Policy'] = csp
        
        return response
    
    def _build_csp(self) -> str:
        """
        Build Content Security Policy header.
        
        CSP prevents XSS by controlling which resources can be loaded.
        Customize this based on your application needs.
        """
        # Get custom CSP or use defaults
        if 'content_security_policy' in self.config:
            return self.config['content_security_policy']
        
        # Default CSP - ADJUST FOR YOUR APPLICATION
        csp_directives = [
            # default-src: Fallback for other directives
            "default-src 'self'",
            
            # script-src: JavaScript sources
            # 'unsafe-inline': Allows inline <script> (needed for React dev)
            # 'unsafe-eval': Allows eval() (needed for some libraries)
            # ⚠️ Remove unsafe-* in production if possible
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            
            # style-src: CSS sources
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            
            # font-src: Font sources
            "font-src 'self' data: https://fonts.gstatic.com",
            
            # img-src: Image sources
            "img-src 'self' data: https: blob:",
            
            # connect-src: AJAX, WebSocket, EventSource
            "connect-src 'self'",
            
            # frame-ancestors: Who can embed this page in iframe
            "frame-ancestors 'none'",
            
            # base-uri: Restrict <base> tag URLs
            "base-uri 'self'",
            
            # form-action: Restrict form submission targets
            "form-action 'self'",
            
            # upgrade-insecure-requests: Auto-upgrade HTTP to HTTPS
            # (only in production)
            # "upgrade-insecure-requests",
        ]
        
        return "; ".join(csp_directives)


def create_security_headers(app, config=None):
    """
    Factory function to create and attach security headers middleware.
    
    Args:
        app: Flask app instance
        config: Optional custom configuration
    
    Example:
        from core.security_headers import create_security_headers
        
        create_security_headers(app, {
            'x_frame_options': 'SAMEORIGIN',
            'referrer_policy': 'no-referrer'
        })
    """
    return SecurityHeaders(app, config)
```

#### Step 2.2: Integrate with Flask App

**File:** `functions/smart_railway_app_function/main.py`

**Changes:**

```python
# Add import at top (after other imports)
from core.security_headers import create_security_headers

def create_flask_app():
    """Create and configure the Flask application with all routes."""
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')
    
    # ── Security Headers (NEW) ────────────────────────────────────────────
    # Add comprehensive security headers to all responses
    security_config = {
        'x_frame_options': 'DENY',  # Prevent clickjacking
        'referrer_policy': 'strict-origin-when-cross-origin',
        'permissions_policy': 'geolocation=(), microphone=(), camera=(), payment=()',
        'hsts': 'max-age=31536000; includeSubDomains',
        # Custom CSP if needed (optional)
        # 'content_security_policy': "default-src 'self'; ..."
    }
    create_security_headers(app, security_config)
    
    # ── CORS Configuration ────────────────────────────────────────────────
    # (existing CORS code)
    
    # ... rest of existing code
```

#### Step 2.3: Test CSP Compatibility

**File:** `functions/smart_railway_app_function/tests/test_security_headers.py` (NEW)

```python
"""
Tests for security headers middleware.
"""

import pytest
from main import create_flask_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_flask_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_security_headers_present(client):
    """Test that all security headers are present."""
    response = client.get('/health')
    
    # Check all headers are present
    assert response.headers.get('X-Frame-Options') == 'DENY'
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-XSS-Protection') == '1; mode=block'
    assert 'Referrer-Policy' in response.headers
    assert 'Permissions-Policy' in response.headers
    assert 'Content-Security-Policy' in response.headers


def test_csp_header_valid(client):
    """Test that CSP header is valid."""
    response = client.get('/health')
    csp = response.headers.get('Content-Security-Policy')
    
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "script-src" in csp
    assert "style-src" in csp


def test_hsts_not_on_http(client):
    """Test that HSTS is not added on HTTP."""
    response = client.get('/health')
    
    # HSTS should not be present on non-HTTPS in development
    # (it's only added when request.is_secure or X-Forwarded-Proto: https)
    assert 'Strict-Transport-Security' not in response.headers
```

#### Step 2.4: Update Frontend for CSP Compatibility

**File:** `railway-app/public/index.html`

**Changes:**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    
    <!-- Add CSP meta tag for development (backup to header) -->
    <!-- Remove or adjust in production -->
    <meta http-equiv="Content-Security-Policy" 
          content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';">
    
    <title>Smart Railway Ticketing System</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
```

### ✅ Success Criteria

- [ ] Security headers module created
- [ ] Headers added to all responses
- [ ] CSP configured for React app
- [ ] Tests pass
- [ ] No console CSP violations in browser
- [ ] Security scan shows A+ rating

### 🧪 Testing Procedure

```bash
# 1. Run unit tests
python -m pytest tests/test_security_headers.py -v

# 2. Start server and check headers
catalyst serve

# 3. Check headers with curl
curl -I http://localhost:3000/server/smart_railway_app_function/health

# 4. Check in browser DevTools
# Open: http://localhost:3000
# DevTools → Network → Select any request → Headers
# Verify all security headers present

# 5. Check for CSP violations
# DevTools → Console
# Should NOT see: "Refused to execute inline script because it violates CSP"

# 6. Online security scan
# Visit: https://securityheaders.com
# Enter your deployed URL
# Target: A+ rating
```

### 🔄 Rollback Strategy

```python
# Feature flag in config.py
ENABLE_SECURITY_HEADERS = os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() == 'true'

# main.py
if ENABLE_SECURITY_HEADERS:
    create_security_headers(app, security_config)
```

---

## Plan #3: CORS Hardening

### 🎯 Objective
Fix permissive CORS configuration to prevent cross-origin attacks while maintaining legitimate cross-origin requests.

### 📊 Current State
- Reflects any origin in development mode
- Allows wildcard (*) with credentials
- No origin validation

### ⏱️ Estimated Time: 1 hour

### 📋 Implementation Steps

#### Step 3.1: Create CORS Configuration Module

**File:** `functions/smart_railway_app_function/core/cors_config.py` (NEW)

```python
"""
CORS Configuration Module
Secure Cross-Origin Resource Sharing configuration.
"""

import os
import logging
from flask import request
from typing import List, Optional

logger = logging.getLogger(__name__)


class CORSConfig:
    """
    CORS configuration manager with strict origin validation.
    """
    
    def __init__(self, allowed_origins: Optional[List[str]] = None):
        """
        Initialize CORS configuration.
        
        Args:
            allowed_origins: List of allowed origins (must be explicit)
        """
        self.allowed_origins = allowed_origins or self._get_default_origins()
        
        # Validate no wildcards when using credentials
        if '*' in self.allowed_origins:
            logger.error("CORS: Wildcard (*) not allowed with credentials")
            raise ValueError("Cannot use wildcard origin with credentials")
        
        logger.info(f"CORS: Allowed origins: {self.allowed_origins}")
    
    def _get_default_origins(self) -> List[str]:
        """Get default allowed origins from environment."""
        env_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
        
        if not env_origins:
            # Default for development
            is_dev = os.getenv('APP_ENVIRONMENT') == 'development'
            if is_dev:
                return [
                    'http://localhost:3000',
                    'http://localhost:3001',
                    'http://127.0.0.1:3000',
                    'http://127.0.0.1:3001',
                ]
            else:
                # Production MUST specify origins
                logger.error("CORS: No allowed origins configured in production!")
                return []
        
        # Parse comma-separated list
        origins = [o.strip() for o in env_origins.split(',') if o.strip()]
        
        # Validate each origin
        validated = []
        for origin in origins:
            if origin == '*':
                logger.error("CORS: Wildcard not allowed")
                continue
            
            if not origin.startswith(('http://', 'https://')):
                logger.warning(f"CORS: Invalid origin {origin} (missing scheme)")
                continue
            
            validated.append(origin)
        
        return validated
    
    def is_allowed(self, origin: Optional[str]) -> bool:
        """
        Check if origin is allowed.
        
        Args:
            origin: Origin header value
        
        Returns:
            True if origin is in allowed list
        """
        if not origin:
            return False
        
        # Exact match required
        is_allowed = origin in self.allowed_origins
        
        if not is_allowed:
            logger.warning(f"CORS: Blocked origin: {origin}")
        
        return is_allowed
    
    def get_allowed_origin(self, request_origin: Optional[str]) -> Optional[str]:
        """
        Get allowed origin for response header.
        
        Args:
            request_origin: Origin from request header
        
        Returns:
            Origin to set in Access-Control-Allow-Origin, or None if not allowed
        """
        if self.is_allowed(request_origin):
            return request_origin
        return None


def create_cors_middleware(app, allowed_origins: Optional[List[str]] = None):
    """
    Create CORS middleware for Flask app.
    
    Args:
        app: Flask app instance
        allowed_origins: List of allowed origins (optional)
    """
    cors_config = CORSConfig(allowed_origins)
    
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to response."""
        origin = request.headers.get('Origin')
        
        # Get allowed origin (validated)
        allowed_origin = cors_config.get_allowed_origin(origin)
        
        if allowed_origin:
            # Set specific origin (never *)
            response.headers['Access-Control-Allow-Origin'] = allowed_origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Always set these (even if origin not allowed)
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRF-Token'
        response.headers['Access-Control-Max-Age'] = '3600'
        response.headers['Vary'] = 'Origin'  # Important for caching
        
        return response
    
    @app.before_request
    def handle_preflight():
        """Handle CORS preflight OPTIONS requests."""
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            return add_cors_headers(response)
    
    return cors_config
```

#### Step 3.2: Update Main App

**File:** `functions/smart_railway_app_function/main.py`

**Replace existing CORS code (lines 62-94) with:**

```python
def create_flask_app():
    """Create and configure the Flask application with all routes."""
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')
    
    # ── Security Headers ──────────────────────────────────────────────────
    from core.security_headers import create_security_headers
    create_security_headers(app)
    
    # ── CORS Configuration (HARDENED) ─────────────────────────────────────
    from core.cors_config import create_cors_middleware
    
    # Get allowed origins from config
    from config import DEFAULT_ALLOWED_ORIGINS
    
    # Create CORS middleware with strict validation
    create_cors_middleware(app, DEFAULT_ALLOWED_ORIGINS)
    
    # Note: Removed old @app.after_request CORS handler
    
    # ── Error Handlers ────────────────────────────────────────────────────
    # (rest of existing code)
```

#### Step 3.3: Update Config

**File:** `functions/smart_railway_app_function/config.py`

**Update DEFAULT_ALLOWED_ORIGINS (lines 362-371):**

```python
# ══════════════════════════════════════════════════════════════════════════════
#  CORS & SECURITY
# ══════════════════════════════════════════════════════════════════════════════

# Determine environment
_is_production = os.getenv('APP_ENVIRONMENT') == 'production'

if _is_production:
    # Production: MUST specify explicit origins in environment variable
    # NEVER use wildcard in production
    _env_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    if not _env_origins:
        logger.warning("PRODUCTION: No CORS_ALLOWED_ORIGINS set! CORS will block all origins.")
    
    DEFAULT_ALLOWED_ORIGINS = [
        o.strip() for o in _env_origins.split(',') if o.strip()
    ]
else:
    # Development: Allow localhost only
    DEFAULT_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:3001',
        'http://localhost:5173',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:3001',
        'http://127.0.0.1:5173',
    ]
```

#### Step 3.4: Update Environment Variables

**File:** `functions/smart_railway_app_function/.env`

**Update line 50:**

```bash
# ══ CORS (comma-separated origins; NO wildcards) ═══════════════
# Production: Add your actual frontend domain
CORS_ALLOWED_ORIGINS=https://smart-railway-app.onslate.in,https://railway-ticketing-app.onslate.in
```

### ✅ Success Criteria

- [ ] CORS module created with strict validation
- [ ] Wildcard origins rejected
- [ ] Unknown origins blocked and logged
- [ ] Preflight requests handled
- [ ] Vary: Origin header added
- [ ] Tests pass

### 🧪 Testing Procedure

```bash
# 1. Test allowed origin
curl -X OPTIONS http://localhost:3000/server/smart_railway_app_function/health \
  -H "Origin: http://localhost:3000" \
  -v

# Expected: Access-Control-Allow-Origin: http://localhost:3000

# 2. Test blocked origin
curl -X OPTIONS http://localhost:3000/server/smart_railway_app_function/health \
  -H "Origin: http://evil-site.com" \
  -v

# Expected: No Access-Control-Allow-Origin header
# Expected log: "CORS: Blocked origin: http://evil-site.com"

# 3. Test in browser
# Open DevTools → Console
# Try to make request from different origin
fetch('http://localhost:3000/server/smart_railway_app_function/health', {
  credentials: 'include'
}).then(r => console.log(r.status))

# Should work if same origin, fail if different
```

---

## Plan #4: Input Validation Framework

### 🎯 Objective
Implement comprehensive input validation to prevent SQL injection, XSS, and other injection attacks.

### 📊 Current State
- No input validation or sanitization
- User input directly used in database queries
- High risk of SQL injection

### ⏱️ Estimated Time: 3-4 hours

### 📋 Implementation Steps

#### Step 4.1: Create Input Validator Module

**File:** `functions/smart_railway_app_function/core/input_validator.py` (NEW)

```python
"""
Input Validation Module
Provides validation and sanitization for all user inputs.
"""

import re
import logging
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class InputValidator:
    """
    Input validation and sanitization utilities.
    
    Prevents SQL injection, XSS, and other injection attacks.
    """
    
    # Regex patterns for common validations
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^\+?[1-9]\d{9,14}$',  # E.164 format
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'alpha': r'^[a-zA-Z]+$',
        'numeric': r'^\d+$',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        'slug': r'^[a-z0-9-]+$',
        'username': r'^[a-zA-Z0-9_-]{3,20}$',
    }
    
    # SQL injection patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(--|\#|\/\*|\*\/)",  # SQL comments
        r"(\bEXEC\b|\bEXECUTE\b)",
        r"(\bxp_\w+)",  # SQL Server extended procedures
        r"(;.*(DROP|ALTER|CREATE|INSERT|UPDATE|DELETE))",
    ]
    
    @classmethod
    def validate_email(cls, email: str, required: bool = True) -> Optional[str]:
        """
        Validate email address.
        
        Args:
            email: Email to validate
            required: If True, raises error if empty
        
        Returns:
            Validated email (lowercase)
        
        Raises:
            ValidationError: If validation fails
        """
        if not email:
            if required:
                raise ValidationError('email', 'Email is required')
            return None
        
        email = email.strip().lower()
        
        if len(email) > 255:
            raise ValidationError('email', 'Email too long (max 255 characters)')
        
        if not re.match(cls.PATTERNS['email'], email, re.IGNORECASE):
            raise ValidationError('email', 'Invalid email format')
        
        return email
    
    @classmethod
    def validate_string(cls, 
                       value: str, 
                       field_name: str,
                       min_length: int = 0,
                       max_length: int = 255,
                       pattern: Optional[str] = None,
                       required: bool = True) -> Optional[str]:
        """
        Validate string field.
        
        Args:
            value: String to validate
            field_name: Name of field (for error messages)
            min_length: Minimum length
            max_length: Maximum length
            pattern: Regex pattern name (from PATTERNS dict)
            required: If True, raises error if empty
        
        Returns:
            Validated string (stripped)
        
        Raises:
            ValidationError: If validation fails
        """
        if not value:
            if required:
                raise ValidationError(field_name, f'{field_name} is required')
            return None
        
        value = value.strip()
        
        if len(value) < min_length:
            raise ValidationError(field_name, 
                f'{field_name} must be at least {min_length} characters')
        
        if len(value) > max_length:
            raise ValidationError(field_name, 
                f'{field_name} must be at most {max_length} characters')
        
        if pattern and pattern in cls.PATTERNS:
            if not re.match(cls.PATTERNS[pattern], value):
                raise ValidationError(field_name, 
                    f'{field_name} has invalid format')
        
        return value
    
    @classmethod
    def validate_integer(cls,
                        value: Any,
                        field_name: str,
                        min_value: Optional[int] = None,
                        max_value: Optional[int] = None,
                        required: bool = True) -> Optional[int]:
        """
        Validate integer field.
        
        Args:
            value: Value to validate
            field_name: Name of field
            min_value: Minimum value
            max_value: Maximum value
            required: If True, raises error if None
        
        Returns:
            Validated integer
        
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if required:
                raise ValidationError(field_name, f'{field_name} is required')
            return None
        
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, f'{field_name} must be an integer')
        
        if min_value is not None and value < min_value:
            raise ValidationError(field_name, 
                f'{field_name} must be at least {min_value}')
        
        if max_value is not None and value > max_value:
            raise ValidationError(field_name, 
                f'{field_name} must be at most {max_value}')
        
        return value
    
    @classmethod
    def validate_date(cls,
                     value: str,
                     field_name: str,
                     format: str = '%Y-%m-%d',
                     required: bool = True) -> Optional[datetime]:
        """
        Validate date field.
        
        Args:
            value: Date string to validate
            field_name: Name of field
            format: Expected date format
            required: If True, raises error if empty
        
        Returns:
            Parsed datetime object
        
        Raises:
            ValidationError: If validation fails
        """
        if not value:
            if required:
                raise ValidationError(field_name, f'{field_name} is required')
            return None
        
        try:
            return datetime.strptime(value, format)
        except ValueError:
            raise ValidationError(field_name, 
                f'{field_name} must be in format {format}')
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """
        Detect potential SQL injection attempts.
        
        Args:
            value: String to check
        
        Returns:
            True if SQL injection pattern detected
        """
        if not value:
            return False
        
        value_upper = value.upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected: {pattern}")
                return True
        
        return False
    
    @classmethod
    def sanitize_sql_string(cls, value: str) -> str:
        """
        Sanitize string for SQL queries (escape single quotes).
        
        IMPORTANT: This is NOT a substitute for parameterized queries!
        Use this only for display/logging purposes.
        
        Args:
            value: String to sanitize
        
        Returns:
            Sanitized string
        """
        if not value:
            return ''
        
        # Escape single quotes (SQL standard)
        return value.replace("'", "''")
    
    @classmethod
    def validate_booking_id(cls, booking_id: str) -> str:
        """
        Validate booking ID format.
        
        Args:
            booking_id: Booking ID to validate
        
        Returns:
            Validated booking ID
        
        Raises:
            ValidationError: If validation fails
        """
        if not booking_id:
            raise ValidationError('booking_id', 'Booking ID is required')
        
        # Booking IDs should be alphanumeric with dashes/underscores
        if not re.match(r'^[A-Z0-9\-_]{10,20}$', booking_id):
            raise ValidationError('booking_id', 'Invalid booking ID format')
        
        # Check for SQL injection
        if cls.detect_sql_injection(booking_id):
            raise ValidationError('booking_id', 'Invalid characters in booking ID')
        
        return booking_id
    
    @classmethod
    def validate_train_number(cls, train_number: Any) -> int:
        """
        Validate train number.
        
        Args:
            train_number: Train number to validate
        
        Returns:
            Validated train number as integer
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            train_number = int(train_number)
        except (ValueError, TypeError):
            raise ValidationError('train_number', 'Train number must be numeric')
        
        if train_number < 10000 or train_number > 99999:
            raise ValidationError('train_number', 
                'Train number must be 5 digits (10000-99999)')
        
        return train_number
    
    @classmethod
    def validate_dict(cls, data: Dict[str, Any], schema: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Validate dictionary against schema.
        
        Args:
            data: Data dictionary to validate
            schema: Validation schema
        
        Returns:
            Validated data dictionary
        
        Example schema:
            {
                'email': {'type': 'email', 'required': True},
                'age': {'type': 'integer', 'min_value': 0, 'max_value': 150},
                'name': {'type': 'string', 'min_length': 2, 'max_length': 50}
            }
        """
        validated = {}
        
        for field, rules in schema.items():
            value = data.get(field)
            field_type = rules.get('type', 'string')
            required = rules.get('required', False)
            
            try:
                if field_type == 'email':
                    validated[field] = cls.validate_email(value, required=required)
                
                elif field_type == 'string':
                    validated[field] = cls.validate_string(
                        value, field,
                        min_length=rules.get('min_length', 0),
                        max_length=rules.get('max_length', 255),
                        pattern=rules.get('pattern'),
                        required=required
                    )
                
                elif field_type == 'integer':
                    validated[field] = cls.validate_integer(
                        value, field,
                        min_value=rules.get('min_value'),
                        max_value=rules.get('max_value'),
                        required=required
                    )
                
                elif field_type == 'date':
                    validated[field] = cls.validate_date(
                        value, field,
                        format=rules.get('format', '%Y-%m-%d'),
                        required=required
                    )
                
            except ValidationError:
                raise
        
        return validated


# Convenience decorator for route validation
def validate_input(schema: Dict[str, Dict]):
    """
    Decorator to validate request JSON against schema.
    
    Usage:
        @app.route('/api/users', methods=['POST'])
        @validate_input({
            'email': {'type': 'email', 'required': True},
            'age': {'type': 'integer', 'min_value': 18}
        })
        def create_user():
            data = request.validated_data  # Already validated
            ...
    """
    def decorator(f):
        from functools import wraps
        from flask import request, jsonify
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                data = request.get_json() or {}
                validated = InputValidator.validate_dict(data, schema)
                request.validated_data = validated
                return f(*args, **kwargs)
            
            except ValidationError as e:
                return jsonify({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': {e.field: e.message}
                }), 400
        
        return wrapped
    return decorator
```

#### Step 4.2: Apply Validation to Routes

**File:** `functions/smart_railway_app_function/routes/session_auth.py`

**Example integration:**

```python
from core.input_validator import InputValidator, ValidationError, validate_input

# Update session_login route
@session_auth_blueprint.route('/login', methods=['POST'])
@validate_input({
    'email': {'type': 'email', 'required': True},
    'password': {'type': 'string', 'required': True, 'min_length': 8, 'max_length': 128}
})
def session_login():
    """User login with session creation."""
    # Use validated data
    data = request.validated_data
    user_email = data['email']  # Already validated and lowercase
    password = data['password']  # Already validated length
    
    # ... rest of login logic
```

### ✅ Success Criteria

- [ ] Input validator module created
- [ ] SQL injection detection implemented
- [ ] All routes apply validation
- [ ] Tests pass
- [ ] SQL injection attempts logged

### 🧪 Testing Procedure

```bash
# 1. Test SQL injection detection
python -c "
from core.input_validator import InputValidator
assert InputValidator.detect_sql_injection(\"' OR '1'='1\") == True
assert InputValidator.detect_sql_injection(\"normal@email.com\") == False
print('SQL injection detection working')
"

# 2. Test validation decorator
curl -X POST http://localhost:3000/server/smart_railway_app_function/session/login \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid","password":"short"}'

# Expected: 400 Bad Request with validation errors

# 3. Test SQL injection attempt
curl -X POST http://localhost:3000/server/smart_railway_app_function/session/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com OR 1=1--","password":"password"}'

# Expected: 400 Bad Request
# Expected log: "SQL injection attempt detected"
```

---

## (Continued in next sections...)

---

## Testing Strategy

### Integration Testing

Create comprehensive integration tests:

**File:** `functions/smart_railway_app_function/tests/test_security_integration.py`

```python
"""
Integration tests for security features.
"""

import pytest
from main import create_flask_app


@pytest.fixture
def client():
    app = create_flask_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_signed_cookie_flow(client):
    """Test complete login flow with signed cookies."""
    # Login
    response = client.post('/session/login', json={
        'email': 'test@example.com',
        'password': 'TestPassword123!'
    })
    
    assert response.status_code == 200
    
    # Get cookie
    cookies = response.headers.getlist('Set-Cookie')
    session_cookie = [c for c in cookies if 'railway_sid' in c][0]
    
    # Verify cookie is signed (contains dot)
    assert '.' in session_cookie
    
    # Use cookie for authenticated request
    response = client.get('/session/verify',
                         headers={'Cookie': session_cookie})
    
    assert response.status_code == 200


def test_tampered_cookie_rejected(client):
    """Test that tampered cookies are rejected."""
    # Login first
    response = client.post('/session/login', json={
        'email': 'test@example.com',
        'password': 'TestPassword123!'
    })
    
    cookie = response.headers.getlist('Set-Cookie')[0]
    
    # Tamper with cookie
    tampered = cookie.replace(cookie[-10:-5], 'xxxxx')
    
    # Try to use tampered cookie
    response = client.get('/session/verify',
                         headers={'Cookie': tampered})
    
    assert response.status_code == 401


def test_security_headers_present(client):
    """Test all security headers are present."""
    response = client.get('/health')
    
    assert 'X-Frame-Options' in response.headers
    assert 'Content-Security-Policy' in response.headers
    assert 'X-Content-Type-Options' in response.headers


def test_cors_blocks_unknown_origin(client):
    """Test CORS blocks unknown origins."""
    response = client.options('/health',
                             headers={'Origin': 'http://evil.com'})
    
    # Should not have CORS header for unknown origin
    assert 'Access-Control-Allow-Origin' not in response.headers


def test_input_validation_blocks_injection(client):
    """Test input validation blocks SQL injection."""
    response = client.post('/session/login', json={
        'email': "' OR '1'='1",
        'password': 'password'
    })
    
    assert response.status_code == 400
```

### Security Scanning

```bash
# 1. Run security scanners
pip install bandit safety
bandit -r functions/smart_railway_app_function
safety check

# 2. Check for secrets in code
pip install detect-secrets
detect-secrets scan functions/

# 3. OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:3000
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Security scan passes
- [ ] No hardcoded secrets
- [ ] `.env` in `.gitignore`
- [ ] CORS configured for production domain
- [ ] HTTPS enforced
- [ ] Session timeout reduced
- [ ] Debug endpoints disabled
- [ ] Rate limiting enabled

### Deployment Steps

```bash
# 1. Backup current deployment
catalyst deploy --backup

# 2. Update environment variables
# In Catalyst Console → Environment Variables
SESSION_SECRET=<your-secret>
CORS_ALLOWED_ORIGINS=https://your-domain.com
APP_ENVIRONMENT=production

# 3. Deploy
cd railway-app && npm run build
catalyst deploy

# 4. Verify deployment
curl -I https://your-domain.com/server/smart_railway_app_function/health

# 5. Check security headers
curl -I https://your-domain.com | grep -i "x-frame"

# 6. Test login flow
curl -X POST https://your-domain.com/server/smart_railway_app_function/session/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  -v

# 7. Monitor logs
catalyst logs --follow
```

### Post-Deployment

- [ ] Security headers verified
- [ ] CORS working
- [ ] Login flow working
- [ ] Cookies signed and secure
- [ ] HTTPS enforced
- [ ] No console errors
- [ ] Audit logs working
- [ ] Rate limiting active

---

## Summary

This implementation plan covers the 7 most critical security vulnerabilities:

1. ✅ **HMAC Cookie Signing** - 2-3 hours
2. ✅ **Security Headers** - 1-2 hours
3. ✅ **CORS Hardening** - 1 hour
4. ✅ **Input Validation** - 3-4 hours
5. ⏳ **Rate Limiting** - 1-2 hours (see full plan)
6. ⏳ **Debug Endpoints** - 30 minutes (see full plan)
7. ⏳ **HTTPS Enforcement** - 30 minutes (see full plan)

**Total Estimated Time:** 12-16 hours

**Recommended Order:**
1. Cookie signing (highest impact)
2. Input validation (prevents SQL injection)
3. Security headers (quick win)
4. CORS hardening (prevent CSRF)
5. Rate limiting (prevent brute force)
6. Debug endpoints (information disclosure)
7. HTTPS enforcement (transport security)

**Next Steps:**
1. Review this plan with your team
2. Schedule implementation sprints
3. Implement in priority order
4. Test thoroughly after each fix
5. Deploy incrementally with rollback plan
6. Monitor for issues

---

**Questions or need clarification on any section?** Let me know which vulnerabilities you want to tackle first!
