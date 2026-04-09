"""
Session-Based Auth Routes - Smart Railway Ticketing System

Replaces JWT tokens with server-side session management.
Uses HttpOnly cookies for session ID storage.

Features:
  - Session-based login/logout/register
  - CSRF token generation and validation
  - Session management endpoints (list, revoke)
  - Password change with session invalidation
"""

import logging
import json
import os
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, make_response

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import (
    TABLES,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SECURE,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_HTTPONLY,
    SESSION_TIMEOUT_HOURS,
    CSRF_HEADER_NAME,
)
from core.security import (
    hash_password,
    verify_password,
    rate_limit,
)
from core.session_middleware import (
    require_session,
    require_session_admin,
    get_current_user_id,
    get_current_user_email,
    get_current_session_id,
    get_current_csrf_token,
)
from services.session_service import (
    create_session,
    revoke_session,
    revoke_all_user_sessions,
    get_user_sessions,
    validate_session,
    regenerate_csrf_token,
    cleanup_expired_sessions,
    get_all_active_sessions,
    admin_revoke_session,
    get_session_stats,
    log_audit_event,  # For audit logging
)

logger = logging.getLogger(__name__)
session_auth_bp = Blueprint('session_auth', __name__)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

BACKEND_SETUP_MESSAGE = 'Backend setup issue detected. Run catalyst login and restart catalyst serve.'


def _is_invalid_oauth_error(value) -> bool:
    """Detect Catalyst OAuth token failures from nested error payloads."""
    if value is None:
        return False
    text = str(value).lower()
    return 'invalid oauth token' in text or 'invalid_token' in text


def _is_tls_bundle_error(value) -> bool:
    """Detect stale/missing cert bundle failures from .build runtime."""
    if value is None:
        return False
    text = str(value).lower()
    return 'could not find a suitable tls ca certificate bundle' in text or 'cacert.pem' in text


def _is_backend_setup_error(value) -> bool:
    return _is_invalid_oauth_error(value) or _is_tls_bundle_error(value)


def _probe_cloudscale_connection() -> tuple:
    """Probe CloudScale once to distinguish setup issues from auth failures."""
    try:
        probe = cloudscale_repo.execute_query("SELECT ROWID FROM Users LIMIT 1")
        if probe.get('success'):
            return True, ''
        return False, str(probe.get('error', 'CloudScale query failed'))
    except Exception as exc:
        return False, str(exc)


def _extract_payload() -> dict:
    """Extract request payload across JSON/form/query variants."""
    data = request.get_json(silent=True)
    if isinstance(data, dict) and data:
        return data

    raw = request.get_data(as_text=True) or ''
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    form_data = request.form.to_dict()
    if form_data:
        return form_data

    values_data = request.values.to_dict()
    if values_data:
        return values_data

    return {}


def _build_user_response(user_row: dict) -> dict:
    """Build standardized user response from database row."""
    return {
        'id': user_row.get('ROWID'),
        'fullName': user_row.get('Full_Name', ''),
        'email': user_row.get('Email', ''),
        'phoneNumber': user_row.get('Phone_Number', ''),
        'role': user_row.get('Role', 'User'),
        'accountStatus': user_row.get('Account_Status', 'Active'),
        'dateOfBirth': user_row.get('Date_of_Birth', ''),
        'address': user_row.get('Address', ''),
    }


def _get_client_ip() -> str:
    """Extract client IP address from request."""
    # Check X-Forwarded-For header first (proxy/load balancer)
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr or ''


def _get_user_agent() -> str:
    """Extract User-Agent from request."""
    return request.headers.get('User-Agent', '')[:500]


def _set_session_cookie(response, session_id: str) -> None:
    """Set HttpOnly session cookie on response."""
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_TIMEOUT_HOURS)
    
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        expires=expires,
        httponly=SESSION_COOKIE_HTTPONLY,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path='/'
    )


def _clear_session_cookie(response) -> None:
    """Clear session cookie from response."""
    response.set_cookie(
        SESSION_COOKIE_NAME,
        '',
        expires=0,
        httponly=SESSION_COOKIE_HTTPONLY,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path='/'
    )


