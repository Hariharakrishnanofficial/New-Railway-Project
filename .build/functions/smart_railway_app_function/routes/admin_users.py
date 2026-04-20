"""Admin Users Routes - Manage administrator (Employees) accounts.

IMPORTANT:
- "Admin users" in this project are stored in the Employees table (Role='Admin').
- Never expose password hashes to the client.
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from config import TABLES
from core.session_middleware import get_current_user_id
from core.permission_validator import require_permission
from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from services.employee_service import create_employee, change_employee_password
from services.session_service import revoke_all_user_sessions

logger = logging.getLogger(__name__)
admin_users_bp = Blueprint('admin_users', __name__)


_ALLOWED_STATUS = {'Active', 'Suspended', 'Blocked', 'Inactive'}


def _parse_rowid(raw: str) -> int:
    try:
        rid = int(str(raw).strip())
        if rid <= 0:
            raise ValueError('ROWID must be positive')
        return rid
    except Exception:
        raise ValueError('Invalid ROWID')


def _employee_to_admin_row(emp: dict) -> dict:
    """Convert Employees row to AdminUsersPage-friendly shape (DB-style keys).

    Intentionally excludes sensitive/internal fields (especially Password hashes).
    """
    if not isinstance(emp, dict):
        return {}

    return {
        'ROWID': emp.get('ROWID'),
        'Employee_ID': emp.get('Employee_ID'),
        'Full_Name': emp.get('Full_Name'),
        'Email': emp.get('Email'),
        'Phone_Number': emp.get('Phone_Number'),
        'Role': emp.get('Role'),
        'Department': emp.get('Department'),
        'Designation': emp.get('Designation'),
        'Account_Status': emp.get('Account_Status'),
        'Is_Active': emp.get('Is_Active'),
        'Joined_At': emp.get('Joined_At'),
        'Last_Login': emp.get('Last_Login'),
        'Address': emp.get('Address'),
    }


@admin_users_bp.route('/admin/users', methods=['GET'])
@require_permission('employees', 'view')
def get_admin_users():
    """List admin employees (sanitized)."""
    try:
        status = (request.args.get('status') or '').strip()
        limit = int(request.args.get('limit', 200))
        offset = int(request.args.get('offset', 0))

        cb = CriteriaBuilder().is_in('Role', ['Admin', 'ADMIN'])
        if status:
            cb.eq('Account_Status', status)
        criteria = cb.build()

        result = cloudscale_repo.get_all_records(
            TABLES['employees'],
            criteria=criteria,
            limit=max(1, min(limit, 500)),
            offset=max(0, offset),
            order_by='ROWID DESC',
        )

        if not result.get('success'):
            return jsonify({'status': 'error', 'message': 'Failed to fetch admin users'}), 500

        employees = result.get('data', {}).get('data', []) or []
        rows = [_employee_to_admin_row(e) for e in employees]
        return jsonify({'status': 'success', 'data': rows}), 200

    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid limit or offset'}), 400
    except Exception as e:
        logger.exception(f'Get admin users error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users/<employee_row_id>', methods=['GET'])
@require_permission('employees', 'view')
def get_admin_user_details(employee_row_id):
    """Get single admin employee details (all fields except Password)."""
    try:
        rid = _parse_rowid(employee_row_id)

        # Prefer broad details, but fall back to the standard employee fetch if needed
        emp = cloudscale_repo.get_employee_details_by_id(str(rid)) or cloudscale_repo.get_employee_by_id(str(rid))
        if not emp:
            return jsonify({'status': 'error', 'message': 'Admin not found'}), 404

        if str(emp.get('Role', '')).lower() != 'admin':
            return jsonify({'status': 'error', 'message': 'Target is not an admin account'}), 400

        # Extra defense: never expose password
        emp.pop('Password', None)
        emp.pop('password', None)

        # Hide internal/metadata fields in details view
        for k in ('ROWID', 'CREATEDTIME', 'MODIFIEDTIME', 'Is_Active', 'Account_Status'):
            emp.pop(k, None)
            emp.pop(k.lower(), None)

        return jsonify({'status': 'success', 'data': emp}), 200

    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
    except Exception as e:
        logger.exception(f'Get admin user details error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users', methods=['POST'])
@require_permission('employees', 'create')
def create_admin_user():
    """Create a new admin employee."""
    data = request.get_json(silent=True) or {}

    full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''
    phone_number = (data.get('phoneNumber') or data.get('Phone_Number') or '').strip()
    department = (data.get('department') or data.get('Department') or '').strip() or None
    designation = (data.get('designation') or data.get('Designation') or '').strip() or None

    if not full_name or not email or not password:
        return jsonify({'status': 'error', 'message': 'Full name, email, and password are required'}), 400

    try:
        current_admin_id = get_current_user_id()
        if not current_admin_id:
            return jsonify({'status': 'error', 'message': 'Invalid admin session'}), 401

        create_result = create_employee(
            full_name=full_name,
            email=email,
            password=password,
            role='Admin',
            invited_by=str(current_admin_id),
            department=department,
            designation=designation,
            phone_number=phone_number or None,
        )

        if not create_result.get('success'):
            msg = create_result.get('error') or 'Failed to create admin'
            status_code = 409 if 'already exists' in msg.lower() else 400
            return jsonify({'status': 'error', 'message': msg}), status_code

        row_id = (create_result.get('data') or {}).get('row_id')
        emp = cloudscale_repo.get_employee_by_id(str(row_id)) if row_id else None
        if not emp:
            return jsonify({'status': 'success', 'message': 'Admin created', 'data': {'ROWID': row_id}}), 201

        # Optional: apply initial account status if provided
        desired_status = (data.get('accountStatus') or data.get('Account_Status') or '').strip()
        if desired_status and desired_status in _ALLOWED_STATUS and desired_status != (emp.get('Account_Status') or ''):
            # Avoid writing schema-variant fields like Updated_At (not present in some deployments).
            cloudscale_repo.update_employee(str(row_id), {
                'Account_Status': desired_status,
            })
            emp = cloudscale_repo.get_employee_by_id(str(row_id)) or emp

        return jsonify({'status': 'success', 'data': _employee_to_admin_row(emp)}), 201

    except Exception as e:
        logger.exception(f'Create admin user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users/<employee_row_id>', methods=['PUT'])
@require_permission('employees', 'edit')
def update_admin_user(employee_row_id):
    """Update an admin employee. Email/Role cannot be changed."""
    data = request.get_json(silent=True) or {}

    try:
        rid = _parse_rowid(employee_row_id)
        emp = cloudscale_repo.get_employee_by_id(str(rid))
        if not emp:
            return jsonify({'status': 'error', 'message': 'Admin not found'}), 404

        if str(emp.get('Role', '')).lower() != 'admin':
            return jsonify({'status': 'error', 'message': 'Target is not an admin account'}), 400

        incoming_email = data.get('email') or data.get('Email')
        if incoming_email is not None:
            if str(incoming_email).strip().lower() != str(emp.get('Email') or '').strip().lower():
                return jsonify({'status': 'error', 'message': 'Email cannot be changed'}), 400
        if 'role' in data or 'Role' in data:
            return jsonify({'status': 'error', 'message': 'Role cannot be changed'}), 400

        update_data = {}
        # Accept both camelCase and DB-style keys
        if 'fullName' in data or 'Full_Name' in data:
            update_data['Full_Name'] = (data.get('fullName') or data.get('Full_Name') or '').strip()
        if 'phoneNumber' in data or 'Phone_Number' in data:
            update_data['Phone_Number'] = (data.get('phoneNumber') or data.get('Phone_Number') or '').strip()
        if 'department' in data or 'Department' in data:
            update_data['Department'] = (data.get('department') or data.get('Department') or '').strip()
        if 'designation' in data or 'Designation' in data:
            update_data['Designation'] = (data.get('designation') or data.get('Designation') or '').strip()
        if 'address' in data or 'Address' in data:
            update_data['Address'] = (data.get('address') or data.get('Address') or '').strip()

        # Optional KYC-ish fields (only if present)
        if 'dateOfBirth' in data or 'Date_of_Birth' in data:
            update_data['Date_of_Birth'] = data.get('dateOfBirth') or data.get('Date_of_Birth')
        if 'aadharVerified' in data or 'Aadhar_Verified' in data:
            update_data['Aadhar_Verified'] = data.get('aadharVerified') if 'aadharVerified' in data else data.get('Aadhar_Verified')
        if 'idProofType' in data or 'ID_Proof_Type' in data:
            update_data['ID_Proof_Type'] = data.get('idProofType') or data.get('ID_Proof_Type')
        if 'idProofNumber' in data or 'ID_Proof_Number' in data:
            update_data['ID_Proof_Number'] = data.get('idProofNumber') or data.get('ID_Proof_Number')

        # Status
        if 'accountStatus' in data or 'Account_Status' in data:
            desired_status = (data.get('accountStatus') or data.get('Account_Status') or '').strip()
            if desired_status and desired_status not in _ALLOWED_STATUS:
                return jsonify({'status': 'error', 'message': 'Invalid account status'}), 400
            update_data['Account_Status'] = desired_status

        # Password reset (handled separately)
        new_password = data.get('password') or data.get('Password')
        if new_password:
            pw_res = change_employee_password(str(rid), str(new_password))
            if not pw_res.get('success'):
                return jsonify({'status': 'error', 'message': pw_res.get('error') or 'Failed to update password'}), 400

        if update_data:
            # Avoid writing schema-variant fields like Updated_At (not present in some deployments).
            result = cloudscale_repo.update_employee(str(rid), update_data)
            if not result.get('success'):
                return jsonify({'status': 'error', 'message': 'Failed to update admin'}), 500

        if not update_data and not new_password:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        emp2 = cloudscale_repo.get_employee_by_id(str(rid))
        return jsonify({'status': 'success', 'data': _employee_to_admin_row(emp2 or emp)}), 200

    except Exception as e:
        logger.exception(f'Update admin user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/admin/users/<employee_row_id>', methods=['DELETE'])
@require_permission('employees', 'deactivate')
def delete_admin_user(employee_row_id):
    """Soft-delete (deactivate) an admin employee and revoke sessions."""
    try:
        rid = _parse_rowid(employee_row_id)
        emp = cloudscale_repo.get_employee_by_id(str(rid))
        if not emp:
            return jsonify({'status': 'error', 'message': 'Admin not found'}), 404

        if str(emp.get('Role', '')).lower() != 'admin':
            return jsonify({'status': 'error', 'message': 'Target is not an admin account'}), 400

        update_res = cloudscale_repo.update_employee(str(rid), {
            'Account_Status': 'Suspended',
            'Is_Active': False,
        })

        if not update_res.get('success'):
            # Fallback for schemas without Is_Active column
            update_res = cloudscale_repo.update_employee(str(rid), {
                'Account_Status': 'Suspended',
            })

        if not update_res.get('success'):
            return jsonify({'status': 'error', 'message': 'Failed to deactivate admin'}), 500

        # Revoke all sessions for this employee
        revoke_all_user_sessions(str(rid))

        return jsonify({'status': 'success', 'message': 'Admin deactivated'}), 200

    except Exception as e:
        logger.exception(f'Delete admin user error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
