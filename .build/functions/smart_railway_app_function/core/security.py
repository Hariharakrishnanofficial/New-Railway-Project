"""
Core Security Module - Smart Railway Ticketing System

Provides:
  - Argon2 password hashing (primary) with bcrypt fallback
  - JWT token generation and validation
  - require_auth / require_admin decorators
  - Rate limiter for sensitive endpoints
"""

from __future__ import annotations

import os
import logging
import threading
import hashlib
import base64
import json
from datetime import datetime, timedelta, timezone
from functools import wraps
from collections import defaultdict
from typing import Optional, Dict, Any

from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "smart-railway-jwt-secret-change-in-production")
JWT_ALGO = "HS256"
JWT_ACCESS_EXPIRY = int(os.getenv("JWT_ACCESS_EXPIRY_MINUTES", "60"))  # 60 minutes
JWT_REFRESH_EXPIRY = int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7"))    # 7 days

# Admin configuration
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@railway.com")
ADMIN_DOMAIN = os.getenv("ADMIN_DOMAIN", "catalyst-cs2.onslate.in")

# Rate limiting
RATE_LIMIT_AUTH = int(os.getenv("RATE_LIMIT_AUTH", "10"))         # 10 attempts
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "900"))    # per 15 minutes

_rate_store: Dict[str, list] = defaultdict(list)
_rate_lock = threading.Lock()

# ══════════════════════════════════════════════════════════════════════════════
#  PASSWORD HASHING (Argon2 primary, bcrypt fallback)
# ══════════════════════════════════════════════════════════════════════════════

# Try to import Argon2 (preferred)
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _ph = PasswordHasher()
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    logger.warning("argon2-cffi not available")

# Try bcrypt as fallback
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.warning("bcrypt not available, using SHA-256 fallback")


