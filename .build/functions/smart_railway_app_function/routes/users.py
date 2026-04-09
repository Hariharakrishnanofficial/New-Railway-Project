"""
Users Routes - User management CRUD operations.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_auth, require_admin, get_current_user_id

logger = logging.getLogger(__name__)
users_bp = Blueprint('users', __name__)


@users_bp.route('/users', methods=['GET'])
@require_admin
def get_all_users():
    """Get all users (admin only)."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        result = cloudscale_repo.get_all_records(
            TABLES['users'],
            limit=limit,
            offset=offset,
            order_by='ROWID DESC'
        )

        if result.get('success'):
            users = result.get('data', {}).get('data', [])
            # Remove passwords from response
            for user in users:
                user.pop('Password', None)
            return jsonify({'status': 'success', 'data': users}), 200

        return jsonify({'status': 'error', 'message': 'Failed to fetch users'}), 500

    except Exception as e:
        logger.exception(f'Get users error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/<user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """Get user by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['users'], user_id)

        if result.get('success') and result.get('data'):
            user = result['data']
            user.pop('Password', None)
            return jsonify({'status': 'success', 'data': user}), 200

        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    except Exception as e:
        logger.exception(f'Get user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users', methods=['POST'])
@require_admin
def create_user():
    """Create a new user (admin only)."""
    from core.security import hash_password

    data = request.get_json(silent=True) or {}

    full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''
    phone_number = (data.get('phoneNumber') or data.get('Phone_Number') or '').strip()
    role = (data.get('role') or data.get('Role') or 'User').strip()

    if not full_name or not email or not password:
        return jsonify({'status': 'error', 'message': 'Full name, email, and password are required'}), 400

    try:
        # Check if email exists
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
@require_admin
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
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['users'], user_id, update_data)

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(user_id)
            return jsonify({'status': 'success', 'message': 'User updated'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to update user'}), 500

    except Exception as e:
        logger.exception(f'Update user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/<user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """Delete user (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['users'], user_id)

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(user_id)
            return jsonify({'status': 'success', 'message': 'User deleted'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to delete user'}), 500

    except Exception as e:
        logger.exception(f'Delete user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@users_bp.route('/users/<user_id>/status', methods=['PUT'])
@require_admin
def update_user_status(user_id):
    """Update user account status (admin only)."""
    data = request.get_json(silent=True) or {}
    status = data.get('status') or data.get('accountStatus') or ''

    if status not in ['Active', 'Blocked', 'Suspended']:
        return jsonify({'status': 'error', 'message': 'Invalid status. Must be Active, Blocked, or Suspended'}), 400

    try:
        result = cloudscale_repo.update_record(TABLES['users'], user_id, {'Account_Status': status})

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(user_id)
            return jsonify({'status': 'success', 'message': f'User status updated to {status}'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to update status'}), 500

    except Exception as e:
        logger.exception(f'Update status error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
