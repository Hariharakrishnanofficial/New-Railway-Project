"""
Auth Routes - Register, Login, Logout, Token refresh, Password management.
Uses JWT tokens with Argon2 password hashing.
"""

import logging
from datetime import datetime, timedelta
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

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


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
    data = request.get_json(silent=True)
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
            'Phone_Number': phone_number,
            'Role': 'User',
            'Account_Status': 'Active',
            'Created_At': datetime.utcnow().isoformat(),
        }

        result = cloudscale_repo.create_record(TABLES['users'], user_data)

        if not result.get('success'):
            return jsonify({'status': 'error', 'message': 'Registration failed'}), 500

        user_id = result.get('data', {}).get('ROWID')

        # Generate tokens
        access_token = generate_access_token(user_id, email, 'User')
        refresh_token = generate_refresh_token(user_id, email)

        user_response = {
            'id': user_id,
            'fullName': full_name,
            'email': email,
            'phoneNumber': phone_number,
            'role': 'User',
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
    data = request.get_json(silent=True) or {}

    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400

    try:
        # Find user
        user = cloudscale_repo.get_user_by_email(email)
        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

        # Verify password
        stored_hash = user.get('Password', '')
        if not verify_password(password, stored_hash):
            return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

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
    data = request.get_json(silent=True) or {}
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
    data = request.get_json(silent=True) or {}

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
    data = request.get_json(silent=True) or {}

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
