# 🔒 Security Implementation Plan (Part 2)
## Plans #5-7: Rate Limiting, Debug Protection, HTTPS Enforcement

---

## Plan #5: Rate Limiting Enhancement

### 🎯 Objective
Enhance rate limiting to prevent brute force attacks on authentication endpoints and implement distributed rate limiting.

### 📊 Current State
- Basic in-memory rate limiter exists
- Not applied to session auth endpoints
- Resets on server restart
- Doesn't work across multiple instances

### ⏱️ Estimated Time: 2-3 hours

### 📋 Implementation Steps

#### Step 5.1: Enhanced Rate Limiter Module

**File:** `functions/smart_railway_app_function/core/rate_limiter.py` (NEW)

```python
"""
Enhanced Rate Limiter with Sliding Window Algorithm
Supports both in-memory and distributed (Catalyst Cache) backends.
"""

import time
import logging
import threading
from typing import Optional, Dict, List, Callable
from functools import wraps
from collections import defaultdict

from flask import request, jsonify, g

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


class InMemoryRateLimiter:
    """
    In-memory rate limiter with sliding window algorithm.
    
    Good for: Development, single-instance deployments
    Limitations: Resets on restart, doesn't sync across instances
    """
    
    def __init__(self):
        self._store: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, Optional[int]]:
        """
        Check if request should be allowed.
        
        Args:
            key: Rate limit key (e.g., "login:192.168.1.1")
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds
        
        with self._lock:
            # Remove expired timestamps
            self._store[key] = [ts for ts in self._store[key] if ts > cutoff]
            
            # Check if limit exceeded
            if len(self._store[key]) >= max_requests:
                # Calculate retry_after
                oldest = self._store[key][0]
                retry_after = int(oldest + window_seconds - now) + 1
                return False, retry_after
            
            # Add current timestamp
            self._store[key].append(now)
            return True, None
    
    def reset(self, key: str):
        """Reset rate limit for key."""
        with self._lock:
            self._store.pop(key, None)
    
    def get_stats(self, key: str, window_seconds: int) -> Dict:
        """Get rate limit stats for key."""
        now = time.time()
        cutoff = now - window_seconds
        
        with self._lock:
            count = len([ts for ts in self._store[key] if ts > cutoff])
            return {
                'key': key,
                'current_count': count,
                'window_seconds': window_seconds
            }


class CatalystCacheRateLimiter:
    """
    Distributed rate limiter using Zoho Catalyst Cache.
    
    Good for: Production, multi-instance deployments
    Features: Persists across restarts, syncs across instances
    """
    
    def __init__(self):
        self._cache = None
        self._cache_segment = "rate_limiter"
        self._initialized = False
    
    def _init_cache(self):
        """Initialize Catalyst Cache (lazy loading)."""
        if self._initialized:
            return
        
        try:
            from repositories.cloudscale_repository import get_catalyst_app
            catalyst_app = get_catalyst_app()
            
            if catalyst_app:
                self._cache = catalyst_app.cache()
                self._initialized = True
                logger.info("Catalyst Cache rate limiter initialized")
            else:
                logger.warning("Catalyst Cache not available, using in-memory fallback")
        
        except Exception as e:
            logger.error(f"Failed to initialize Catalyst Cache: {e}")
    
    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, Optional[int]]:
        """
        Check if request should be allowed using Catalyst Cache.
        
        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        self._init_cache()
        
        if not self._initialized:
            # Fallback to in-memory
            logger.debug("Using in-memory rate limiter fallback")
            return InMemoryRateLimiter().check_rate_limit(key, max_requests, window_seconds)
        
        try:
            cache_key = f"{self._cache_segment}:{key}"
            now = time.time()
            
            # Get existing timestamps from cache
            cached_data = self._cache.get_value(cache_key)
            timestamps = cached_data['value'] if cached_data else []
            
            # Remove expired timestamps
            timestamps = [ts for ts in timestamps if ts > now - window_seconds]
            
            # Check if limit exceeded
            if len(timestamps) >= max_requests:
                oldest = timestamps[0]
                retry_after = int(oldest + window_seconds - now) + 1
                return False, retry_after
            
            # Add current timestamp
            timestamps.append(now)
            
            # Store back in cache (TTL = window_seconds + 60)
            self._cache.put_value(
                cache_key,
                timestamps,
                ttl=window_seconds + 60
            )
            
            return True, None
        
        except Exception as e:
            logger.error(f"Rate limiter cache error: {e}")
            # Allow request on error (fail open)
            return True, None
    
    def reset(self, key: str):
        """Reset rate limit for key."""
        if not self._initialized:
            return
        
        try:
            cache_key = f"{self._cache_segment}:{key}"
            self._cache.delete_value(cache_key)
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")


# Global rate limiter instance
_rate_limiter: Optional[InMemoryRateLimiter | CatalystCacheRateLimiter] = None


def get_rate_limiter():
    """Get global rate limiter instance."""
    global _rate_limiter
    
    if _rate_limiter is None:
        # Try to use Catalyst Cache in production
        import os
        if os.getenv('APP_ENVIRONMENT') == 'production':
            _rate_limiter = CatalystCacheRateLimiter()
        else:
            _rate_limiter = InMemoryRateLimiter()
    
    return _rate_limiter


def rate_limit(max_requests: int = 10, 
               window_seconds: int = 900,
               key_func: Optional[Callable] = None):
    """
    Rate limit decorator for Flask routes.
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        key_func: Function to generate rate limit key (default: IP-based)
    
    Usage:
        @app.route('/api/login', methods=['POST'])
        @rate_limit(max_requests=5, window_seconds=900)
        def login():
            ...
    
    Custom key function:
        def email_based_key():
            data = request.get_json()
            return f"login:{data.get('email', 'unknown')}"
        
        @rate_limit(max_requests=5, key_func=email_based_key)
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                # Default: IP-based
                ip = request.remote_addr or 'unknown'
                key = f"{f.__name__}:{ip}"
            
            # Check rate limit
            limiter = get_rate_limiter()
            is_allowed, retry_after = limiter.check_rate_limit(
                key, max_requests, window_seconds
            )
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded: {key} (retry after {retry_after}s)")
                
                # Log to audit if user context available
                if hasattr(g, 'user_email'):
                    try:
                        from services.session_service import log_audit_event
                        log_audit_event(
                            event_type='rate_limit_exceeded',
                            user_id=getattr(g, 'user_id', None),
                            user_email=getattr(g, 'user_email', None),
                            ip_address=request.remote_addr,
                            details={
                                'endpoint': f.__name__,
                                'key': key,
                                'retry_after': retry_after
                            },
                            severity='warning'
                        )
                    except:
                        pass
                
                return jsonify({
                    'status': 'error',
                    'message': f'Too many requests. Please try again after {retry_after} seconds.',
                    'retry_after': retry_after
                }), 429
            
            return f(*args, **kwargs)
        
        return wrapped
    return decorator


def rate_limit_by_user(max_requests: int = 10, window_seconds: int = 900):
    """
    Rate limit by user ID (for authenticated endpoints).
    
    Usage:
        @require_session
        @rate_limit_by_user(max_requests=10, window_seconds=60)
        def create_booking():
            ...
    """
    def key_func():
        user_id = getattr(g, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        # Fallback to IP if no user
        return f"ip:{request.remote_addr}"
    
    return rate_limit(max_requests, window_seconds, key_func)


def rate_limit_by_email(max_requests: int = 5, window_seconds: int = 900):
    """
    Rate limit by email (for login/registration endpoints).
    
    Usage:
        @rate_limit_by_email(max_requests=5, window_seconds=900)
        def login():
            data = request.get_json()
            email = data.get('email')
            ...
    """
    def key_func():
        data = request.get_json() or {}
        email = data.get('email', 'unknown')
        return f"email:{email}"
    
    return rate_limit(max_requests, window_seconds, key_func)
```

#### Step 5.2: Apply Rate Limiting to Auth Routes

**File:** `functions/smart_railway_app_function/routes/session_auth.py`

**Add rate limiting to sensitive endpoints:**

```python
from core.rate_limiter import rate_limit, rate_limit_by_email, rate_limit_by_user

# Login endpoint - 5 attempts per 15 minutes per email
@session_auth_blueprint.route('/login', methods=['POST'])
@rate_limit_by_email(max_requests=5, window_seconds=900)
def session_login():
    """User login with session creation."""
    # ... existing code


# Registration endpoint - 3 registrations per hour per IP
@session_auth_blueprint.route('/register', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=3600)
def session_register():
    """User registration with OTP verification."""
    # ... existing code


# OTP verification - 3 attempts per 10 minutes per email
@session_auth_blueprint.route('/verify-otp', methods=['POST'])
@rate_limit_by_email(max_requests=3, window_seconds=600)
def verify_otp():
    """Verify OTP for registration."""
    # ... existing code


# Password reset request - 3 requests per hour per email
@session_auth_blueprint.route('/forgot-password', methods=['POST'])
@rate_limit_by_email(max_requests=3, window_seconds=3600)
def forgot_password():
    """Request password reset."""
    # ... existing code


# Password change - 5 attempts per hour per user
@session_auth_blueprint.route('/change-password', methods=['POST'])
@require_session
@rate_limit_by_user(max_requests=5, window_seconds=3600)
def session_change_password():
    """Change password for authenticated user."""
    # ... existing code
```

#### Step 5.3: Add Rate Limit Status Endpoint

**File:** `functions/smart_railway_app_function/routes/session_auth.py`

```python
@session_auth_blueprint.route('/rate-limit/status', methods=['GET'])
@require_session
def rate_limit_status():
    """
    Get rate limit status for current user.
    
    Returns:
        Rate limit information
    """
    from core.rate_limiter import get_rate_limiter
    
    user_id = g.user_id
    limiter = get_rate_limiter()
    
    # Check various rate limit keys
    keys = {
        'login': f"email:{g.user_email}",
        'user_actions': f"user:{user_id}",
        'ip_actions': f"ip:{request.remote_addr}"
    }
    
    status = {}
    for name, key in keys.items():
        stats = limiter.get_stats(key, window_seconds=900)
        status[name] = stats
    
    return jsonify({
        'status': 'success',
        'data': status
    })
```

#### Step 5.4: Unit Tests

**File:** `functions/smart_railway_app_function/tests/test_rate_limiter.py` (NEW)

```python
"""
Unit tests for rate limiter.
"""

import pytest
import time
from core.rate_limiter import InMemoryRateLimiter


def test_rate_limit_allows_within_limit():
    """Test rate limiter allows requests within limit."""
    limiter = InMemoryRateLimiter()
    
    # 5 requests should be allowed
    for i in range(5):
        is_allowed, retry_after = limiter.check_rate_limit('test:key', max_requests=5, window_seconds=10)
        assert is_allowed is True
        assert retry_after is None


def test_rate_limit_blocks_exceeding_limit():
    """Test rate limiter blocks requests exceeding limit."""
    limiter = InMemoryRateLimiter()
    
    # First 5 requests allowed
    for i in range(5):
        limiter.check_rate_limit('test:key', max_requests=5, window_seconds=10)
    
    # 6th request should be blocked
    is_allowed, retry_after = limiter.check_rate_limit('test:key', max_requests=5, window_seconds=10)
    assert is_allowed is False
    assert retry_after is not None
    assert retry_after > 0


def test_rate_limit_resets_after_window():
    """Test rate limiter resets after window expires."""
    limiter = InMemoryRateLimiter()
    
    # Fill up the limit
    for i in range(3):
        limiter.check_rate_limit('test:key', max_requests=3, window_seconds=1)
    
    # Should be blocked
    is_allowed, _ = limiter.check_rate_limit('test:key', max_requests=3, window_seconds=1)
    assert is_allowed is False
    
    # Wait for window to expire
    time.sleep(1.5)
    
    # Should be allowed again
    is_allowed, _ = limiter.check_rate_limit('test:key', max_requests=3, window_seconds=1)
    assert is_allowed is True


def test_rate_limit_different_keys_independent():
    """Test different keys have independent limits."""
    limiter = InMemoryRateLimiter()
    
    # Fill limit for key1
    for i in range(5):
        limiter.check_rate_limit('test:key1', max_requests=5, window_seconds=10)
    
    # key1 should be blocked
    is_allowed, _ = limiter.check_rate_limit('test:key1', max_requests=5, window_seconds=10)
    assert is_allowed is False
    
    # key2 should still be allowed
    is_allowed, _ = limiter.check_rate_limit('test:key2', max_requests=5, window_seconds=10)
    assert is_allowed is True
```

### ✅ Success Criteria

- [ ] Enhanced rate limiter implemented
- [ ] Rate limiting applied to all auth endpoints
- [ ] Different limits for different endpoints
- [ ] Audit logging for rate limit violations
- [ ] Unit tests pass
- [ ] Manual testing confirms rate limits work

### 🧪 Testing Procedure

```bash
# 1. Run unit tests
pytest tests/test_rate_limiter.py -v

# 2. Test login rate limit (5 attempts per 15 min)
for i in {1..6}; do
  echo "Attempt $i:"
  curl -X POST http://localhost:3000/server/smart_railway_app_function/session/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrongpassword"}'
  echo ""
done

# Expected: First 5 attempts return 401, 6th returns 429 (Too Many Requests)

# 3. Check rate limit status (for authenticated user)
curl -X GET http://localhost:3000/server/smart_railway_app_function/session/rate-limit/status \
  -H "Cookie: railway_sid=<your-session-id>"

# 4. Verify audit log
# Should contain rate_limit_exceeded events
```

---

## Plan #6: Debug Endpoints Protection

### 🎯 Objective
Disable or protect debug endpoints in production to prevent information disclosure.

### 📊 Current State
- Debug endpoints expose database schema
- Debug endpoints reveal configuration
- No authentication required
- Available in production

### ⏱️ Estimated Time: 30-60 minutes

### 📋 Implementation Steps

#### Step 6.1: Environment-Based Debug Protection

**File:** `functions/smart_railway_app_function/main.py`

**Wrap debug endpoints with environment check:**

```python
def create_flask_app():
    """Create and configure the Flask application with all routes."""
    
    app = Flask(__name__)
    # ... existing config
    
    # ── Debug Endpoints (DEVELOPMENT ONLY) ────────────────────────────────
    # Only register debug endpoints in development environment
    if os.getenv('APP_ENVIRONMENT') == 'development':
        
        @app.route('/debug/columns')
        def debug_columns():
            """Debug endpoint to list table columns (DEVELOPMENT ONLY)."""
            from repositories.cloudscale_repository import get_catalyst_app
            
            try:
                catalyst_app = get_catalyst_app()
                if not catalyst_app:
                    return jsonify({'status': 'error', 'message': 'Catalyst not initialized'}), 500
                
                zcql = catalyst_app.zcql()
                result = zcql.execute_query("SELECT * FROM Users LIMIT 1")
                
                if result:
                    columns = list(result[0]['Users'].keys())
                    return jsonify({'status': 'success', 'columns': columns}), 200
                else:
                    return jsonify({'status': 'success', 'message': 'No users found'}), 200
            
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @app.route('/debug/config')
        def debug_config():
            """Debug endpoint to show configuration (DEVELOPMENT ONLY)."""
            from config import TABLES
            from repositories.cloudscale_repository import get_catalyst_app
            
            catalyst_ready = get_catalyst_app() is not None
            return jsonify({
                'database': 'CloudScale (ZCQL)',
                'catalyst_initialized': catalyst_ready,
                'tables': list(TABLES.keys()),
                'table_count': len(TABLES),
                'environment': os.getenv('APP_ENVIRONMENT', 'unknown')
            })
        
        logger.info("Debug endpoints registered (DEVELOPMENT MODE)")
    
    else:
        # Production: Return 404 for debug endpoints
        @app.route('/debug/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def debug_not_available(path):
            """Debug endpoints not available in production."""
            logger.warning(f"Attempt to access debug endpoint in production: /debug/{path}")
            return jsonify({
                'status': 'error',
                'message': 'Not found'
            }), 404
    
    # ... rest of application setup
```

#### Step 6.2: Admin-Protected Debug Endpoints (Alternative)

If you need debug endpoints in production for troubleshooting:

**File:** `functions/smart_railway_app_function/routes/admin_debug.py` (NEW)

```python
"""
Admin-only debug endpoints for production troubleshooting.
"""

from flask import Blueprint, jsonify, request
from core.session_middleware import require_admin
from repositories.cloudscale_repository import get_catalyst_app
from config import TABLES

admin_debug_blueprint = Blueprint('admin_debug', __name__, url_prefix='/admin/debug')


@admin_debug_blueprint.route('/health-check', methods=['GET'])
@require_admin
def admin_health_check():
    """
    Detailed health check for admins.
    
    Returns:
        Detailed system health information
    """
    catalyst_app = get_catalyst_app()
    
    health = {
        'catalyst_initialized': catalyst_app is not None,
        'tables_configured': len(TABLES),
        'environment': os.getenv('APP_ENVIRONMENT'),
    }
    
    # Test database connectivity
    if catalyst_app:
        try:
            zcql = catalyst_app.zcql()
            result = zcql.execute_query("SELECT COUNT(*) as user_count FROM Users")
            health['database_accessible'] = True
            health['user_count'] = result[0]['user_count'] if result else 0
        except Exception as e:
            health['database_accessible'] = False
            health['database_error'] = str(e)
    
    return jsonify({
        'status': 'success',
        'data': health
    })


@admin_debug_blueprint.route('/tables', methods=['GET'])
@require_admin
def admin_list_tables():
    """
    List all configured tables (admin only).
    
    Returns:
        List of tables
    """
    return jsonify({
        'status': 'success',
        'data': {
            'tables': list(TABLES.keys()),
            'count': len(TABLES)
        }
    })


# Register in main.py
# from routes.admin_debug import admin_debug_blueprint
# app.register_blueprint(admin_debug_blueprint)
```

#### Step 6.3: Add Security Audit Log for Debug Access

**File:** `functions/smart_railway_app_function/routes/admin_debug.py`

```python
from services.session_service import log_audit_event

@admin_debug_blueprint.before_request
def log_debug_access():
    """Log all debug endpoint access for security audit."""
    from flask import g
    
    log_audit_event(
        event_type='debug_endpoint_access',
        user_id=getattr(g, 'user_id', None),
        user_email=getattr(g, 'user_email', None),
        ip_address=request.remote_addr,
        details={
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path
        },
        severity='info'
    )
```

### ✅ Success Criteria

- [ ] Debug endpoints only available in development
- [ ] Production returns 404 for debug endpoints
- [ ] Admin-protected debug endpoints available (optional)
- [ ] Security audit logging for debug access
- [ ] Tests pass

### 🧪 Testing Procedure

```bash
# 1. Test in development
APP_ENVIRONMENT=development catalyst serve
curl http://localhost:3000/server/smart_railway_app_function/debug/config
# Expected: 200 OK with config data

# 2. Test in production
APP_ENVIRONMENT=production catalyst serve
curl http://localhost:3000/server/smart_railway_app_function/debug/config
# Expected: 404 Not Found

# 3. Test admin debug endpoint (if implemented)
curl http://localhost:3000/server/smart_railway_app_function/admin/debug/health-check \
  -H "Cookie: railway_sid=<admin-session-id>"
# Expected: 200 OK with health data (if admin)
# Expected: 403 Forbidden (if not admin)
```

---

## Plan #7: HTTPS Enforcement

### 🎯 Objective
Enforce HTTPS in production to protect data in transit and prevent man-in-the-middle attacks.

### 📊 Current State
- No HTTPS enforcement
- Cookies can be intercepted over HTTP
- Session hijacking possible

### ⏱️ Estimated Time: 30-60 minutes

### 📋 Implementation Steps

#### Step 7.1: HTTPS Redirect Middleware

**File:** `functions/smart_railway_app_function/core/https_enforcer.py` (NEW)

```python
"""
HTTPS Enforcement Middleware
Redirects HTTP requests to HTTPS in production.
"""

import os
import logging
from flask import request, redirect

logger = logging.getLogger(__name__)


class HTTPSEnforcer:
    """
    Middleware to enforce HTTPS in production.
    
    Features:
    - Redirects HTTP to HTTPS (301 permanent redirect)
    - Checks X-Forwarded-Proto header for proxies
    - Respects environment configuration
    - Logs HTTP requests in production
    """
    
    def __init__(self, app=None):
        """
        Initialize HTTPS enforcer.
        
        Args:
            app: Flask app instance (optional)
        """
        self.enabled = os.getenv('APP_ENVIRONMENT') == 'production'
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Register HTTPS enforcer with Flask app."""
        if self.enabled:
            app.before_request(self.enforce_https)
            logger.info("HTTPS enforcement enabled (PRODUCTION MODE)")
        else:
            logger.info("HTTPS enforcement disabled (DEVELOPMENT MODE)")
    
    def enforce_https(self):
        """
        Enforce HTTPS for all requests in production.
        
        Redirects HTTP requests to HTTPS with 301 (permanent redirect).
        """
        if not self.enabled:
            return None
        
        # Check if request is already HTTPS
        is_secure = request.is_secure
        
        # Check X-Forwarded-Proto header (for proxies/load balancers)
        forwarded_proto = request.headers.get('X-Forwarded-Proto', '').lower()
        if forwarded_proto == 'https':
            is_secure = True
        
        if not is_secure:
            # Log insecure request attempt
            logger.warning(f"HTTP request blocked: {request.method} {request.path} from {request.remote_addr}")
            
            # Build HTTPS URL
            url = request.url.replace('http://', 'https://', 1)
            
            # 301 Permanent Redirect (tells browsers to always use HTTPS)
            return redirect(url, code=301)
        
        return None


def create_https_enforcer(app):
    """
    Factory function to create HTTPS enforcer.
    
    Args:
        app: Flask app instance
    
    Returns:
        HTTPSEnforcer instance
    """
    return HTTPSEnforcer(app)
```

#### Step 7.2: Integrate with Flask App

**File:** `functions/smart_railway_app_function/main.py`

```python
def create_flask_app():
    """Create and configure the Flask application with all routes."""
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')
    
    # ── HTTPS Enforcement (PRODUCTION ONLY) ───────────────────────────────
    from core.https_enforcer import create_https_enforcer
    create_https_enforcer(app)
    
    # ── Security Headers ──────────────────────────────────────────────────
    from core.security_headers import create_security_headers
    create_security_headers(app)
    
    # ... rest of application setup
```

#### Step 7.3: Update Cookie Configuration

**File:** `functions/smart_railway_app_function/config.py`

**Ensure Secure flag is set in production:**

```python
# ══════════════════════════════════════════════════════════════════════════════
#  SESSION MANAGEMENT CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Session cookie configuration
_is_production = os.getenv('APP_ENVIRONMENT') == 'production'
_is_development = os.getenv('APP_ENVIRONMENT') == 'development'

# Secure flag: MUST be True in production (HTTPS only)
SESSION_COOKIE_SECURE = _is_production  # Always True in production

# SameSite: Lax allows navigation, Strict is more secure but can break UX
SESSION_COOKIE_SAMESITE = 'Strict' if _is_production else 'Lax'

# HttpOnly: Always True for security
SESSION_COOKIE_HTTPONLY = True

logger.info(f"Session cookies: Secure={SESSION_COOKIE_SECURE}, SameSite={SESSION_COOKIE_SAMESITE}")
```

#### Step 7.4: Environment Variable Configuration

**File:** `functions/smart_railway_app_function/.env`

**For production:**

```bash
# ══ Flask ══════════════════════════════════════════════════════
APP_ENVIRONMENT=production  # Enable HTTPS enforcement
SECRET_KEY=<your-production-secret>

# ══ Session Management ═════════════════════════════════════════
# Secure cookie - MUST be true in production
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Strict
```

#### Step 7.5: Catalyst Hosting Configuration

Zoho Catalyst automatically provides HTTPS. Ensure your custom domain has SSL certificate:

```bash
# In Catalyst Console:
# 1. Go to Settings → Custom Domain
# 2. Add your domain (e.g., railway.example.com)
# 3. Catalyst automatically provisions SSL certificate
# 4. Update DNS records as instructed
# 5. Wait for SSL activation (5-10 minutes)

# Verify SSL is active:
curl -I https://your-domain.com
# Should return: HTTP/2 200 (not HTTP/1.1)
```

### ✅ Success Criteria

- [ ] HTTPS enforcer created
- [ ] HTTP requests redirected to HTTPS in production
- [ ] Secure flag set on cookies in production
- [ ] HSTS header added
- [ ] SSL certificate active on custom domain
- [ ] Tests pass

### 🧪 Testing Procedure

