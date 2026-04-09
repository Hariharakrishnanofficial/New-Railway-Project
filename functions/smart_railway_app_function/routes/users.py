""" 
Users Routes - User management CRUD operations.

This module uses the **session-based auth system** (HttpOnly cookie + CSRF) via
`core.session_middleware`.

Endpoints are split into:
- Passenger self-service: `/users/me` (requires passenger session)
- Admin management: `/users/*` (requires admin session)
"""

import logging

from flask import Blueprint, jsonify, make_response, request

from config import (
    TABLES,
    SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
)
from repositories.cloudscale_repository import cloudscale_repo
from core.session_middleware import (
    get_current_user_id,
    get_current_user_type,
    is_admin,
    require_session,
    require_session_admin,
)
from services.session_service import revoke_all_user_sessions

logger = logging.getLogger(__name__)
users_bp = Blueprint('users', __name__)


def _sanitize_user_row(row: dict) -> dict:
    """Remove sensitive fields from a Users row before returning it."""
    if not isinstance(row, dict):
        return {}
    cleaned = dict(row)
    cleaned.pop('Password', None)
    return cleaned


def _clear_session_cookie(response) -> None:
    """Clear the session cookie using the same cookie settings as login."""
    response.set_cookie(
        SESSION_COOKIE_NAME,
        '',
        expires=0,
        httponly=SESSION_COOKIE_HTTPONLY,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path='/',
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PASSENGER SELF-SERVICE
# ══════════════════════════════════════════════════════════════════════════════

@users_bp.route('/users/me', methods=['GET'])
@require_session
def get_current_user():
    """Get the currently authenticated passenger user's profile."""
    try:
        if get_current_user_type().lower() != 'user':
            return jsonify({
                'status': 'error',
                'code': 'USER_REQUIRED',
                'message': 'Passenger user session required'
            }), 403

        user_id = get_current_user_id()
        result = cloudscale_repo.get_record_by_id(TABLES['users'], user_id)

        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': _sanitize_user_row(result['data'])}), 200

        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    except Exception as e:
        logger.exception(f'Get current user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/me', methods=['PUT'])
@require_session
def update_current_user():
    """Update the currently authenticated passenger user's editable profile fields."""
    data = request.get_json(silent=True) or {}

    try:
        if get_current_user_type().lower() != 'user':
            return jsonify({
                'status': 'error',
                'code': 'USER_REQUIRED',
                'message': 'Passenger user session required'
            }), 403

        user_id = get_current_user_id()

        update_data = {}
        field_mapping = {
            'fullName': 'Full_Name',
            'phoneNumber': 'Phone_Number',
            'address': 'Address',
            'dateOfBirth': 'Date_of_Birth',
        }

        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['users'], user_id, update_data)
        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(user_id)
            fetch = cloudscale_repo.get_record_by_id(TABLES['users'], user_id)
            if fetch.get('success') and fetch.get('data'):
                return jsonify({'status': 'success', 'data': _sanitize_user_row(fetch['data'])}), 200
            return jsonify({'status': 'success', 'message': 'Profile updated'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to update profile'}), 500

    except Exception as e:
        logger.exception(f'Update current user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/me', methods=['DELETE'])
@require_session
def deactivate_current_user():
    """Deactivate the currently authenticated passenger user (soft delete)."""
    try:
        if get_current_user_type().lower() != 'user':
            return jsonify({
                'status': 'error',
                'code': 'USER_REQUIRED',
                'message': 'Passenger user session required'
            }), 403

        user_id = get_current_user_id()

        # Soft-deactivate the user. Login already blocks Suspended accounts.
        result = cloudscale_repo.update_record(TABLES['users'], user_id, {'Account_Status': 'Suspended'})
        if not result.get('success'):
            return jsonify({'status': 'error', 'message': 'Failed to deactivate user'}), 500

        cloudscale_repo.invalidate_user_cache(user_id)
        revoke_all_user_sessions(user_id)

        response = make_response(jsonify({'status': 'success', 'message': 'Account deactivated'}), 200)
        _clear_session_cookie(response)
        return response

    except Exception as e:
        logger.exception(f'Deactivate current user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@users_bp.route('/users', methods=['GET'])
@require_session_admin
def get_all_users():
    """Get all users (admin only)."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        result = cloudscale_repo.get_all_records(
            TABLES['users'],
            limit=limit,
            offset=offset,
            order_by='ROWID DESC'
        )

        if result.get('success'):
            users = result.get('data', {}).get('data', [])
            users = [_sanitize_user_row(u) for u in (users or [])]
            return jsonify({'status': 'success', 'data': users}), 200

        return jsonify({'status': 'error', 'message': 'Failed to fetch users'}), 500

    except Exception as e:
        logger.exception(f'Get users error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/<user_id>', methods=['GET'])
@require_session
def get_user(user_id):
    """Get a user by ID (admin or self only)."""
    try:
        current_type = get_current_user_type().lower()
        current_user_id = str(get_current_user_id() or '')
        target_id = str(user_id or '')

        allowed = is_admin() or (current_type == 'user' and current_user_id == target_id)
        if not allowed:
            return jsonify({
                'status': 'error',
                'code': 'FORBIDDEN',
                'message': 'Not allowed to access this user'
            }), 403

        result = cloudscale_repo.get_record_by_id(TABLES['users'], target_id)

        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': _sanitize_user_row(result['data'])}), 200

        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    except Exception as e:
        logger.exception(f'Get user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users', methods=['POST'])
@require_session_admin
def create_user():
    """Create a new user (admin only)."""
    from core.security import hash_password

    data = request.get_json(silent=True) or {}

    full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''
    phone_number = (data.get('phoneNumber') or data.get('Phone_Number') or '').strip()
    role = (data.get('role') or data.get('Role') or 'USER').strip().upper()
    if role not in ('USER', 'ADMIN', 'EMPLOYEE'):
        role = 'USER'

    if not full_name or not email or not password:
        return jsonify({'status': 'error', 'message': 'Full name, email, and password are required'}), 400

    try:
        existing = cloudscale_repo.get_user_by_email(email)
        if existing:
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 409

        user_data = {
            'Full_Name': full_name,
            'Email': email,
            'Password': hash_password(password),
            'Phone_Number': phone_number,
            'Role': role,
            'Account_Status': 'Active',
        }

        result = cloudscale_repo.create_record(TABLES['users'], user_data)

        if result.get('success'):
            user_data.pop('Password', None)
            user_data['ROWID'] = result.get('data', {}).get('ROWID')
            return jsonify({'status': 'success', 'data': user_data}), 201

        return jsonify({'status': 'error', 'message': 'Failed to create user'}), 500

    except Exception as e:
        logger.exception(f'Create user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/<user_id>', methods=['PUT'])
@require_session_admin
def update_user(user_id):
    """Update user (admin only)."""
    data = request.get_json(silent=True) or {}

    try:
        update_data = {}
        field_mapping = {
            'fullName': 'Full_Name',
            'phoneNumber': 'Phone_Number',
            'role': 'Role',
            'accountStatus': 'Account_Status',
            'address': 'Address',
        }

        for client_key, db_key in field_mapping.items():
            if client_key in data:
                if db_key == 'Role':
                    role_value = (data[client_key] or 'USER').strip().upper()
                    update_data[db_key] = role_value if role_value in ('USER', 'ADMIN', 'EMPLOYEE') else 'USER'
                else:
                    update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['users'], str(user_id), update_data)

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(str(user_id))
            return jsonify({'status': 'success', 'message': 'User updated'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to update user'}), 500

    except Exception as e:
        logger.exception(f'Update user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/<user_id>', methods=['DELETE'])
@require_session_admin
def delete_user(user_id):
    """Soft-delete (deactivate) a user (admin only)."""
    try:
        # Soft delete to avoid breaking linked records (bookings, passengers, etc.)
        result = cloudscale_repo.update_record(TABLES['users'], str(user_id), {'Account_Status': 'Suspended'})

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(str(user_id))
            revoke_all_user_sessions(str(user_id))
            return jsonify({'status': 'success', 'message': 'User deactivated'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to deactivate user'}), 500

    except Exception as e:
        logger.exception(f'Delete user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/<user_id>/status', methods=['PUT'])
@require_session_admin
def update_user_status(user_id):
    """Update user account status (admin only)."""
    data = request.get_json(silent=True) or {}
    status = data.get('status') or data.get('accountStatus') or ''

    if status not in ['Active', 'Blocked', 'Suspended']:
        return jsonify({'status': 'error', 'message': 'Invalid status. Must be Active, Blocked, or Suspended'}), 400

    try:
        result = cloudscale_repo.update_record(TABLES['users'], str(user_id), {'Account_Status': status})

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(str(user_id))
            if status in ('Blocked', 'Suspended'):
                revoke_all_user_sessions(str(user_id))
            return jsonify({'status': 'success', 'message': f'User status updated to {status}'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to update status'}), 500

    except Exception as e:
        logger.exception(f'Update status error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
