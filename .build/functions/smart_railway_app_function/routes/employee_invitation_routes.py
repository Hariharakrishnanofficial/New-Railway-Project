"""
Employee Invitation Routes - Smart Railway Ticketing System

Admin endpoints for managing employee invitations:
- POST /admin/employees/invite - Create employee invitation
- GET /admin/employees/invitations - List employee invitations
"""

import logging
from flask import Blueprint, jsonify, request

from core.session_middleware import (
    get_current_user_id,
    get_current_user_role,
)
from core.permission_validator import require_permission
from services.employee_invitation_service import (
    create_employee_invitation,
    list_employee_invitations,
    refresh_invitation,
    reinvite_employee,
    verify_invitation_token,
    mark_invitation_used,
)
from services.employee_service import create_employee
from core.security import hash_password
from repositories.cloudscale_repository import cloudscale_repo
from config import TABLES

logger = logging.getLogger(__name__)
employee_invitation_bp = Blueprint('employee_invitation', __name__)


@employee_invitation_bp.route('/admin/employees/invite', methods=['POST', 'OPTIONS'])
@require_permission('employees', 'invite')
def invite_employee():
    """
    Create an employee invitation and send email.
    
    Request:
        POST /admin/employees/invite
        {
            "email": "employee@example.com"
        }
    
    Response:
        {
            "status": "success",
            "message": "Employee invitation sent successfully",
            "data": {
                "invitation_id": "123",
                "email": "employee@example.com",
                "expires_at": "2026-04-10T13:43:35.426Z",
                "registration_link": "https://.../#/register?invitation=abc123"
            }
        }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    admin_user_id = get_current_user_id()
    data = request.get_json() or {}
    
    # Validate input
    email = (data.get('email') or '').strip().lower()
    role = (data.get('role') or 'Employee').strip()
    department = (data.get('department') or '').strip()
    designation = (data.get('designation') or '').strip()
    if not email:
        return jsonify({
            'status': 'error',
            'message': 'Email is required'
        }), 400
    
    if '@' not in email or '.' not in email:
        return jsonify({
            'status': 'error',
            'message': 'Please enter a valid email address'
        }), 400
    
    try:
        # Create invitation
        result = create_employee_invitation(
            admin_user_id,
            email,
            role=role,
            department=department or None,
            designation=designation or None,
        )
        
        if not result.get('success'):
            error_message = result.get('error', 'Failed to create invitation')
            return jsonify({
                'status': 'error',
                'message': error_message
            }), 400
        
        data = result['data']
        
        return jsonify({
            'status': 'success',
            'message': 'Employee invitation sent successfully',
            'data': {
                'invitation_id': data['invitation_id'],
                'email': data['email'],
                'expires_at': data['expires_at'],
                'registration_link': data['registration_link'],
                'currentUserRole': get_current_user_role()
            }
        }), 201
        
    except Exception as e:
        logger.exception(f"Error in invite_employee: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to send invitation'
        }), 500


@employee_invitation_bp.route('/admin/employees/invitations', methods=['GET'])
@require_permission('employees', 'invite')
def list_invitations():
    """
    List employee invitations created by the current admin.
    
    Response:
        {
            "status": "success",
            "data": {
                "invitations": [
                    {
                        "id": "123",
                        "email": "employee@example.com",
                        "invited_at": "2026-04-03T13:43:35.426Z",
                        "expires_at": "2026-04-10T13:43:35.426Z",
                        "is_used": false,
                        "used_at": null,
                        "registered_user_id": null,
                        "invited_by_name": "Admin User"
                    }
                ],
                "total": 1
            }
        }
    """
    admin_user_id = get_current_user_id()
    
    try:
        # Get limit from query parameter (default 50)
        limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100
        
        result = list_employee_invitations(admin_user_id, limit)
        
        if not result.get('success'):
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Failed to fetch invitations')
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': {
                **result['data'],
                'currentUserRole': get_current_user_role()
            }
        }), 200
        
    except Exception as e:
        logger.exception(f"Error in list_invitations: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to list invitations'
        }), 500


@employee_invitation_bp.route('/admin/employees/invitations/<invitation_id>', methods=['DELETE'])
@require_permission('employees', 'invite')
def cancel_invitation(invitation_id):
    """
    Cancel an employee invitation (mark as used/expired).
    
    Response:
        {
            "status": "success",
            "message": "Invitation cancelled successfully"
        }
    """
    admin_user_id = get_current_user_id()
    
    try:
        # TODO: Implement cancel invitation logic
        # For now, return not implemented
        return jsonify({
            'status': 'error',
            'message': 'Cancel invitation not yet implemented'
        }), 501
        
    except Exception as e:
        logger.exception(f"Error in cancel_invitation: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to cancel invitation'
        }), 500


@employee_invitation_bp.route('/admin/employees/invitations/<invitation_id>/refresh', methods=['POST'])
@require_permission('employees', 'invite')
def refresh_employee_invitation(invitation_id):
    admin_user_id = get_current_user_id()

    try:
        result = refresh_invitation(invitation_id, admin_user_id)
        if not result.get('success'):
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Failed to refresh invitation')
            }), 400

        return jsonify({
            'status': 'success',
            'message': 'Invitation refreshed successfully',
            'data': {
                **result['data'],
                'currentUserRole': get_current_user_role()
            }
        }), 200

    except Exception as e:
        logger.exception(f"Error in refresh_employee_invitation: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to refresh invitation'
        }), 500


@employee_invitation_bp.route('/admin/employees/invitations/<invitation_id>/reinvite', methods=['POST'])
@require_permission('employees', 'invite')
def reinvite_employee_invitation(invitation_id):
    admin_user_id = get_current_user_id()

    try:
        result = reinvite_employee(invitation_id, admin_user_id)
        if not result.get('success'):
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Failed to reinvite employee')
            }), 400

        return jsonify({
            'status': 'success',
            'message': 'Employee reinvited successfully',
            'data': {
                **result['data'],
                'currentUserRole': get_current_user_role()
            }
        }), 200

    except Exception as e:
        logger.exception(f"Error in reinvite_employee_invitation: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to reinvite employee'
        }), 500


@employee_invitation_bp.route('/employee/register', methods=['POST'])
def register_employee_from_invitation():
    """
    Register an employee using a valid invitation token.

    Request:
    {
        "invitation": "token",
        "fullName": "Jane Doe",
        "password": "StrongPassword123!",
        "phoneNumber": "+91-9876543210"
    }
    """
    data = request.get_json(silent=True) or {}
    token = (data.get('invitation') or data.get('token') or '').strip()
    full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
    password = data.get('password') or data.get('Password') or ''
    phone_number = (data.get('phoneNumber') or data.get('Phone_Number') or '').strip()

    if not token:
        return jsonify({'status': 'error', 'message': 'Invitation token is required'}), 400
    if not full_name:
        return jsonify({'status': 'error', 'message': 'Full name is required'}), 400
    if not password or len(password) < 8:
        return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400

    is_valid, invitation = verify_invitation_token(token)
    if not is_valid or not invitation:
        return jsonify({'status': 'error', 'message': 'Invitation is invalid or expired'}), 400

    email = (invitation.get('Email') or '').strip().lower()
    role = invitation.get('Role') or 'Employee'
    department = invitation.get('Department') or ''
    designation = invitation.get('Designation') or ''
    invited_by = invitation.get('Invited_By')
    invitation_id = invitation.get('ROWID')

    if cloudscale_repo.get_user_by_email(email) or cloudscale_repo.get_employee_by_email(email):
        return jsonify({'status': 'error', 'message': 'Account already exists for this email'}), 409

    user_role = 'ADMIN' if role.lower() == 'admin' else 'EMPLOYEE'
    user_data = {
        'Full_Name': full_name,
        'Email': email,
        'Password': hash_password(password),
        'Phone_Number': phone_number,
        'Role': user_role,
        'Account_Status': 'Active',
    }

    user_result = cloudscale_repo.create_record(TABLES['users'], user_data)
    if not user_result.get('success'):
        return jsonify({'status': 'error', 'message': 'Failed to create user account'}), 500

    user_id = user_result.get('data', {}).get('ROWID')

    employee_result = create_employee(
        full_name=full_name,
        email=email,
        password=password,
        role=role,
        invited_by=str(invited_by),
        invitation_id=str(invitation_id),
        user_id=str(user_id),
        phone_number=phone_number,
        department=department,
        designation=designation,
    )

    if not employee_result.get('success'):
        if user_id:
            cloudscale_repo.delete_record(TABLES['users'], str(user_id))
        return jsonify({'status': 'error', 'message': employee_result.get('error', 'Failed to create employee')}), 400

    employee_row_id = employee_result.get('data', {}).get('row_id')
    if employee_row_id:
        mark_invitation_used(token, str(employee_row_id))

    return jsonify({
        'status': 'success',
        'message': 'Employee account created successfully',
        'data': employee_result.get('data', {})
    }), 201
