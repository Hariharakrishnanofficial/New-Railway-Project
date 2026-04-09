"""
Auth Routes - Register, Login, Logout, Token refresh, Password management.
Uses JWT tokens with Argon2 password hashing.
"""

import logging
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import (
    hash_password,
    verify_password,
    generate_access_token,
    generate_refresh_token,
    decode_token,
    rate_limit,
    require_auth,
    get_current_user_id,
)
from core.exceptions import (
    AuthenticationError,
    ValidationError,
    UserNotFoundError,
    DuplicateEmailError,
)
from services.otp_service import send_password_reset_otp, verify_password_reset_otp

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)
BACKEND_SETUP_MESSAGE = 'Backend setup issue detected. Run catalyst login and restart catalyst serve.'

# Rate limiting configuration for forgot password
RATE_LIMIT_FORGOT_PASSWORD = int(os.getenv('RATE_LIMIT_FORGOT_PASSWORD', '5'))
RATE_LIMIT_FORGOT_PASSWORD_WINDOW = int(os.getenv('RATE_LIMIT_FORGOT_PASSWORD_WINDOW', '3600'))


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


def _probe_cloudscale_connection() -> tuple[bool, str]:
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


# ══════════════════════════════════════════════════════════════════════════════
#  REGISTER
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/register', methods=['POST'])
@rate_limit(max_calls=10, window_seconds=3600)
def register():
    """Register a new user account."""

    cloudscale_ok, cloudscale_error = _probe_cloudscale_connection()
    if not cloudscale_ok and _is_backend_setup_error(cloudscale_error):
        return jsonify({
            'status': 'error',
            'message': BACKEND_SETUP_MESSAGE,
            'details': cloudscale_error,
        }), 503

    data = _extract_payload()
    logger.debug('Auth register payload received')

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
            'Role': 'USER',
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

        # Generate tokens
        access_token = generate_access_token(user_id, email, 'User')
        refresh_token = generate_refresh_token(user_id, email)

        user_response = {
            'id': user_id,
            'fullName': full_name,
            'email': email,
            'phoneNumber': phone_number,
            'role': 'USER',
            'accountStatus': 'Active',
        }

        return jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'data': {
                'user': user_response,
                'token': access_token,
                'refreshToken': refresh_token,
            }
        }), 201

    except Exception as e:
        logger.exception(f'Registration error: {e}')
        return jsonify({'status': 'error', 'message': 'Registration failed'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/login', methods=['POST'])
@rate_limit(max_calls=10, window_seconds=900)
def login():
    """Login with email and password."""

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
            return jsonify({'status': 'error', 'message': 'No account found with this email address. Please check your email or register for a new account.'}), 404

        # Verify password
        stored_hash = user.get('Password', '')
        if not verify_password(password, stored_hash):
            return jsonify({'status': 'error', 'message': 'Invalid password'}), 401

        # Check account status
        account_status = user.get('Account_Status', 'Active')
        if account_status == 'Blocked':
            return jsonify({'status': 'error', 'message': 'Account is blocked. Contact support.'}), 403
        if account_status == 'Suspended':
            return jsonify({'status': 'error', 'message': 'Account is suspended. Contact support.'}), 403

        user_id = user.get('ROWID')
        role = user.get('Role', 'User')

        # Generate tokens
        access_token = generate_access_token(user_id, email, role)
        refresh_token = generate_refresh_token(user_id, email)

        user_response = _build_user_response(user)

        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'user': user_response,
                'token': access_token,
                'refreshToken': refresh_token,
            }
        }), 200

    except Exception as e:
        logger.exception(f'Login error: {e}')
        return jsonify({'status': 'error', 'message': 'Login failed'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  LOGOUT
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user (client should discard tokens)."""
    return jsonify({
        'status': 'success',
        'message': 'Logged out successfully'
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
#  VALIDATE SESSION
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/validate', methods=['GET'])
@require_auth
def validate_session():
    """Validate current JWT token and return user data."""
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
                'user': user_response
            }
        }), 200

    except Exception as e:
        logger.exception(f'Validate session error: {e}')
        return jsonify({'status': 'error', 'message': 'Session validation failed'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  REFRESH TOKEN
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token."""
    data = _extract_payload()
    refresh_token_str = (data.get('refreshToken') or data.get('refresh_token') or '').strip()

    if not refresh_token_str:
        return jsonify({'status': 'error', 'message': 'Refresh token is required'}), 400

    payload = decode_token(refresh_token_str)
    if not payload or payload.get('type') != 'refresh':
        return jsonify({'status': 'error', 'message': 'Invalid or expired refresh token'}), 401

    user_id = payload.get('sub', '')
    email = payload.get('email', '')

    # Fetch user to get current role
    user = cloudscale_repo.get_user_cached(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    role = user.get('Role', 'User')
    new_access_token = generate_access_token(user_id, email, role)

    return jsonify({
        'status': 'success',
        'data': {
            'token': new_access_token,
            'tokenType': 'Bearer',
            'expiresIn': 3600,
        }
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
#  UPDATE PROFILE
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/profile', methods=['PUT'])
@require_auth
def update_profile():
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
#  CHANGE PASSWORD
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password."""
    user_id = get_current_user_id()
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
            return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 401

        # Update password
        new_hash = hash_password(new_password)
        cloudscale_repo.update_record(TABLES['users'], user_id, {'Password': new_hash})

        # Generate new token
        email = user.get('Email', '')
        role = user.get('Role', 'User')
        new_token = generate_access_token(user_id, email, role)

        # Invalidate cache
        cloudscale_repo.invalidate_user_cache(user_id)

        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully',
            'data': {
                'token': new_token
            }
        }), 200

    except Exception as e:
        logger.exception(f'Change password error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to change password'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  SETUP ADMIN (First-time setup, no auth required)
# ══════════════════════════════════════════════════════════════════════════════

SETUP_KEY = os.getenv('ADMIN_SETUP_KEY', 'railway2026')


@auth_bp.route('/auth/setup-admin', methods=['POST'])
@rate_limit(max_calls=5, window_seconds=3600)
def setup_admin():
    """
    Create the first admin account. Requires a setup key for security.
    Only works if no admin exists yet (or with valid setup key).
    """
    data = _extract_payload()

    setup_key = (data.get('setupKey') or data.get('setup_key') or '').strip()
    full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''
    phone_number = (data.get('phoneNumber') or data.get('Phone_Number') or '').strip()

    # Validate setup key
    if setup_key != SETUP_KEY:
        return jsonify({'status': 'error', 'message': 'Invalid setup key'}), 403

    # Validate inputs
    if not full_name:
        return jsonify({'status': 'error', 'message': 'Full name is required'}), 400
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    if not password or len(password) < 8:
        return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400

    try:
        # Check if email already exists
        existing = cloudscale_repo.get_user_by_email(email)
        if existing:
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 409

        # Check if any admin exists
        criteria = CriteriaBuilder().is_in('Role', ['Admin', 'ADMIN']).build()
        admin_check = cloudscale_repo.execute_query(
            f"SELECT COUNT(ROWID) as count FROM {TABLES['users']} WHERE Role IN ('Admin', 'ADMIN')"
        )
        admin_count = 0
        if admin_check.get('success'):
            rows = admin_check.get('data', {}).get('data', [])
            if rows:
                admin_count = rows[0].get('count', 0) or 0

        # Create admin user
        user_data = {
            'Full_Name': full_name,
            'Email': email,
            'Password': hash_password(password),
            'Role': 'ADMIN',
            'Account_Status': 'Active',
        }
        if phone_number:
            user_data['Phone_Number'] = phone_number

        result = cloudscale_repo.create_record(TABLES['users'], user_data)

        if not result.get('success'):
            return jsonify({'status': 'error', 'message': 'Failed to create admin'}), 500

        user_id = result.get('data', {}).get('ROWID')

        # Generate tokens
        access_token = generate_access_token(user_id, email, 'ADMIN')
        refresh_token = generate_refresh_token(user_id, email)

        user_response = {
            'id': user_id,
            'fullName': full_name,
            'email': email,
            'phoneNumber': phone_number,
            'role': 'ADMIN',
            'accountStatus': 'Active',
        }

        logger.info(f'Admin account created: {email} (total admins: {admin_count + 1})')

        return jsonify({
            'status': 'success',
            'message': 'Admin account created successfully',
            'data': {
                'user': user_response,
                'token': access_token,
                'refreshToken': refresh_token,
            }
        }), 201

    except Exception as e:
        logger.exception(f'Setup admin error: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to create admin'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  FORGOT PASSWORD
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/forgot-password', methods=['POST'])
@rate_limit(max_calls=RATE_LIMIT_FORGOT_PASSWORD, window_seconds=RATE_LIMIT_FORGOT_PASSWORD_WINDOW)
def forgot_password():
    """
    Request a password reset. Sends OTP to user's email.
    """
    data = _extract_payload()
    email = (data.get('email') or data.get('Email') or '').strip().lower()

    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400

    try:
        # Find user - check if email exists
        user = cloudscale_repo.get_user_by_email(email)
        if not user:
            # Return clear error message for better user experience
            logger.info(f'Password reset requested for non-existent email: {email}')
            return jsonify({
                'status': 'error',
                'message': 'This email is not registered. Please sign up first or check your email address.'
            }), 404

        # Send OTP using otp_service (always track as resend)
        result = send_password_reset_otp(email, is_resend=True)
        
        if not result.get('success'):
            error = result.get('error', 'Failed to send verification code')
            cooldown = result.get('cooldown')
            limit_exceeded = result.get('limit_exceeded')
            
            if limit_exceeded:
                return jsonify({
                    'status': 'error',
                    'message': error,
                    'limit_exceeded': True
                }), 429
            
            if cooldown:
                return jsonify({
                    'status': 'error',
                    'message': error,
                    'cooldown': cooldown
                }), 429
            
            return jsonify({'status': 'error', 'message': error}), 500

        logger.info(f'Password reset OTP sent to: {email}')

        return jsonify({
            'status': 'success',
            'message': 'Verification code sent to your email',
            'expiresInMinutes': result.get('expiresInMinutes', 10),
            'remaining_resend_attempts': result.get('remaining_resend_attempts', 2)
        }), 200

    except Exception as e:
        logger.exception(f'Forgot password error: {e}')
        return jsonify({'status': 'error', 'message': 'Request failed'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  RESET PASSWORD
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/reset-password', methods=['POST'])
@rate_limit(max_calls=10, window_seconds=3600)
def reset_password():
    """
    Reset password using OTP verification.
    """
    data = _extract_payload()

    otp = (data.get('otp') or data.get('code') or data.get('token') or '').strip()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    new_password = data.get('newPassword') or data.get('new_password') or data.get('password') or ''

    if not otp:
        return jsonify({'status': 'error', 'message': 'Verification code is required'}), 400
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    if not new_password or len(new_password) < 8:
        return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400

    try:
        # Verify OTP
        is_valid, message = verify_password_reset_otp(email, otp)
        
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400

        # Find and update user
        user = cloudscale_repo.get_user_by_email(email)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        user_id = user.get('ROWID')
        new_hash = hash_password(new_password)

        # Update password
        cloudscale_repo.update_record(TABLES['users'], user_id, {'Password': new_hash})
        cloudscale_repo.invalidate_user_cache(user_id)

        logger.info(f'Password reset successful for: {email}')

        return jsonify({
            'status': 'success',
            'message': 'Password reset successfully. Please login with your new password.'
        }), 200

    except Exception as e:
        logger.exception(f'Reset password error: {e}')
        return jsonify({'status': 'error', 'message': 'Password reset failed'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  TEST TOKEN (Development only)
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/auth/test-token', methods=['GET'])
def test_token():
    """Verify JWT token is valid (development endpoint)."""
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return jsonify({'status': 'error', 'message': 'No token provided'}), 401

    token = auth_header[7:]
    payload = decode_token(token)

    if not payload:
        return jsonify({'status': 'error', 'message': 'Invalid or expired token'}), 401

    return jsonify({
        'status': 'success',
        'message': 'Token is valid',
        'data': {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role'),
            'exp': payload.get('exp'),
        }
    }), 200
