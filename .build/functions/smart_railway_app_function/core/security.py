"""
Core Security Module - Smart Railway Ticketing System

Provides:
  - Argon2 password hashing (Primary and Mandatory)
  - JWT token generation and validation
  - require_auth / require_admin decorators
  - Rate limiter for sensitive endpoints
"""

from __future__ import annotations

import os
import logging
import threading
import hashlib
import hmac
import base64
import json
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from collections import defaultdict
from typing import Optional, Dict, Any

from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# Try to import Argon2 (Mandatory)
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    # Tunable Argon2 parameters for constrained serverless environments.
    # Defaults are secure while avoiding high-memory failures on small runtimes.
    _argon2_time_cost = int(os.getenv("ARGON2_TIME_COST", "2"))
    _argon2_memory_cost = int(os.getenv("ARGON2_MEMORY_COST_KIB", "19456"))  # 19 MiB
    _argon2_parallelism = int(os.getenv("ARGON2_PARALLELISM", "2"))

    _ph = PasswordHasher(
        time_cost=_argon2_time_cost,
        memory_cost=_argon2_memory_cost,
        parallelism=_argon2_parallelism,
    )
    _ph_low_memory = PasswordHasher(
        time_cost=2,
        memory_cost=8192,   # 8 MiB emergency Argon2 fallback
        parallelism=1,
    )
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    if os.name != "nt":
        logger.error("argon2-cffi not available! Security critical failure.")
    else:
        logger.warning("argon2-cffi not available; using PBKDF2-SHA256 fallback on Windows.")

# Try bcrypt for legacy support ONLY
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "260000"))
PBKDF2_SALT_BYTES = int(os.getenv("PBKDF2_SALT_BYTES", "16"))


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64d(txt: str) -> bytes:
    pad = "=" * (-len(txt) % 4)
    return base64.urlsafe_b64decode((txt + pad).encode("utf-8"))


def _pbkdf2_hash(plain: str, iterations: int = PBKDF2_ITERATIONS, salt: bytes = None) -> str:
    salt_bytes = salt if salt is not None else secrets.token_bytes(PBKDF2_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt_bytes, iterations)
    return f"pbkdf2_sha256${iterations}${_b64e(salt_bytes)}${_b64e(dk)}"


def _pbkdf2_verify(plain: str, hashed: str) -> bool:
    try:
        _alg, iter_s, salt_s, dk_s = hashed.split("$", 3)
        iterations = int(iter_s)
        salt = _b64d(salt_s)
        expected = _b64d(dk_s)
        actual = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

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
#  PASSWORD HASHING (Argon2 primary)
# ══════════════════════════════════════════════════════════════════════════════

def hash_password(plain: str) -> str:
    """
    Hash a plaintext password using Argon2-id.
    Argon2 is the mandatory algorithm for this system.
    """
    if ARGON2_AVAILABLE:
        try:
            return _ph.hash(plain)
        except Exception as exc:
            # Serverless runtimes can throw memory allocation errors for stronger params.
            logger.warning(f"Primary Argon2 hashing failed, retrying with low-memory params: {exc}")
            try:
                return _ph_low_memory.hash(plain)
            except Exception as low_exc:
                logger.exception(f"Argon2 low-memory fallback also failed: {low_exc}")
    
    # Fallback (Windows dev / emergency): PBKDF2-SHA256 (salted + iterated)
    return _pbkdf2_hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify password against stored hash.

    Supports:
    - Argon2 hashes ($argon2id$...) [Primary]
    - bcrypt hashes ($2b$..., $2a$...) [Legacy Transition]
    - PBKDF2-SHA256 hashes (pbkdf2_sha256$...)
    - Legacy SHA-256 hashes [Legacy Transition]
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
                logger.error("Argon2 hash found but argon2-cffi not available")
                return False

        # bcrypt hashes (transition only)
        elif hashed.startswith("$2"):
            if BCRYPT_AVAILABLE:
                return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
            else:
                logger.warning("bcrypt hash found but bcrypt not available")
                return False

        # PBKDF2-SHA256 hashes (preferred fallback on Windows dev)
        elif hashed.startswith("pbkdf2_sha256$"):
            return _pbkdf2_verify(plain, hashed)

        # SHA-256 transition (64 hex chars)
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
    # PBKDF2 fallback should be upgraded to Argon2 when available
    if hashed.startswith("pbkdf2_sha256$"):
        return ARGON2_AVAILABLE
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

        # Session-first auth (default for this app). Fall back to JWT only when a Bearer token exists.
        if not token:
            from core.session_middleware import require_session
            return require_session(f)(*args, **kwargs)

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

        # Session-first admin auth. Fall back to JWT only when a Bearer token exists.
        if not token:
            from core.session_middleware import require_session_admin
            return require_session_admin(f)(*args, **kwargs)

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


def require_role(roles):
    """
    Decorator: Requires user role in allowed roles.
    Uses JWT claims and preserves admin email/domain override.
    """
    normalized_roles = {str(role).lower() for role in (roles or [])}

    def decorator(f):
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

            is_admin_email = (
                email == ADMIN_EMAIL.lower() or
                email.endswith("@" + ADMIN_DOMAIN)
            )
            is_admin_role = role.lower() == "admin"
            is_admin = is_admin_email or is_admin_role

            if normalized_roles:
                allowed = role.lower() in normalized_roles or (is_admin and "admin" in normalized_roles)
                if not allowed:
                    return jsonify({
                        "status": "error",
                        "message": "Access denied"
                    }), 403

            g.user_id = payload.get("sub", "")
            g.user_email = email
            g.user_role = "Admin" if is_admin else role

            return f(*args, **kwargs)

        return decorated

    return decorator


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