def hash_password(plain: str) -> str:
    """
    Hash a plaintext password.

    Priority:
    1. Argon2 (most secure, memory-hard)
    2. bcrypt (cost factor 12)
    3. SHA-256 (fallback for environments without crypto libs)
    """
    if ARGON2_AVAILABLE:
        return _ph.hash(plain)
    elif BCRYPT_AVAILABLE:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
    else:
        logger.warning("Using SHA-256 fallback for password hashing")
        return hashlib.sha256(plain.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify password against stored hash.

    Supports:
    - Argon2 hashes ($argon2id$...)
    - bcrypt hashes ($2b$..., $2a$...)
    - Legacy SHA-256 hashes
    """
    if not plain or not hashed:
        return False

    try:
        # Argon2 hashes start with $argon2
        if hashed.startswith("$argon2"):
            if ARGON2_AVAILABLE:
                try:
                    _ph.verify(hashed, plain)
                    return True
                except VerifyMismatchError:
                    return False
            else:
                logger.warning("Argon2 hash found but argon2-cffi not available")
                return False

        # bcrypt hashes start with $2b$ or $2a$
        elif hashed.startswith("$2"):
            if BCRYPT_AVAILABLE:
                return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
            else:
                logger.warning("bcrypt hash found but bcrypt not available")
                return False

        # SHA-256 fallback (64 hex chars)
        elif len(hashed) == 64:
            return hashlib.sha256(plain.encode()).hexdigest() == hashed

        return False

    except Exception as exc:
        logger.error(f"verify_password error: {exc}")
        return False


def needs_rehash(hashed: str) -> bool:
    """Return True if password should be rehashed with a stronger algorithm."""
    if not hashed:
        return True
    # Argon2 is strongest, no rehash needed
    if hashed.startswith("$argon2"):
        return False
    # bcrypt is acceptable, but could upgrade to Argon2
    if hashed.startswith("$2"):
        return ARGON2_AVAILABLE
    # SHA-256 should always be rehashed
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  JWT TOKEN MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def generate_access_token(user_id: str, email: str, role: str) -> str:
    """Generate a signed JWT access token."""
    try:
        import jwt
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=JWT_ACCESS_EXPIRY),
            "type": "access",
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    except ImportError:
        # Fallback: base64 encoded token (less secure but works)
        return _create_simple_token(user_id, email, role, JWT_ACCESS_EXPIRY * 60)


def generate_refresh_token(user_id: str, email: str) -> str:
    """Generate a long-lived refresh token."""
    try:
        import jwt
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "email": email,
            "iat": now,
            "exp": now + timedelta(days=JWT_REFRESH_EXPIRY),
            "type": "refresh",
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    except ImportError:
        return _create_simple_token(user_id, email, "User", JWT_REFRESH_EXPIRY * 86400)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT. Returns payload dict or None on failure."""
    try:
        import jwt
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except ImportError:
        return _decode_simple_token(token)
    except Exception as exc:
        logger.debug(f"JWT decode failed: {exc}")
        return None


def _create_simple_token(user_id: str, email: str, role: str, expires_seconds: int) -> str:
    """Fallback: Create a base64-encoded token when PyJWT is not available."""
    expires_at = (datetime.utcnow() + timedelta(seconds=expires_seconds)).isoformat()
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expires_at,
        "secret": JWT_SECRET[:16],  # Partial secret for validation
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_simple_token(token: str) -> Optional[Dict[str, Any]]:
    """Fallback: Decode a base64-encoded token."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())

        # Validate secret
        if payload.get("secret") != JWT_SECRET[:16]:
            return None

        # Check expiry
        exp = datetime.fromisoformat(payload["exp"])
        if datetime.utcnow() > exp:
            return None

        return payload
    except Exception:
        return None


def _extract_bearer(req) -> Optional[str]:
    """Extract Bearer token from Authorization header."""
    auth = req.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH DECORATORS
# ══════════════════════════════════════════════════════════════════════════════

def require_auth(f):
    """
    Decorator: Requires valid JWT access token.
    Sets g.user_id, g.user_email, g.user_role on success.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer(request)

        if not token:
            return jsonify({
                "status": "error",
                "message": "Authentication required"
            }), 401

        payload = decode_token(token)

        if not payload:
            return jsonify({
                "status": "error",
                "message": "Invalid or expired token. Please log in again."
            }), 401

        # Check token type
        if payload.get("type") not in ("access", None):
            return jsonify({
                "status": "error",
                "message": "Invalid token type"
            }), 401

        # Set user context
        g.user_id = payload.get("sub", "")
        g.user_email = payload.get("email", "")
        g.user_role = payload.get("role", "User")

        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    """
    Decorator: Requires Admin role.
    Uses JWT claims or checks admin domain/email.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer(request)

        if not token:
            return jsonify({
                "status": "error",
                "message": "Authentication required"
            }), 401

        payload = decode_token(token)

        if not payload:
            return jsonify({
                "status": "error",
                "message": "Invalid or expired token"
            }), 401

        email = payload.get("email", "").lower()
        role = payload.get("role", "User")

        # Check if admin
        is_admin_email = (
            email == ADMIN_EMAIL.lower() or
            email.endswith("@" + ADMIN_DOMAIN)
        )
        is_admin_role = role.lower() == "admin"

        if not is_admin_email and not is_admin_role:
            return jsonify({
                "status": "error",
                "message": "Admin access required"
            }), 403

        # Set user context
        g.user_id = payload.get("sub", "")
        g.user_email = email
        g.user_role = "Admin"

        return f(*args, **kwargs)

    return decorated


def get_current_user_id() -> str:
    """Return user_id from JWT context."""
    return getattr(g, "user_id", "")


def get_current_user_email() -> str:
    """Return user email from JWT context."""
    return getattr(g, "user_email", "")


def get_current_user_role() -> str:
    """Return role from JWT context."""
    return getattr(g, "user_role", "User")


# ══════════════════════════════════════════════════════════════════════════════
#  RATE LIMITER
# ══════════════════════════════════════════════════════════════════════════════

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
                    "status": "error",
                    "message": f"Too many requests. Please try again after {window_seconds // 60} minutes."
                }), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator
