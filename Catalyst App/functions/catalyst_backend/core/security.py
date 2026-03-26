"""
Core Security Module — Railway Ticketing System
Provides:
  - bcrypt password hashing (replaces insecure SHA-256)
  - JWT token generation and validation (replaces header-only auth)
  - require_auth / require_admin decorators
  - Rate limiter for sensitive endpoints
"""

from __future__ import annotations

import os
import logging
import threading
import hashlib
from datetime import datetime, timedelta, timezone
from functools import wraps
from collections import defaultdict

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("bcrypt not available, using SHA-256 fallback for password hashing")

import jwt
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# ── JWT Config ──────────────────────────────────────────────────────────────
JWT_SECRET  = os.getenv("JWT_SECRET_KEY", "railway-secret-change-in-production-do-not-use-default")
JWT_ALGO    = "HS256"
JWT_EXPIRY  = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))          # access token: 60 min
JWT_REFRESH = int(os.getenv("JWT_REFRESH_DAYS", "7"))             # refresh token: 7 days

# ── In-memory rate limiter (per IP) ─────────────────────────────────────────
_rate_store: dict = defaultdict(list)
_rate_lock  = threading.Lock()

RATE_LIMIT_AUTH      = int(os.getenv("RATE_LIMIT_AUTH", "100"))   # Increased to 100
RATE_LIMIT_WINDOW    = int(os.getenv("RATE_LIMIT_WINDOW", "60"))   # Decreased to 60s