def _extract_device_fingerprint() -> dict:
    """Extract device fingerprint data from request headers."""
    return {
        'user_agent': request.headers.get('User-Agent', ''),
        'accept_language': request.headers.get('Accept-Language', ''),
        'accept_encoding': request.headers.get('Accept-Encoding', ''),
        'screen_resolution': request.headers.get('X-Screen-Resolution', ''),
        'timezone': request.headers.get('X-Timezone', ''),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  DEBUG ENDPOINT - Cookie Settings
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/debug/cookie-settings', methods=['GET'])
def debug_cookie_settings():
    """
    Debug endpoint to check current cookie settings.
    Returns cookie configuration and any existing session cookie.
    """
    return jsonify({
        'status': 'success',
        'cookieSettings': {
            'name': SESSION_COOKIE_NAME,
            'secure': SESSION_COOKIE_SECURE,
            'samesite': SESSION_COOKIE_SAMESITE,
            'httponly': SESSION_COOKIE_HTTPONLY,
            'timeoutHours': SESSION_TIMEOUT_HOURS,
        },
        'request': {
            'origin': request.headers.get('Origin', 'none'),
            'host': request.headers.get('Host', 'none'),
            'userAgent': request.headers.get('User-Agent', 'none')[:100],
        },
        'cookies': {
            'session_cookie_present': bool(request.cookies.get(SESSION_COOKIE_NAME)),
            'session_cookie_value_prefix': (request.cookies.get(SESSION_COOKIE_NAME) or '')[:8] + '...' if request.cookies.get(SESSION_COOKIE_NAME) else None,
            'all_cookie_names': list(request.cookies.keys()),
        }
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
#  REGISTER (Session-based)
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/register', methods=['POST'])
@rate_limit(max_calls=10, window_seconds=3600)
def session_register():
    """
    Register a new user account with session-based authentication.
    
    Creates user, generates session ID, sets HttpOnly cookie.
    """
    cloudscale_ok, cloudscale_error = _probe_cloudscale_connection()
    if not cloudscale_ok and _is_backend_setup_error(cloudscale_error):
        return jsonify({
            'status': 'error',
            'message': BACKEND_SETUP_MESSAGE,
            'details': cloudscale_error,
        }), 503

    data = _extract_payload()
    logger.debug('Session register payload received')

    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''
    phone_number = (data.get('phoneNumber') or data.get('Phone_Number') or '').strip()

    # Validation
    if not full_name:
        return jsonify({'status': 'error', 'message': 'Full name is required'}), 400
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    if not password:
        return jsonify({'status': 'error', 'message': 'Password is required'}), 400
    if len(password) < 8:
        return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400

    try:
        # Check if email already exists
        existing = cloudscale_repo.get_user_by_email(email)
        if existing:
            return jsonify({'status': 'error', 'message': 'Email already registered'}), 409

        # Create user
        hashed_password = hash_password(password)
        user_data = {
            'Full_Name': full_name,
            'Email': email,
            'Password': hashed_password,
            'Role': 'User',
            'Account_Status': 'Active',
        }

        if phone_number:
            user_data['Phone_Number'] = phone_number

        result = cloudscale_repo.create_record(TABLES['users'], user_data)

        if not result.get('success'):
            logger.error('Registration create_record failed: %s', result.get('error'))
            error_details = str(result.get('error', 'Unknown create_record error'))
            if _is_backend_setup_error(error_details):
                return jsonify({
                    'status': 'error',
                    'message': BACKEND_SETUP_MESSAGE,
                    'details': error_details,
                }), 503
            return jsonify({
                'status': 'error',
                'message': 'Registration failed',
                'details': error_details,
            }), 500

        user_id = result.get('data', {}).get('ROWID')

        # Create session
        session_id, csrf_token = create_session(
            user_id=user_id,
            user_email=email,
            user_role='User',
            ip_address=_get_client_ip(),
            user_agent=_get_user_agent(),
            device_fingerprint=_extract_device_fingerprint()
        )

        user_response = {
            'id': user_id,
            'fullName': full_name,
            'email': email,
            'phoneNumber': phone_number,
            'role': 'User',
            'accountStatus': 'Active',
        }

        # Build response with session cookie
        response = make_response(jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'data': {
                'user': user_response,
                'csrfToken': csrf_token,
            }
        }), 201)

        _set_session_cookie(response, session_id)
        return response

    except Exception as e:
        logger.exception(f'Session registration error: {e}')
        return jsonify({'status': 'error', 'message': 'Registration failed'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN (Session-based)
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/login', methods=['POST'])
@rate_limit(max_calls=10, window_seconds=900)
def session_login():
    """
    Login with email and password.
    
    Creates server-side session, sets HttpOnly cookie, returns CSRF token.
    """
    cloudscale_ok, cloudscale_error = _probe_cloudscale_connection()
    if not cloudscale_ok and _is_backend_setup_error(cloudscale_error):
        return jsonify({
            'status': 'error',
            'message': BACKEND_SETUP_MESSAGE,
            'details': cloudscale_error,
        }), 503

    data = _extract_payload()

    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400

    try:
        # Find user
        user = cloudscale_repo.get_user_by_email(email)
        if not user:
            # Log failed login attempt (user not found)
            log_audit_event(
                event_type="LOGIN_FAILED",
                user_email=email,
                ip_address=_get_client_ip(),
                details={"reason": "user_not_found"},
                severity="WARNING"
            )
            return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

        # Verify password
        stored_hash = user.get('Password', '')
        if not verify_password(password, stored_hash):
            # Log failed login attempt (wrong password)
            log_audit_event(
                event_type="LOGIN_FAILED",
                user_email=email,
                user_id=user.get('ROWID', ''),
                ip_address=_get_client_ip(),
                details={"reason": "invalid_password"},
                severity="WARNING"
            )
            return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

        # Check account status
        account_status = user.get('Account_Status', 'Active')
        if account_status == 'Blocked':
            log_audit_event(
                event_type="LOGIN_BLOCKED",
                user_email=email,
                user_id=user.get('ROWID', ''),
                ip_address=_get_client_ip(),
                details={"reason": "account_blocked"},
                severity="WARNING"
            )
            return jsonify({'status': 'error', 'message': 'Account is blocked. Contact support.'}), 403
        if account_status == 'Suspended':
            log_audit_event(
                event_type="LOGIN_BLOCKED",
                user_email=email,
                user_id=user.get('ROWID', ''),
                ip_address=_get_client_ip(),
                details={"reason": "account_suspended"},
                severity="WARNING"
            )
            return jsonify({'status': 'error', 'message': 'Account is suspended. Contact support.'}), 403

        user_id = user.get('ROWID')
        role = user.get('Role', 'User')

        # Create session (enforces concurrent session limit)
        session_id, csrf_token = create_session(
            user_id=user_id,
            user_email=email,
            user_role=role,
            ip_address=_get_client_ip(),
            user_agent=_get_user_agent(),
            device_fingerprint=_extract_device_fingerprint()
        )

        user_response = _build_user_response(user)

        # Build response with session cookie
        response = make_response(jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'user': user_response,
                'csrfToken': csrf_token,
            }
        }), 200)

        _set_session_cookie(response, session_id)
        return response

    except Exception as e:
        logger.exception(f'Session login error: {e}')
        return jsonify({'status': 'error', 'message': 'Login failed'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  LOGOUT (Session-based)
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/logout', methods=['POST'])
def session_logout():
    """
    Logout user by revoking server-side session.
    
    Clears session from database and removes cookie.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    
    if session_id:
        # Revoke session in database
        revoke_session(session_id)
        logger.info(f"Session logged out: {session_id[:8]}...")

    # Build response with cleared cookie
    response = make_response(jsonify({
        'status': 'success',
        'message': 'Logged out successfully'
    }), 200)

    _clear_session_cookie(response)
    return response


# ══════════════════════════════════════════════════════════════════════════════
#  VALIDATE SESSION
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/validate', methods=['GET'])
@require_session
def session_validate():
    """
    Validate current session and return user data.
    
    Also returns CSRF token for subsequent requests.
    """
    user_id = get_current_user_id()

    try:
        result = cloudscale_repo.get_record_by_id(TABLES['users'], user_id)

        if not result.get('success') or not result.get('data'):
            return jsonify({'status': 'error', 'message': 'User not found'}), 401

        user = result['data']
        account_status = user.get('Account_Status', 'Active')

        if account_status != 'Active':
            return jsonify({'status': 'error', 'message': 'Account is not active'}), 403

        user_response = _build_user_response(user)

        return jsonify({
            'status': 'success',
            'data': {
                'user': user_response,
                'csrfToken': get_current_csrf_token(),
            }
        }), 200

    except Exception as e:
        logger.exception(f'Session validate error: {e}')
        return jsonify({'status': 'error', 'message': 'Session validation failed'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  UPDATE PROFILE (Session-based)
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/profile', methods=['PUT'])
@require_session
def session_update_profile():
    """Update user profile."""
    user_id = get_current_user_id()
    data = _extract_payload()

    try:
        update_data = {}

        # Map fields
        field_mapping = {
            'fullName': 'Full_Name',
            'phoneNumber': 'Phone_Number',
            'dateOfBirth': 'Date_of_Birth',
            'address': 'Address',
        }

        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['users'], user_id, update_data)

        if not result.get('success'):
            return jsonify({'status': 'error', 'message': 'Failed to update profile'}), 500

        # Invalidate cache
        cloudscale_repo.invalidate_user_cache(user_id)

        # Fetch updated user
        user_result = cloudscale_repo.get_record_by_id(TABLES['users'], user_id)
        user_response = _build_user_response(user_result.get('data', {})) if user_result.get('success') else {}

        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully',
            'data': {
                'user': user_response
            }
        }), 200

    except Exception as e:
        logger.exception(f'Profile update error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to update profile'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  CHANGE PASSWORD (Session-based, revokes all sessions)
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/change-password', methods=['POST'])
@require_session
def session_change_password():
    """
    Change user password.
    
    Revokes all other sessions for security (forces re-login on other devices).
    """
    user_id = get_current_user_id()
    user_email = get_current_user_email()
    current_session = get_current_session_id()
    data = _extract_payload()

    current_password = data.get('currentPassword') or data.get('old_password') or ''
    new_password = data.get('newPassword') or data.get('new_password') or ''

    if not current_password or not new_password:
        return jsonify({'status': 'error', 'message': 'Current and new passwords are required'}), 400

    if len(new_password) < 8:
        return jsonify({'status': 'error', 'message': 'New password must be at least 8 characters'}), 400

    try:
        # Get user
        result = cloudscale_repo.get_record_by_id(TABLES['users'], user_id)
        if not result.get('success') or not result.get('data'):
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        user = result['data']

        # Verify current password
        if not verify_password(current_password, user.get('Password', '')):
            log_audit_event(
                event_type="PASSWORD_CHANGE_FAILED",
                user_email=user_email,
                user_id=user_id,
                ip_address=_get_client_ip(),
                session_id=current_session,
                details={"reason": "wrong_current_password"},
                severity="WARNING"
            )
            return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 401

        # Update password
        new_hash = hash_password(new_password)
        cloudscale_repo.update_record(TABLES['users'], user_id, {'Password': new_hash})

        # Revoke all OTHER sessions (keep current session)
        revoked_count = revoke_all_user_sessions(user_id, exclude_session=current_session)

        # Log password change
        log_audit_event(
            event_type="PASSWORD_CHANGED",
            user_email=user_email,
            user_id=user_id,
            ip_address=_get_client_ip(),
            session_id=current_session,
            details={"revoked_sessions": revoked_count},
            severity="INFO"
        )

        # Invalidate cache
        cloudscale_repo.invalidate_user_cache(user_id)

        logger.info(f"Password changed for user {user_id}, revoked {revoked_count} other sessions")

        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully. Other devices have been logged out.',
            'data': {
                'revokedSessions': revoked_count
            }
        }), 200

    except Exception as e:
        logger.exception(f'Change password error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to change password'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION MANAGEMENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/sessions', methods=['GET'])
@require_session
def list_sessions():
    """
    List all active sessions for the current user.
    
    Allows users to see which devices are logged in.
    """
    user_id = get_current_user_id()
    current_session = get_current_session_id()

    try:
        sessions = get_user_sessions(user_id)
        
        # Mark current session
        for session in sessions:
            session['is_current'] = (session['session_id'] == current_session)
            # Mask session ID for security (only show last 8 chars)
            session['session_id'] = f"...{session['session_id'][-8:]}"

        return jsonify({
            'status': 'success',
            'data': {
                'sessions': sessions,
                'totalCount': len(sessions),
            }
        }), 200

    except Exception as e:
        logger.exception(f'List sessions error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to list sessions'}), 500


@session_auth_bp.route('/session/sessions/<session_suffix>/revoke', methods=['POST'])
@require_session
def revoke_user_session(session_suffix: str):
    """
    Revoke a specific session by its suffix.
    
    Users can log out other devices.
    """
    user_id = get_current_user_id()
    current_session = get_current_session_id()

    try:
        # Find session matching suffix
        sessions = get_user_sessions(user_id)
        target_session = None
        
        for session in sessions:
            if session['session_id'].endswith(session_suffix):
                target_session = session['session_id']
                break

        if not target_session:
            return jsonify({'status': 'error', 'message': 'Session not found'}), 404

        # Don't allow revoking current session via this endpoint
        if target_session == current_session:
            return jsonify({'status': 'error', 'message': 'Cannot revoke current session. Use logout instead.'}), 400

        # Revoke the session
        success = revoke_session(target_session, user_id)

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Session revoked successfully'
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to revoke session'}), 500

    except Exception as e:
        logger.exception(f'Revoke session error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to revoke session'}), 500


@session_auth_bp.route('/session/sessions/revoke-all', methods=['POST'])
@require_session
def revoke_all_sessions():
    """
    Revoke all sessions except current.
    
    Logs out all other devices.
    """
    user_id = get_current_user_id()
    current_session = get_current_session_id()

    try:
        revoked_count = revoke_all_user_sessions(user_id, exclude_session=current_session)

        return jsonify({
            'status': 'success',
            'message': f'Revoked {revoked_count} session(s)',
            'data': {
                'revokedCount': revoked_count
            }
        }), 200

    except Exception as e:
        logger.exception(f'Revoke all sessions error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to revoke sessions'}), 500


@session_auth_bp.route('/session/csrf-token', methods=['GET'])
@require_session
def get_csrf_token():
    """Get CSRF token for current session."""
    return jsonify({
        'status': 'success',
        'data': {
            'csrfToken': get_current_csrf_token()
        }
    }), 200


@session_auth_bp.route('/session/csrf-token/regenerate', methods=['POST'])
@require_session
def regenerate_csrf():
    """Regenerate CSRF token for current session."""
    session_id = get_current_session_id()
    
    try:
        new_token = regenerate_csrf_token(session_id)
        
        if new_token:
            return jsonify({
                'status': 'success',
                'data': {
                    'csrfToken': new_token
                }
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to regenerate CSRF token'}), 500

    except Exception as e:
        logger.exception(f'CSRF regenerate error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to regenerate CSRF token'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN SESSION MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@session_auth_bp.route('/session/admin/sessions', methods=['GET'])
@require_session_admin
def admin_list_all_sessions():
    """List all active sessions (admin only)."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        sessions = get_all_active_sessions(limit=min(limit, 1000), offset=offset)
        stats = get_session_stats()

        return jsonify({
            'status': 'success',
            'data': {
                'sessions': sessions,
                'stats': stats,
            }
        }), 200

    except Exception as e:
        logger.exception(f'Admin list sessions error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to list sessions'}), 500


@session_auth_bp.route('/session/admin/sessions/<session_id>/revoke', methods=['POST'])
@require_session_admin
def admin_force_revoke_session(session_id: str):
    """Force revoke any session (admin only)."""
    admin_id = get_current_user_id()

    try:
        success = admin_revoke_session(session_id, admin_id)

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Session revoked by admin'
            }), 200
        else:
            return jsonify({'status': 'error', 'message': 'Session not found or already revoked'}), 404

    except Exception as e:
        logger.exception(f'Admin revoke session error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to revoke session'}), 500