```bash
# 1. Test HTTPS redirect (in production)
curl -I http://your-domain.com/health
# Expected: 301 Moved Permanently
# Expected: Location: https://your-domain.com/health

# 2. Test HTTPS works
curl -I https://your-domain.com/health
# Expected: 200 OK
# Expected: Strict-Transport-Security header present

# 3. Test cookie Secure flag
curl -v https://your-domain.com/session/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
# Expected: Set-Cookie header contains "Secure"

# 4. Browser test
# Open: http://your-domain.com
# Should auto-redirect to: https://your-domain.com

# 5. SSL Labs test
# Visit: https://www.ssllabs.com/ssltest/
# Enter your domain
# Target: A or A+ rating
```

### 🔄 Rollback Strategy

```python
# Feature flag in config.py
ENFORCE_HTTPS = os.getenv('ENFORCE_HTTPS', 'true' if _is_production else 'false').lower() == 'true'

# https_enforcer.py
self.enabled = ENFORCE_HTTPS

# To disable in emergency:
# Set environment variable: ENFORCE_HTTPS=false
```

---

## Complete Implementation Checklist

### Phase 1: Critical Security Fixes (Week 1)

- [ ] **Day 1-2:** HMAC Cookie Signing
  - [ ] Create cookie signer module
  - [ ] Update session service
  - [ ] Update routes
  - [ ] Write tests
  - [ ] Deploy and test

- [ ] **Day 3:** Input Validation
  - [ ] Create validator module
  - [ ] Apply to all routes
  - [ ] Write tests
  - [ ] Deploy and test

- [ ] **Day 4:** Security Headers
  - [ ] Create headers module
  - [ ] Configure CSP
  - [ ] Test in browser
  - [ ] Deploy

- [ ] **Day 5:** CORS Hardening
  - [ ] Create CORS module
  - [ ] Update config
  - [ ] Test cross-origin requests
  - [ ] Deploy

### Phase 2: Enhanced Protection (Week 2)

- [ ] **Day 6-7:** Rate Limiting
  - [ ] Create rate limiter
  - [ ] Apply to auth endpoints
  - [ ] Test limits
  - [ ] Deploy

- [ ] **Day 8:** Debug Protection
  - [ ] Wrap debug endpoints
  - [ ] Test in production
  - [ ] Deploy

- [ ] **Day 9:** HTTPS Enforcement
  - [ ] Create HTTPS enforcer
  - [ ] Configure SSL
  - [ ] Test redirects
  - [ ] Deploy

- [ ] **Day 10:** Final Testing
  - [ ] Run all tests
  - [ ] Security scan
  - [ ] Penetration testing
  - [ ] Documentation update

---

## Monitoring & Maintenance

### Security Monitoring Checklist

- [ ] Set up log monitoring for:
  - [ ] Failed login attempts
  - [ ] Rate limit violations
  - [ ] SQL injection attempts
  - [ ] Cookie tampering
  - [ ] Debug endpoint access

- [ ] Configure alerts for:
  - [ ] Multiple failed logins from same IP
  - [ ] Unusual rate limit patterns
  - [ ] Security header violations
  - [ ] SSL certificate expiry

### Regular Security Tasks

**Weekly:**
- [ ] Review audit logs
- [ ] Check for dependency updates
- [ ] Monitor rate limit stats

**Monthly:**
- [ ] Run security scan
- [ ] Review and update CSP
- [ ] Check SSL certificate status
- [ ] Review CORS configuration

**Quarterly:**
- [ ] Penetration testing
- [ ] Security audit
- [ ] Update security documentation
- [ ] Rotate secrets (SESSION_SECRET, etc.)

---

## Summary

You now have detailed implementation plans for all 7 critical security vulnerabilities:

1. ✅ **HMAC Cookie Signing** - Prevent session tampering
2. ✅ **Security Headers** - Prevent XSS, clickjacking, etc.
3. ✅ **CORS Hardening** - Prevent cross-origin attacks
4. ✅ **Input Validation** - Prevent SQL injection
5. ✅ **Rate Limiting** - Prevent brute force attacks
6. ✅ **Debug Protection** - Prevent information disclosure
7. ✅ **HTTPS Enforcement** - Protect data in transit

**Total Implementation Time:** 12-16 hours  
**Recommended Sprint:** 10 days (2 weeks)

**Ready to start implementation?** I recommend beginning with **HMAC Cookie Signing** as it has the highest impact on session security.

Let me know which vulnerability you'd like to tackle first, and I can guide you through the implementation!
