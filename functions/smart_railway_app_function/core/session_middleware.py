"""
Session Middleware - Smart Railway Ticketing System

Provides session-based authentication decorators to replace JWT-based auth.

Features:
  - Session validation from HttpOnly cookies
  - CSRF token validation for state-changing requests
  - Admin role verification
  - Request context population (g.user_id, g.user_email, g.user_role)
  - Sliding session timeout (auto-extends on activity)
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Optional, Callable, Any

from flask import request, jsonify, g, make_response

from config import (
    SESSION_COOKIE_NAME,
    CSRF_HEADER_NAME,
    ADMIN_EMAIL,
    ADMIN_DOMAIN,
)
from services.session_service import (
    validate_session,
    validate_csrf_token,
    extract_raw_session_id,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def _get_session_id_from_request() -> Optional[str]:
    """
    Extract session ID from request.
    
    Priority:
    1. HttpOnly cookie (primary, most secure)
    2. Authorization header (fallback for API clients)
    
    Returns:
        Session ID string or None
    """
    # Primary: HttpOnly cookie
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        return session_id
    
    # Fallback: Authorization header for API clients
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("session "):
        return auth_header[8:].strip()
    
    return None


def _get_csrf_token_from_request() -> Optional[str]:
    """Extract CSRF token from request header."""
    return request.headers.get(CSRF_HEADER_NAME)


def _is_state_changing_request() -> bool:
    """Check if request method modifies state (requires CSRF)."""
    return request.method in ("POST", "PUT", "DELETE", "PATCH")


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION AUTH DECORATOR
# ══════════════════════════════════════════════════════════════════════════════

def require_session(f: Callable) -> Callable:
    """
    Decorator: Requires valid session.
    
    Sets g.user_id, g.user_email, g.user_role, g.session_id on success.
    Validates CSRF token for state-changing requests.
    
    Returns 401 if:
        - No session cookie present
        - Session is invalid/expired
        - CSRF token missing/invalid on state-changing requests
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Extract session ID
        session_id = _get_session_id_from_request()
        
        if not session_id:
            logger.debug("No session ID in request")
            return jsonify({
                "status": "error",
                "code": "AUTH_REQUIRED",
                "message": "Authentication required"
            }), 401
        
        # Validate session
        session_data = validate_session(session_id)
        
        if not session_data:
            logger.debug(f"Invalid session: {session_id[:8] if session_id else 'None'}...")
            response = make_response(jsonify({
                "status": "error",
                "code": "INVALID_SESSION",
                "message": "Session expired or invalid. Please log in again."
            }), 401)
            # Clear invalid cookie (use same settings as when setting the cookie)
            from config import SESSION_COOKIE_SECURE, SESSION_COOKIE_SAMESITE
            response.set_cookie(
                SESSION_COOKIE_NAME,
                "",
                expires=0,
                httponly=True,
                secure=SESSION_COOKIE_SECURE,
                samesite=SESSION_COOKIE_SAMESITE,
                path="/"
            )
            return response
        
        # CSRF validation for state-changing requests
        raw_session_id = (session_data or {}).get("session_id") or extract_raw_session_id(session_id)

        if _is_state_changing_request():
            csrf_token = _get_csrf_token_from_request()
            
            if not csrf_token:
                logger.warning(f"CSRF token missing for {request.method} {request.path}")
                return jsonify({
                    "status": "error",
                    "code": "CSRF_MISSING",
                    "message": "CSRF token required for this request"
                }), 403
            
            if not validate_csrf_token(raw_session_id, csrf_token):
                logger.warning(f"CSRF validation failed for session {session_id[:8]}...")
                return jsonify({
                    "status": "error",
                    "code": "CSRF_INVALID",
                    "message": "Invalid CSRF token"
                }), 403
        
        # Set request context
        g.session_id = raw_session_id or ""
        g.user_id = str(session_data.get("user_id", ""))
        g.user_email = session_data.get("user_email", "")
        g.user_role = session_data.get("user_role", "User")
        g.user_type = session_data.get("user_type", "user")  # 'user' or 'employee'
        g.csrf_token = session_data.get("csrf_token", "")
        
        return f(*args, **kwargs)
    
    return decorated


def require_session_admin(f: Callable) -> Callable:
    """
    Decorator: Requires valid session with Admin role.
    
    Sets g.user_id, g.user_email, g.user_role, g.session_id on success.
    
    Returns 401 if not authenticated.
    Returns 403 if not admin.
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Extract session ID
        session_id = _get_session_id_from_request()
        
        if not session_id:
            return jsonify({
                "status": "error",
                "code": "AUTH_REQUIRED",
                "message": "Authentication required"
            }), 401
        
        # Validate session
        session_data = validate_session(session_id)
        
        if not session_data:
            response = make_response(jsonify({
                "status": "error",
                "code": "INVALID_SESSION",
                "message": "Session expired or invalid. Please log in again."
            }), 401)
            response.set_cookie(
                SESSION_COOKIE_NAME,
                "",
                expires=0,
                httponly=True,
                secure=True,
                samesite="Strict",
                path="/"
            )
            return response
        
        # CSRF validation for state-changing requests
        raw_session_id = (session_data or {}).get("session_id") or extract_raw_session_id(session_id)

        if _is_state_changing_request():
            csrf_token = _get_csrf_token_from_request()
            
            if not csrf_token or not validate_csrf_token(raw_session_id, csrf_token):
                logger.warning(f"CSRF validation failed - token present: {bool(csrf_token)}, session: {session_id[:10]}...")
                return jsonify({
                    "status": "error",
                    "code": "CSRF_INVALID",
                    "message": "Invalid or missing CSRF token"
                }), 403
        
        # Check admin role
        email = (session_data.get("user_email") or "").lower()
        role = (session_data.get("user_role") or "User").lower()
        
        is_admin_email = (
            email == ADMIN_EMAIL.lower() or
            email.endswith("@" + ADMIN_DOMAIN)
        )
        is_admin_role = role == "admin"
        
        if not is_admin_email and not is_admin_role:
            logger.warning(f"Admin access denied for user {email}")
            return jsonify({
                "status": "error",
                "code": "ADMIN_REQUIRED",
                "message": "Admin access required"
            }), 403
        
        # Set request context
        g.session_id = raw_session_id or ""
        g.user_id = str(session_data.get("user_id", ""))
        g.user_email = email
        g.user_role = "Admin"
        g.user_type = session_data.get("user_type", "employee")  # Admin must be employee
        g.csrf_token = session_data.get("csrf_token", "")
        
        return f(*args, **kwargs)
    
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
#  REQUIRE EMPLOYEE SESSION DECORATOR
# ══════════════════════════════════════════════════════════════════════════════

def require_session_employee(f: Callable) -> Callable:
    """
    Decorator: Requires valid employee session (any role: Admin or Employee).
    
    This is for endpoints that any employee can access (not just admins).
    Used for employee self-service features like password change.
    
    Sets: g.session_id, g.user_id, g.user_email, g.user_role, g.user_type
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        session_id = _get_session_id_from_request()
        
        if not session_id:
            return jsonify({
                "status": "error",
                "code": "SESSION_REQUIRED",
                "message": "Session required. Please login."
            }), 401
        
        # Validate session
        session_data = validate_session(session_id)
        
        if not session_data:
            return jsonify({
                "status": "error",
                "code": "SESSION_INVALID",
                "message": "Invalid or expired session. Please login again."
            }), 401
        
        # Check user type - must be employee
        user_type = (session_data.get("user_type") or "").lower()
        
        if user_type != "employee":
            return jsonify({
                "status": "error",
                "code": "EMPLOYEE_REQUIRED",
                "message": "Employee access required"
            }), 403
        
        # CSRF validation for state-changing requests
        raw_session_id = (session_data or {}).get("session_id") or extract_raw_session_id(session_id)

        if _is_state_changing_request():
            csrf_token = _get_csrf_token_from_request()
            
            if not csrf_token or not validate_csrf_token(raw_session_id, csrf_token):
                return jsonify({
                    "status": "error",
                    "code": "CSRF_INVALID",
                    "message": "Invalid or missing CSRF token"
                }), 403
        
        # Set request context
        g.session_id = raw_session_id or ""
        g.user_id = str(session_data.get("user_id", ""))
        g.user_email = session_data.get("user_email", "")
        g.user_role = session_data.get("user_role", "Employee")
        g.user_type = "employee"
        g.csrf_token = session_data.get("csrf_token", "")
        
        return f(*args, **kwargs)
    
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
#  OPTIONAL SESSION DECORATOR
# ══════════════════════════════════════════════════════════════════════════════

def optional_session(f: Callable) -> Callable:
    """
    Decorator: Validates session if present, but doesn't require it.
    
    Useful for endpoints that work for both authenticated and anonymous users.
    Sets g.user_id etc. if session is valid, leaves them empty otherwise.
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Default context values
        g.session_id = None
        g.user_id = ""
        g.user_email = ""
        g.user_role = ""
        g.user_type = ""
        g.csrf_token = ""
        
        # Try to validate session
        session_id = _get_session_id_from_request()
        
        if session_id:
            session_data = validate_session(session_id)
            
            if session_data:
                g.session_id = session_data.get("session_id") or extract_raw_session_id(session_id) or ""
                g.user_id = session_data.get("user_id", "")
                g.user_email = session_data.get("user_email", "")
                g.user_role = session_data.get("user_role", "User")
                g.user_type = session_data.get("user_type", "user")
                g.csrf_token = session_data.get("csrf_token", "")
        
        return f(*args, **kwargs)
    
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
#  CONTEXT HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_current_session_id() -> str:
    """Return current session ID from request context."""
    return getattr(g, "session_id", "") or ""


def get_current_user_id() -> str:
    """Return current user ID from request context."""
    return getattr(g, "user_id", "") or ""


def get_current_user_email() -> str:
    """Return current user email from request context."""
    return getattr(g, "user_email", "") or ""


def get_current_user_role() -> str:
    """Return current user role from request context."""
    return getattr(g, "user_role", "User") or "User"


def get_current_user_type() -> str:
    """Return current user type from request context ('user' or 'employee')."""
    return getattr(g, "user_type", "user") or "user"


def get_current_csrf_token() -> str:
    """Return CSRF token for current session."""
    return getattr(g, "csrf_token", "") or ""


def is_authenticated() -> bool:
    """Check if current request is authenticated."""
    return bool(getattr(g, "session_id", None))


def is_admin() -> bool:
    """Check if current user is admin."""
    return get_current_user_role().lower() == "admin"