@session_auth_bp.route('/session/admin/users/<user_id>/sessions/revoke-all', methods=['POST'])
@require_session_admin
def admin_revoke_user_sessions(user_id: str):
    """Revoke all sessions for a specific user (admin only)."""
    try:
        revoked_count = revoke_all_user_sessions(user_id)

        return jsonify({
            'status': 'success',
            'message': f'Revoked {revoked_count} session(s) for user {user_id}',
            'data': {
                'revokedCount': revoked_count
            }
        }), 200

    except Exception as e:
        logger.exception(f'Admin revoke user sessions error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to revoke sessions'}), 500


@session_auth_bp.route('/session/admin/cleanup', methods=['POST'])
@require_session_admin
def admin_cleanup_sessions():
    """Trigger cleanup of expired sessions (admin only)."""
    try:
        cleaned_count = cleanup_expired_sessions()

        return jsonify({
            'status': 'success',
            'message': f'Cleaned up {cleaned_count} expired session(s)',
            'data': {
                'cleanedCount': cleaned_count
            }
        }), 200

    except Exception as e:
        logger.exception(f'Admin cleanup sessions error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to cleanup sessions'}), 500


@session_auth_bp.route('/session/admin/stats', methods=['GET'])
@require_session_admin
def admin_session_stats():
    """Get session statistics (admin only)."""
    try:
        stats = get_session_stats()

        return jsonify({
            'status': 'success',
            'data': stats
        }), 200

    except Exception as e:
        logger.exception(f'Admin session stats error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get stats'}), 500
