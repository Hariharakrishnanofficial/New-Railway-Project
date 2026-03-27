"""
Admin Users routes — CRUD for administrator accounts (Users table with Role=Admin).
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from services.zoho_service import zoho
from repositories.cloudscale_repository import zoho_repo
from config import TABLES
from core.security import require_admin, hash_password
from utils.log_helper import log_admin_action

admin_users_bp = Blueprint('admin_users', __name__)


def _is_true(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ('true', '1', 'yes', 'active')
    if isinstance(val, (int, float)):
        return val != 0
    return bool(val)


@admin_users_bp.route('/api/admin/users', methods=['GET'])
@admin_users_bp.route('/api/admin/admin-users', methods=['GET'])
@require_admin
def list_admin_users():
    limit = request.args.get('limit', 200, type=int)
    search = request.args.get('search', '').strip().lower()

    result = zoho.get_all_records(TABLES['users'], criteria='(Role == "Admin")', limit=limit)
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)

    records = result.get('data', {}).get('data', []) or []
    if search:
        records = [
            u for u in records
            if search in (u.get('Full_Name') or '').lower()
            or search in (u.get('Email') or '').lower()
            or search in (u.get('Phone_Number') or '').lower()
        ]

    return jsonify({'success': True, 'data': {'data': records, 'count': len(records)}}), 200


@admin_users_bp.route('/api/admin/users/<admin_id>', methods=['GET'])
@admin_users_bp.route('/api/admin/admin-users/<admin_id>', methods=['GET'])
@require_admin
def get_admin_user(admin_id):
    result = zoho.get_record_by_id(TABLES['users'], admin_id)
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)

    record = result.get('data', {})
    if (record.get('Role') or '').lower() != 'admin':
        return jsonify({'success': False, 'error': 'Admin user not found'}), 404

    return jsonify({'success': True, 'data': record}), 200


@admin_users_bp.route('/api/admin/users', methods=['POST'])
@admin_users_bp.route('/api/admin/admin-users', methods=['POST'])
@require_admin
def create_admin_user():
    data = request.get_json() or {}
    full_name = (data.get('Full_Name') or '').strip()
    email = (data.get('Email') or '').strip()
    phone = (data.get('Phone_Number') or '').strip()
    password = (data.get('Password') or '').strip()

    if not all([full_name, email, phone, password]):
        missing = [f for f, v in [('Full_Name', full_name), ('Email', email), ('Phone_Number', phone), ('Password', password)] if not v]
        return jsonify({'success': False, 'error': f'Missing: {", ".join(missing)}'}), 400

    payload = {
        'Full_Name': full_name,
        'Email': email,
        'Phone_Number': phone,
        'Address': data.get('Address', ''),
        'Role': 'Admin',
        'Account_Status': data.get('Account_Status', 'Active'),
        'Date_of_Birth': data.get('Date_of_Birth') or None,
        'ID_Proof_Type': data.get('ID_Proof_Type') or None,
        'ID_Proof_Number': data.get('ID_Proof_Number') or None,
        'Aadhar_Verified': _is_true(data.get('Aadhar_Verified', False)),
        'Is_Aadhar_Verified': _is_true(data.get('Aadhar_Verified', False)),
        'Registered_Date': datetime.now().strftime('%d-%b-%Y %H:%M:%S'),
        'Password': hash_password(password),
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    result = zoho.create_record(TABLES['users'], payload)
    if result.get('success'):
        actor = request.headers.get('X-User-Email', 'Unknown')
        record_id = result.get('data', {}).get('ID')
        log_admin_action(actor, 'CREATE_ADMIN_USER', {'record_id': record_id, 'email': email})

    return jsonify(result), result.get('status_code', 200)


@admin_users_bp.route('/api/admin/users/<admin_id>', methods=['PUT'])
@admin_users_bp.route('/api/admin/admin-users/<admin_id>', methods=['PUT'])
@require_admin
def update_admin_user(admin_id):
    data = request.get_json() or {}
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    existing = zoho.get_record_by_id(TABLES['users'], admin_id)
    if not existing.get('success'):
        return jsonify(existing), existing.get('status_code', 500)
    if (existing.get('data', {}).get('Role') or '').lower() != 'admin':
        return jsonify({'success': False, 'error': 'Admin user not found'}), 404

    payload = {k: v for k, v in {
        'Full_Name': data.get('Full_Name'),
        'Email': data.get('Email'),
        'Phone_Number': data.get('Phone_Number'),
        'Address': data.get('Address'),
        'Account_Status': data.get('Account_Status'),
        'Date_of_Birth': data.get('Date_of_Birth'),
        'ID_Proof_Type': data.get('ID_Proof_Type'),
        'ID_Proof_Number': data.get('ID_Proof_Number'),
        'Aadhar_Verified': _is_true(data.get('Aadhar_Verified')) if 'Aadhar_Verified' in data else None,
        'Is_Aadhar_Verified': _is_true(data.get('Aadhar_Verified')) if 'Aadhar_Verified' in data else None,
        'Password': hash_password(data['Password']) if data.get('Password') else None,
        'Role': 'Admin',
    }.items() if v is not None}

    if not payload:
        return jsonify({'success': False, 'error': 'No valid fields to update'}), 400

    result = zoho.update_record(TABLES['users'], admin_id, payload)
    if result.get('success'):
        zoho_repo.invalidate_user_cache(admin_id)
        actor = request.headers.get('X-User-Email', 'Unknown')
        log_admin_action(actor, 'UPDATE_ADMIN_USER', {'record_id': admin_id})

    return jsonify(result), result.get('status_code', 200)


@admin_users_bp.route('/api/admin/users/<admin_id>', methods=['DELETE'])
@admin_users_bp.route('/api/admin/admin-users/<admin_id>', methods=['DELETE'])
@require_admin
def delete_admin_user(admin_id):
    existing = zoho.get_record_by_id(TABLES['users'], admin_id)
    if not existing.get('success'):
        return jsonify(existing), existing.get('status_code', 500)
    if (existing.get('data', {}).get('Role') or '').lower() != 'admin':
        return jsonify({'success': False, 'error': 'Admin user not found'}), 404

    actor_email = (request.headers.get('X-User-Email') or '').strip().lower()
    target_email = (existing.get('data', {}).get('Email') or '').strip().lower()
    if actor_email and actor_email == target_email:
        return jsonify({'success': False, 'error': 'You cannot delete your own admin account'}), 400

    result = zoho.delete_record(TABLES['users'], admin_id)
    if result.get('success'):
        zoho_repo.invalidate_user_cache(admin_id)
        actor = request.headers.get('X-User-Email', 'Unknown')
        log_admin_action(actor, 'DELETE_ADMIN_USER', {'record_id': admin_id})

    return jsonify(result), result.get('status_code', 200)
