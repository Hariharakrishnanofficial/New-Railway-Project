"""
Admin Users Routes - Admin user management.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES, ADMIN_DOMAIN
from core.security import hash_password
from core.session_middleware import require_session_admin

logger = logging.getLogger(__name__)
admin_users_bp = Blueprint('admin_users', __name__)


@admin_users_bp.route('/admin/users', methods=['GET'])
@require_session_admin
def get_admin_users():
    """Get all admin users."""
    try:
        criteria = CriteriaBuilder().is_in('Role', ['Admin', 'ADMIN']).build()
        result = cloudscale_repo.get_all_records(TABLES['users'], criteria=criteria, limit=100)

        if result.get('success'):
            users = result.get('data', {}).get('data', [])
            # Remove passwords
            for user in users:
                user.pop('Password', None)
            return jsonify({'status': 'success', 'data': users}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch admin users'}), 500
    except Exception as e:
        logger.exception(f'Get admin users error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users', methods=['POST'])
@require_session_admin
def create_admin_user():
    """Create a new admin user."""
    data = request.get_json(silent=True) or {}

    full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''

    if not full_name or not email or not password:
        return jsonify({'status': 'error', 'message': 'Full name, email, and password are required'}), 400

    # Optionally enforce admin domain
    if ADMIN_DOMAIN and not email.endswith('@' + ADMIN_DOMAIN):
        return jsonify({'status': 'error', 'message': f'Admin email must end with @{ADMIN_DOMAIN}'}), 400

    try:
        # Check if email exists
        existing = cloudscale_repo.get_user_by_email(email)
        if existing:
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 409

        user_data = {
            'Full_Name': full_name,
            'Email': email,
            'Password': hash_password(password),
            'Role': 'ADMIN',
            'Account_Status': 'Active',
        }

        result = cloudscale_repo.create_record(TABLES['users'], user_data)

        if result.get('success'):
            user_data.pop('Password', None)
            user_data['ROWID'] = result.get('data', {}).get('ROWID')
            return jsonify({'status': 'success', 'data': user_data}), 201

        return jsonify({'status': 'error', 'message': 'Failed to create admin user'}), 500

    except Exception as e:
        logger.exception(f'Create admin user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users/<user_id>', methods=['PUT'])
@require_session_admin
def update_admin_user(user_id):
    """Update an admin user."""
    data = request.get_json(silent=True) or {}

    try:
        update_data = {}
        if 'fullName' in data:
            update_data['Full_Name'] = data['fullName']
        if 'accountStatus' in data:
            update_data['Account_Status'] = data['accountStatus']
        if 'password' in data and data['password']:
            update_data['Password'] = hash_password(data['password'])

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['users'], user_id, update_data)

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(user_id)
            return jsonify({'status': 'success', 'message': 'Admin user updated'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to update admin user'}), 500

    except Exception as e:
        logger.exception(f'Update admin user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users/<user_id>', methods=['DELETE'])
@require_session_admin
def delete_admin_user(user_id):
    """Delete an admin user."""
    try:
        result = cloudscale_repo.delete_record(TABLES['users'], user_id)

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(user_id)
            return jsonify({'status': 'success', 'message': 'Admin user deleted'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to delete admin user'}), 500

    except Exception as e:
        logger.exception(f'Delete admin user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users/<user_id>/promote', methods=['POST'])
@require_session_admin
def promote_to_admin(user_id):
    """Promote a regular user to admin."""
    try:
        result = cloudscale_repo.update_record(TABLES['users'], user_id, {'Role': 'ADMIN'})

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(user_id)
            return jsonify({'status': 'success', 'message': 'User promoted to admin'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to promote user'}), 500

    except Exception as e:
        logger.exception(f'Promote user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users/<user_id>/demote', methods=['POST'])
@require_session_admin
def demote_from_admin(user_id):
    """Demote an admin to regular user."""
    try:
        result = cloudscale_repo.update_record(TABLES['users'], user_id, {'Role': 'USER'})

        if result.get('success'):
            cloudscale_repo.invalidate_user_cache(user_id)
            return jsonify({'status': 'success', 'message': 'Admin demoted to user'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to demote admin'}), 500

    except Exception as e:
        logger.exception(f'Demote admin error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
