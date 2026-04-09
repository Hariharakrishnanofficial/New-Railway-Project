"""
Data Seeding Routes - Create initial/test data in CloudScale.
"""

import logging
from flask import Blueprint, jsonify

from repositories.cloudscale_repository import cloudscale_repo
from config import TABLES
from core.security import hash_password, generate_access_token, generate_refresh_token

logger = logging.getLogger(__name__)
seed_bp = Blueprint('seed', __name__)


@seed_bp.route('/seed/user', methods=['POST'])
def seed_test_user():
    """Create test user: agent@agent.com / agent@agent.com"""
    try:
        test_email = 'agent@agent.com'
        test_password = 'agent@agent.com'

        existing = cloudscale_repo.get_user_by_email(test_email)

        if existing:
            user_id = existing.get('ROWID')
            role = existing.get('Role', 'User')
            access_token = generate_access_token(user_id, test_email, role)
            refresh_token = generate_refresh_token(user_id, test_email)

            return jsonify({
                'status': 'success',
                'message': 'User already exists',
                'data': {
                    'user': {
                        'id': user_id,
                        'fullName': existing.get('Full_Name'),
                        'email': existing.get('Email'),
                        'role': existing.get('Role'),
                    },
                    'token': access_token,
                    'refreshToken': refresh_token,
                    'created': False,
                }
            }), 200

        hashed_password = hash_password(test_password)

        user_data = {
            'Full_Name': 'Agent User',
            'Email': test_email,
            'Password': hashed_password,
            'Phone_Number': '9876543210',
            'Role': 'User',
            'Account_Status': 'Active',
        }

        result = cloudscale_repo.create_record(TABLES['users'], user_data)

        if not result.get('success'):
            return jsonify({
                'status': 'error',
                'message': 'Failed to create user',
                'error': result.get('error')
            }), 500

        user_id = result.get('data', {}).get('ROWID')
        access_token = generate_access_token(user_id, test_email, 'User')
        refresh_token = generate_refresh_token(user_id, test_email)

        return jsonify({
            'status': 'success',
            'message': 'Test user created successfully',
            'data': {
                'user': {
                    'id': user_id,
                    'fullName': 'Agent User',
                    'email': test_email,
                    'role': 'User',
                },
                'credentials': {
                    'email': test_email,
                    'password': test_password,
                },
                'token': access_token,
                'refreshToken': refresh_token,
                'created': True,
            }
        }), 201

    except Exception as e:
        logger.exception(f'Seed user error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to seed user',
            'error': str(e)
        }), 500


@seed_bp.route('/seed/admin', methods=['POST'])
def seed_admin_user():
    """Create admin user: admin@railway.com / admin@railway.com"""
    try:
        admin_email = 'admin@railway.com'
        admin_password = 'admin@railway.com'

        existing = cloudscale_repo.get_user_by_email(admin_email)

        if existing:
            user_id = existing.get('ROWID')
            access_token = generate_access_token(user_id, admin_email, 'Admin')
            refresh_token = generate_refresh_token(user_id, admin_email)

            return jsonify({
                'status': 'success',
                'message': 'Admin user already exists',
                'data': {
                    'user': {
                        'id': user_id,
                        'fullName': existing.get('Full_Name'),
                        'email': existing.get('Email'),
                        'role': existing.get('Role'),
                    },
                    'token': access_token,
                    'refreshToken': refresh_token,
                    'created': False,
                }
            }), 200

        hashed_password = hash_password(admin_password)

        admin_data = {
            'Full_Name': 'System Administrator',
            'Email': admin_email,
            'Password': hashed_password,
            'Phone_Number': '9000000001',
            'Role': 'Admin',
            'Account_Status': 'Active',
        }

        result = cloudscale_repo.create_record(TABLES['users'], admin_data)

        if not result.get('success'):
            return jsonify({
                'status': 'error',
                'message': 'Failed to create admin',
                'error': result.get('error')
            }), 500

        user_id = result.get('data', {}).get('ROWID')
        access_token = generate_access_token(user_id, admin_email, 'Admin')
        refresh_token = generate_refresh_token(user_id, admin_email)

        return jsonify({
            'status': 'success',
            'message': 'Admin user created successfully',
            'data': {
                'user': {
                    'id': user_id,
                    'fullName': 'System Administrator',
                    'email': admin_email,
                    'role': 'Admin',
                },
                'credentials': {
                    'email': admin_email,
                    'password': admin_password,
                },
                'token': access_token,
                'refreshToken': refresh_token,
                'created': True,
            }
        }), 201

    except Exception as e:
        logger.exception(f'Seed admin error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to seed admin',
            'error': str(e)
        }), 500


@seed_bp.route('/seed/status', methods=['GET'])
def seed_status():
    """Check if seed data exists."""
    try:
        test_user = cloudscale_repo.get_user_by_email('agent@agent.com')
        admin_user = cloudscale_repo.get_user_by_email('admin@railway.com')
        user_count = cloudscale_repo.count_records(TABLES['users'])

        return jsonify({
            'status': 'success',
            'data': {
                'testUser': {
                    'exists': test_user is not None,
                    'email': 'agent@agent.com',
                    'id': test_user.get('ROWID') if test_user else None,
                },
                'adminUser': {
                    'exists': admin_user is not None,
                    'email': 'admin@railway.com',
                    'id': admin_user.get('ROWID') if admin_user else None,
                },
                'totalUsers': user_count,
            }
        }), 200

    except Exception as e:
        logger.exception(f'Seed status error: {e}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to check seed status',
            'error': str(e)
        }), 500