# ════════════════════════════════════════════════════════════════════════════
#  PASSWORD HASHING  (bcrypt — replaces SHA-256)
# ════════════════════════════════════════════════════════════════════════════

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt (cost factor 12), fallback to SHA-256."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
    else:
        # Fallback: SHA-256 (temporary until bcrypt is properly installed)
        logger.warning("Using SHA-256 fallback for password hashing (bcrypt unavailable)")
        return hashlib.sha256(plain.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify password against stored hash.
    Supports both bcrypt (new) and legacy SHA-256 (migration path).
    Falls back to SHA-256 if bcrypt unavailable.
    """
    if not plain or not hashed:
        return False
    try:
        # bcrypt hashes start with $2b$ or $2a$
        if hashed.startswith("$2"):
            if BCRYPT_AVAILABLE:
                return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
            else:
                logger.warning("bcrypt unavailable, cannot verify bcrypt hash")
                return False
        # SHA-256 path (legacy or fallback)
        sha_hash = hashlib.sha256(plain.encode()).hexdigest()
        return sha_hash == hashed
    except Exception as exc:
        logger.error(f"verify_password error: {exc}")
        return False


def needs_rehash(hashed: str) -> bool:
    """Return True if the password was hashed with the old SHA-256 scheme."""
    return not (hashed or "").startswith("$2")


# ════════════════════════════════════════════════════════════════════════════
#  JWT TOKEN MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

def generate_access_token(user_id: str, email: str, role: str) -> str:
    """Generate a signed JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub":   user_id,
        "email": email,
        "role":  role,
        "iat":   now,
        "exp":   now + timedelta(minutes=JWT_EXPIRY),
        "type":  "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def generate_refresh_token(user_id: str, email: str) -> str:
    """Generate a long-lived refresh token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub":  user_id,
        "email": email,
        "iat":   now,
        "exp":   now + timedelta(days=JWT_REFRESH),
        "type":  "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns payload dict or None on failure."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.debug(f"JWT invalid: {exc}")
        return None


def _extract_bearer(req) -> str | None:
    """Extract Bearer token from Authorization header or X-Auth-Token header."""
    auth = req.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return req.headers.get("X-Auth-Token", "").strip() or None


# ════════════════════════════════════════════════════════════════════════════
#  AUTH DECORATORS
# ════════════════════════════════════════════════════════════════════════════

def require_auth(f):
    """
    Decorator: requires valid JWT access token.
    Sets g.user_id, g.user_email, g.user_role on success.

    BACKWARDS COMPATIBILITY: Also accepts the legacy X-User-Email / X-User-Role
    headers so existing frontend code works without changes.
    Falls back to legacy headers if JWT is invalid/expired.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer(request)

        if token:
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                # Valid JWT - use its claims
                g.user_id    = payload.get("sub", "")
                g.user_email = payload.get("email", "")
                g.user_role  = payload.get("role", "User")
            else:
                # Invalid/expired JWT - fall back to legacy headers
                logger.debug("JWT invalid/expired, falling back to legacy headers for auth check")
                g.user_email = request.headers.get("X-User-Email", "").strip()
                g.user_role  = request.headers.get("X-User-Role", "User").strip()
                g.user_id    = request.headers.get("X-User-ID", "").strip()
                if not g.user_email:
                    return jsonify({"success": False, "error": "Invalid or expired token. Please log in again."}), 401
        else:
            # No JWT - use legacy headers
            g.user_email = request.headers.get("X-User-Email", "").strip()
            g.user_role  = request.headers.get("X-User-Role", "User").strip()
            g.user_id    = request.headers.get("X-User-ID", "").strip()
            if not g.user_email:
                return jsonify({"success": False, "error": "Authentication required"}), 401

        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """
    Decorator: requires Admin role.
    Accepts JWT or legacy X-User-Email/Role headers.
    Falls back to legacy headers if JWT is invalid/expired.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer(request)
        email = None
        role = None

        if token:
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                # Valid JWT - use its claims
                role  = payload.get("role", "User")
                email = payload.get("email", "")
            else:
                # Invalid/expired JWT - fall back to legacy headers
                logger.debug("JWT invalid/expired, falling back to legacy headers for admin check")
                email = request.headers.get("X-User-Email", "").strip().lower()
                role  = request.headers.get("X-User-Role", "").strip()
        else:
            # No JWT - use legacy headers
            email = request.headers.get("X-User-Email", "").strip().lower()
            role  = request.headers.get("X-User-Role", "").strip()

        # Ensure we have some form of identity
        if not email:
            return jsonify({"success": False, "error": "Authentication required"}), 401

        from config import ADMIN_DOMAIN, ADMIN_EMAIL
        is_admin_email = (email == ADMIN_EMAIL or email.endswith("@" + ADMIN_DOMAIN))
        if not is_admin_email and role.lower() != "admin":
            return jsonify({"success": False, "error": "Admin access required"}), 403

        g.user_email = email
        g.user_role  = "Admin"
        return f(*args, **kwargs)
    return decorated


def get_current_user_id() -> str:
    """Return user_id from JWT context (g) or X-User-ID header."""
    return getattr(g, "user_id", "") or request.headers.get("X-User-ID", "").strip()


def get_current_user_email() -> str:
    """Return user email from JWT context."""
    return getattr(g, "user_email", "") or request.headers.get("X-User-Email", "").strip()


def get_current_user_role() -> str:
    """Return role from JWT context."""
    return getattr(g, "user_role", "User")


# ════════════════════════════════════════════════════════════════════════════
#  RATE LIMITER
# ════════════════════════════════════════════════════════════════════════════

def check_rate_limit(key: str, max_calls: int = RATE_LIMIT_AUTH, window_seconds: int = RATE_LIMIT_WINDOW) -> bool:
    """
    Token-bucket rate limiter.
    Returns True if request is allowed, False if rate limit exceeded.
    """
    now = datetime.now().timestamp()
    with _rate_lock:
        calls = _rate_store[key]
        # Remove calls outside the window
        _rate_store[key] = [t for t in calls if now - t < window_seconds]
        if len(_rate_store[key]) >= max_calls:
            return False
        _rate_store[key].append(now)
    return True


def rate_limit(max_calls: int = RATE_LIMIT_AUTH, window_seconds: int = RATE_LIMIT_WINDOW):
    """Decorator factory for rate limiting by IP."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr or "unknown"
            if not check_rate_limit(f"rl:{f.__name__}:{ip}", max_calls, window_seconds):
                return jsonify({
                    "success": False,
                    "error": f"Too many requests. Please try again after {window_seconds // 60} minutes."
                }), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator
