"""
Admin Employee Management Routes - Smart Railway Ticketing System

Complete CRUD operations for managing admin and employee accounts:
- POST   /admin/employees           - Create new employee (sends welcome email)
- GET    /admin/employees           - List all employees (with filters)
- GET    /admin/employees/<id>      - Get employee details
- PUT    /admin/employees/<id>      - Update employee
- DELETE /admin/employees/<id>      - Delete employee
- POST   /admin/employees/<id>/status - Change account status

Employee self-service:
- POST   /employee/password/reset-request - Request password reset OTP
- POST   /employee/password/reset         - Reset password with OTP

All admin operations require admin session authentication.
"""

import os
import secrets
import string
import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request

try:
    import zcatalyst_sdk
    CATALYST_AVAILABLE = True
except ImportError:
    CATALYST_AVAILABLE = False

from core.session_middleware import (
    require_session_admin,
    require_session_employee,
    get_current_user_id,
)
from core.security import hash_password
from services.employee_service import (
    create_employee,
    get_employee,
    update_employee,
    delete_employee,
    list_all_employees,
    get_employees_by_role,
    change_employee_password,
    DEFAULT_ADMIN_PERMISSIONS,
    DEFAULT_EMPLOYEE_PERMISSIONS,
)
from services.otp_service import (
    generate_otp,
    create_otp_record,
    verify_otp,
    send_otp_email,
)
from repositories.cloudscale_repository import cloudscale_repo
from config import TABLES

logger = logging.getLogger(__name__)
admin_employees_bp = Blueprint('admin_employees', __name__)

# Email configuration
FROM_EMAIL = os.getenv('CATALYST_FROM_EMAIL', 'noreply@smartrailway.com')
APP_NAME = os.getenv('APP_NAME', 'Smart Railway')


def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    # Ensure at least one of each type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%"),
    ]
    # Fill rest with random chars
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # Shuffle
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def send_welcome_email(email: str, full_name: str, password: str, role: str) -> dict:
    """
    Send welcome email with login credentials to new employee.
    
    Args:
        email: Employee's email address
        full_name: Employee's full name
        password: Temporary password
        role: Employee role (Admin/Employee)
    
    Returns:
        Result dict with success status
    """
    if not CATALYST_AVAILABLE:
        logger.warning("Catalyst SDK not available, simulating email send")
        logger.info(f"[DEV] Welcome email for {email}: Password={password}")
        return {'success': True, 'simulated': True}
    
    try:
        app = zcatalyst_sdk.initialize()
        mail_service = app.email()
        
        subject = f"Welcome to {APP_NAME} - Your Login Credentials"
        content = _build_welcome_email(full_name, email, password, role)
        
        mail_obj = {
            'from_email': FROM_EMAIL,
            'to_email': [email],
            'subject': subject,
            'content': content,
            'html_mode': True,
        }
        
        logger.info(f"Sending welcome email to {email}")
        response = mail_service.send_mail(mail_obj)
        logger.info(f"Welcome email sent to {email}")
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return {'success': False, 'error': str(e)}


def _build_welcome_email(full_name: str, email: str, password: str, role: str) -> str:
    """Build HTML welcome email with credentials."""
    login_url = os.getenv('APP_URL', 'https://smart-railway.onslate.in')
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #1a1a2e; margin: 0; font-size: 28px;">🚂 {APP_NAME}</h1>
        </div>
        
        <h2 style="color: #333; margin: 0 0 10px;">Welcome, {full_name}!</h2>
        <p style="color: #666; margin: 0 0 30px; line-height: 1.6;">
            Your {role} account has been created. Use the credentials below to login to the system.
        </p>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 30px; margin-bottom: 30px;">
            <h3 style="color: white; margin: 0 0 20px; font-size: 18px;">Your Login Credentials</h3>
            
            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <p style="color: rgba(255,255,255,0.8); margin: 0 0 5px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Email</p>
                <p style="color: white; margin: 0; font-size: 16px; font-weight: bold;">{email}</p>
            </div>
            
            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; padding: 15px;">
                <p style="color: rgba(255,255,255,0.8); margin: 0 0 5px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Temporary Password</p>
                <p style="color: white; margin: 0; font-size: 20px; font-weight: bold; font-family: monospace; letter-spacing: 2px;">{password}</p>
            </div>
        </div>
        
        <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin-bottom: 25px;">
            <p style="color: #856404; margin: 0; font-size: 14px;">
                ⚠️ <strong>Important:</strong> Please change your password immediately after your first login for security purposes.
            </p>
        </div>
        
        <div style="text-align: center; margin-bottom: 30px;">
            <a href="{login_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">
                Login to {APP_NAME}
            </a>
        </div>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h4 style="color: #333; margin: 0 0 10px;">Getting Started:</h4>
            <ol style="color: #666; margin: 0; padding-left: 20px; line-height: 1.8;">
                <li>Click the login button above or go to: <strong>{login_url}</strong></li>
                <li>Enter your email and temporary password</li>
                <li>Change your password to something secure</li>
                <li>Start using the system!</li>
            </ol>
        </div>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
            If you did not expect this email, please contact your administrator.<br>
            © 2026 {APP_NAME}. All rights reserved.
        </p>
    </div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
#  CREATE EMPLOYEE (Admin only) - With Welcome Email
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/admin/employees', methods=['POST'])
@require_session_admin
def create_new_employee():
    """
    Create a new employee (Admin or Employee role).
    Automatically generates a temporary password and sends welcome email.
    
    Request:
    ```json
    {
        "fullName": "John Smith",
        "email": "john@railway.com",
        "role": "Admin",
        "phoneNumber": "+91-9876543210",
        "department": "Operations",
        "designation": "Station Master"
    }
    ```
    
    Response (201):
    ```json
    {
        "status": "success",
        "message": "Employee created successfully. Welcome email sent.",
        "data": {
            "row_id": "1001",
            "employee_id": "ADM001",
            "email": "john@railway.com",
            "full_name": "John Smith",
            "role": "Admin"
        }
    }
    ```
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Validate required fields
        full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
        email = (data.get('email') or data.get('Email') or '').strip().lower()
        role = (data.get('role') or data.get('Role') or '').strip()
        
        # Password is optional - auto-generate if not provided
        password = data.get('password') or data.get('Password')
        auto_generated_password = False
        
        if not full_name:
            return jsonify({'status': 'error', 'message': 'Full name is required'}), 400
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400
        if role not in ('Admin', 'Employee'):
            return jsonify({'status': 'error', 'message': 'Role must be Admin or Employee'}), 400
        
        # Auto-generate password if not provided
        if not password:
            password = generate_temp_password(12)
            auto_generated_password = True
        
        # Get current admin's ID for invited_by (employee ROWID)
        current_admin_id = get_current_user_id()
        if not current_admin_id:
            return jsonify({'status': 'error', 'message': 'Invalid admin session'}), 401

        # Ensure user does not exist already
        existing_user = cloudscale_repo.get_user_by_email(email)
        if existing_user:
            return jsonify({'status': 'error', 'message': 'User with this email already exists'}), 409
        
        # Optional fields
        phone_number = data.get('phoneNumber') or data.get('Phone_Number')
        department = data.get('department') or data.get('Department')
        designation = data.get('designation') or data.get('Designation')
        
        user_role = 'ADMIN' if role == 'Admin' else 'EMPLOYEE'
        user_data = {
            'Full_Name': full_name,
            'Email': email,
            'Password': hash_password(password),
            'Phone_Number': phone_number or '',
            'Role': user_role,
            'Account_Status': 'Active',
        }

        user_result = cloudscale_repo.create_record(TABLES['users'], user_data)
        if not user_result.get('success'):
            return jsonify({'status': 'error', 'message': 'Failed to create user account'}), 500

        user_id = user_result.get('data', {}).get('ROWID')

        # Create employee profile
        result = create_employee(
            full_name=full_name,
            email=email,
            password=password,
            role=role,
            invited_by=current_admin_id,
            invitation_id=None,
            user_id=user_id,
            phone_number=phone_number,
            department=department,
            designation=designation
        )
        
        if result.get('success'):
            # Send welcome email with credentials
            email_result = send_welcome_email(email, full_name, password, role)
            
            response_data = result.get('data')
            message = 'Employee created successfully'
            
            if email_result.get('success'):
                message += '. Welcome email sent.'
            else:
                message += '. Note: Welcome email could not be sent.'
                logger.warning(f"Welcome email failed for {email}: {email_result.get('error')}")
            
            return jsonify({
                'status': 'success',
                'message': message,
                'data': response_data,
                'email_sent': email_result.get('success', False)
            }), 201
        
        if not result.get('success'):
            # Roll back user record if employee creation fails
            if user_id:
                cloudscale_repo.delete_record(TABLES['users'], str(user_id))

        error_msg = result.get('error', 'Failed to create employee')
        if 'already exists' in error_msg.lower():
            return jsonify({'status': 'error', 'message': error_msg}), 409
        
        return jsonify({'status': 'error', 'message': error_msg}), 400
        
    except Exception as e:
        logger.exception(f'Create employee error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  READ EMPLOYEES (List & Get)
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/admin/employees', methods=['GET'])
@require_session_admin
def list_employees():
    """
    List all employees with optional filters.
    
    Query Parameters:
    - role: "Admin" or "Employee" (filter by role)
    - status: "Active", "Inactive", "Suspended" (filter by account status)
    - department: Filter by department
    - limit: Max records to return (default: 100)
    - offset: Pagination offset (default: 0)
    
    Response (200):
    ```json
    {
        "status": "success",
        "data": [
            {
                "row_id": "1001",
                "employee_id": "ADM001",
                "full_name": "John Smith",
                "email": "john@railway.com",
                "role": "Admin",
                "department": "Operations",
                "designation": "Station Master",
                "account_status": "Active",
                "created_at": "2026-04-06T13:00:00Z"
            }
        ],
        "total": 15,
        "limit": 100,
        "offset": 0
    }
    ```
    """
    try:
        # Get filter parameters
        role_filter = request.args.get('role')
        status_filter = request.args.get('status')
        department_filter = request.args.get('department')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Validate role filter
        if role_filter and role_filter not in ('Admin', 'Employee'):
            return jsonify({'status': 'error', 'message': 'Invalid role filter'}), 400
        
        # Get employees
        if role_filter:
            result = get_employees_by_role(role_filter)
        else:
            result = list_all_employees()
        
        if not result.get('success'):
            return jsonify({'status': 'error', 'message': result.get('error')}), 500
        
        employees = result.get('data', [])
        
        # Apply additional filters
        if status_filter:
            employees = [e for e in employees if e.get('account_status') == status_filter]
        if department_filter:
            employees = [e for e in employees if e.get('department') == department_filter]
        
        # Apply pagination
        total = len(employees)
        employees = employees[offset:offset + limit]
        
        return jsonify({
            'status': 'success',
            'data': employees,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid limit or offset'}), 400
    except Exception as e:
        logger.exception(f'List employees error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_employees_bp.route('/admin/employees/<employee_id>', methods=['GET'])
@require_session_admin
def get_employee_details(employee_id):
    """
    Get detailed information about a specific employee.
    
    Response (200):
    ```json
    {
        "status": "success",
        "data": {
            "row_id": "1001",
            "employee_id": "ADM001",
            "full_name": "John Smith",
            "email": "john@railway.com",
            "phone_number": "+91-9876543210",
            "role": "Admin",
            "department": "Operations",
            "designation": "Station Master",
            "permissions": {
                "modules": {
                    "employees": ["view", "create", "edit"]
                },
                "admin_access": true
            },
            "account_status": "Active",
            "last_login": "2026-04-06T10:00:00Z",
            "joined_at": "2026-03-15T08:00:00Z",
            "created_at": "2026-03-15T08:00:00Z"
        }
    }
    ```
    """
    try:
        result = get_employee(employee_id)
        
        if not result.get('success'):
            return jsonify({'status': 'error', 'message': 'Employee not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': result.get('data')
        }), 200
        
    except Exception as e:
        logger.exception(f'Get employee error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  UPDATE EMPLOYEE
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/admin/employees/<employee_id>', methods=['PUT'])
@require_session_admin
def update_employee_details(employee_id):
    """
    Update employee details.
    
    Note: Email, Role, and Employee_ID cannot be changed.
    
    Request:
    ```json
    {
        "fullName": "John Smith Updated",
        "phoneNumber": "+91-9876543211",
        "department": "Customer Service",
        "designation": "Senior Station Master"
    }
    ```
    
    Response (200):
    ```json
    {
        "status": "success",
        "message": "Employee updated successfully"
    }
    ```
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Prevent changing email or role
        if 'email' in data or 'Email' in data:
            return jsonify({'status': 'error', 'message': 'Email cannot be changed'}), 400
        if 'role' in data or 'Role' in data:
            return jsonify({'status': 'error', 'message': 'Role cannot be changed'}), 400
        
        # Extract updateable fields
        full_name = data.get('fullName') or data.get('Full_Name')
        phone_number = data.get('phoneNumber') or data.get('Phone_Number')
        department = data.get('department') or data.get('Department')
        designation = data.get('designation') or data.get('Designation')
        account_status = data.get('accountStatus') or data.get('Account_Status')
        
        # Update employee
        result = update_employee(
            employee_row_id=employee_id,
            full_name=full_name,
            phone_number=phone_number,
            department=department,
            designation=designation,
            account_status=account_status
        )
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Employee updated successfully'
            }), 200
        
        error = result.get('error', 'Failed to update employee')
        return jsonify({'status': 'error', 'message': error}), 400
        
    except Exception as e:
        logger.exception(f'Update employee error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  DELETE EMPLOYEE
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/admin/employees/<employee_id>', methods=['DELETE'])
@require_session_admin
def delete_employee_record(employee_id):
    """
    Delete an employee record permanently.
    
    ⚠️ WARNING: This action is irreversible. Consider deactivating instead.
    
    Response (200):
    ```json
    {
        "status": "success",
        "message": "Employee deleted successfully"
    }
    ```
    """
    try:
        # For safety, only allow deletion of inactive/suspended employees
        emp = get_employee(employee_id)
        if not emp.get('success'):
            return jsonify({'status': 'error', 'message': 'Employee not found'}), 404
        
        employee_data = emp.get('data', {})
        if employee_data.get('account_status') == 'Active':
            return jsonify({
                'status': 'error',
                'message': 'Cannot delete active employees. Deactivate first.'
            }), 400
        
        # Delete employee
        result = delete_employee(employee_id)
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Employee deleted successfully'
            }), 200
        
        return jsonify({'status': 'error', 'message': result.get('error')}), 400
        
    except Exception as e:
        logger.exception(f'Delete employee error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  CHANGE ACCOUNT STATUS
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/admin/employees/<employee_id>/status', methods=['POST'])
@require_session_admin
def change_account_status(employee_id):
    """
    Change employee account status (Active/Inactive/Suspended).
    
    Request:
    ```json
    {
        "status": "Suspended",
        "reason": "Training period"
    }
    ```
    
    Response (200):
    ```json
    {
        "status": "success",
        "message": "Account status changed to Suspended"
    }
    ```
    """
    try:
        data = request.get_json(silent=True) or {}
        
        new_status = data.get('status')
        if not new_status or new_status not in ('Active', 'Inactive', 'Suspended'):
            return jsonify({
                'status': 'error',
                'message': 'Status must be Active, Inactive, or Suspended'
            }), 400
        
        result = update_employee(
            employee_row_id=employee_id,
            account_status=new_status
        )
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': f'Account status changed to {new_status}'
            }), 200
        
        return jsonify({'status': 'error', 'message': result.get('error')}), 400
        
    except Exception as e:
        logger.exception(f'Change status error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  CHANGE PASSWORD
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/admin/employees/<employee_id>/password', methods=['POST'])
@require_session_admin
def change_employee_password_admin(employee_id):
    """
    Change an employee's password (Admin only).
    
    Request:
    ```json
    {
        "newPassword": "NewSecurePass456!"
    }
    ```
    
    Response (200):
    ```json
    {
        "status": "success",
        "message": "Password changed successfully"
    }
    ```
    """
    try:
        data = request.get_json(silent=True) or {}
        
        new_password = data.get('newPassword') or data.get('new_password')
        if not new_password or len(new_password) < 6:
            return jsonify({
                'status': 'error',
                'message': 'Password must be at least 6 characters'
            }), 400
        
        result = change_employee_password(employee_id, new_password)
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Password changed successfully'
            }), 200
        
        error = result.get('error', 'Failed to change password')
        if 'not found' in error.lower():
            return jsonify({'status': 'error', 'message': 'Employee not found'}), 404
        
        return jsonify({'status': 'error', 'message': error}), 400
        
    except Exception as e:
        logger.exception(f'Change password error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  SUMMARY / HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/admin/employees/summary', methods=['GET'])
@require_session_admin
def get_employees_summary():
    """
    Get summary statistics about employees.
    
    Response (200):
    ```json
    {
        "status": "success",
        "data": {
            "total_employees": 45,
            "total_admins": 5,
            "total_staff": 40,
            "active": 42,
            "inactive": 2,
            "suspended": 1,
            "by_department": {
                "Operations": 20,
                "Customer Service": 15,
                "IT": 10
            }
        }
    }
    ```
    """
    try:
        # Get all employees
        result = list_all_employees()
        if not result.get('success'):
            return jsonify({'status': 'error', 'message': result.get('error')}), 500
        
        employees = result.get('data', [])
        
        # Calculate statistics
        summary = {
            'total_employees': len(employees),
            'total_admins': len([e for e in employees if e.get('role') == 'Admin']),
            'total_staff': len([e for e in employees if e.get('role') == 'Employee']),
            'active': len([e for e in employees if e.get('account_status') == 'Active']),
            'inactive': len([e for e in employees if e.get('account_status') == 'Inactive']),
            'suspended': len([e for e in employees if e.get('account_status') == 'Suspended']),
            'by_department': {}
        }
        
        # Count by department
        for emp in employees:
            dept = emp.get('department') or 'Unassigned'
            summary['by_department'][dept] = summary['by_department'].get(dept, 0) + 1
        
        return jsonify({
            'status': 'success',
            'data': summary
        }), 200
        
    except Exception as e:
        logger.exception(f'Get summary error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE SELF-SERVICE: PASSWORD RESET
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/employee/password/reset-request', methods=['POST'])
def request_password_reset():
    """
    Request password reset OTP for employee account.
    Sends OTP to employee's registered email.
    
    Request:
    ```json
    {
        "email": "employee@railway.com"
    }
    ```
    
    Response (200):
    ```json
    {
        "status": "success",
        "message": "Password reset OTP sent to your email"
    }
    ```
    """
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400
        
        # Check if employee exists
        employee = cloudscale_repo.get_employee_by_email(email)
        if not employee:
            # Don't reveal if email exists (security)
            return jsonify({
                'status': 'success',
                'message': 'If this email is registered, you will receive a password reset OTP'
            }), 200
        
        # Check if account is active
        if employee.get('Account_Status') != 'Active':
            return jsonify({
                'status': 'error',
                'message': 'Your account is not active. Please contact administrator.'
            }), 403
        
        # Generate and store OTP
        otp = generate_otp()
        otp_result = create_otp_record(email, otp, purpose='employee_password_reset')
        
        if not otp_result.get('success'):
            logger.error(f"Failed to create OTP: {otp_result.get('error')}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate reset code. Please try again.'
            }), 500
        
        # Send OTP email
        email_result = send_otp_email(email, otp, purpose='password_reset')
        
        if email_result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Password reset OTP sent to your email'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send reset email. Please try again.'
            }), 500
            
    except Exception as e:
        logger.exception(f'Password reset request error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_employees_bp.route('/employee/password/reset', methods=['POST'])
def reset_password_with_otp():
    """
    Reset employee password using OTP.
    
    Request:
    ```json
    {
        "email": "employee@railway.com",
        "otp": "123456",
        "newPassword": "NewSecurePass123!"
    }
    ```
    
    Response (200):
    ```json
    {
        "status": "success",
        "message": "Password reset successfully. You can now login with your new password."
    }
    ```
    """
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        otp = (data.get('otp') or '').strip()
        new_password = data.get('newPassword') or data.get('new_password') or ''
        
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400
        if not otp:
            return jsonify({'status': 'error', 'message': 'OTP is required'}), 400
        if not new_password or len(new_password) < 6:
            return jsonify({
                'status': 'error',
                'message': 'Password must be at least 6 characters'
            }), 400
        
        # Check if employee exists
        employee = cloudscale_repo.get_employee_by_email(email)
        if not employee:
            return jsonify({'status': 'error', 'message': 'Invalid email or OTP'}), 400
        
        # Verify OTP
        otp_valid, otp_message = verify_otp(email, otp, purpose='employee_password_reset')
        
        if not otp_valid:
            return jsonify({'status': 'error', 'message': otp_message}), 400
        
        # Update password
        employee_id = str(employee.get('ROWID'))
        result = change_employee_password(employee_id, new_password)
        
        if result.get('success'):
            logger.info(f"Password reset successful for employee: {email}")
            return jsonify({
                'status': 'success',
                'message': 'Password reset successfully. You can now login with your new password.'
            }), 200
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to reset password. Please try again.'
        }), 500
        
    except Exception as e:
        logger.exception(f'Password reset error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_employees_bp.route('/employee/password/change', methods=['POST'])
@require_session_employee
def change_own_password():
    """
    Employee changes their own password (requires valid session).
    
    Request:
    ```json
    {
        "currentPassword": "OldPassword123!",
        "newPassword": "NewSecurePass456!"
    }
    ```
    
    Response (200):
    ```json
    {
        "status": "success",
        "message": "Password changed successfully"
    }
    ```
    """
    try:
        data = request.get_json(silent=True) or {}
        current_password = data.get('currentPassword') or data.get('current_password') or ''
        new_password = data.get('newPassword') or data.get('new_password') or ''
        
        if not current_password:
            return jsonify({'status': 'error', 'message': 'Current password is required'}), 400
        if not new_password or len(new_password) < 6:
            return jsonify({
                'status': 'error',
                'message': 'New password must be at least 6 characters'
            }), 400
        
        # Get current employee
        employee_id = get_current_user_id()
        if not employee_id:
            return jsonify({'status': 'error', 'message': 'Invalid session'}), 401
        
        # Get employee record to verify current password
        emp_result = get_employee(employee_id)
        if not emp_result.get('success'):
            return jsonify({'status': 'error', 'message': 'Employee not found'}), 404
        
        employee = cloudscale_repo.get_employee_by_id(employee_id)
        if not employee:
            return jsonify({'status': 'error', 'message': 'Employee not found'}), 404

        # Verify current password against Users table
        user = cloudscale_repo.get_user_by_email(employee.get('Email', ''))
        if not user:
            return jsonify({'status': 'error', 'message': 'User account not found'}), 404

        from core.security import verify_password
        password_valid = verify_password(current_password, user.get('Password', ''))
        
        if not password_valid:
            return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 400
        
        # Update to new password
        result = change_employee_password(employee_id, new_password)
        
        if result.get('success'):
            logger.info(f"Password changed by employee: {employee_id}")
            return jsonify({
                'status': 'success',
                'message': 'Password changed successfully'
            }), 200
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to change password'
        }), 500
        
    except Exception as e:
        logger.exception(f'Change password error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN: RESEND WELCOME EMAIL
# ══════════════════════════════════════════════════════════════════════════════

@admin_employees_bp.route('/admin/employees/<employee_id>/resend-welcome', methods=['POST'])
@require_session_admin
def resend_welcome_email(employee_id):
    """
    Resend welcome email with a new temporary password.
    
    Response (200):
    ```json
    {
        "status": "success",
        "message": "Welcome email resent with new temporary password"
    }
    ```
    """
    try:
        # Get employee
        emp_result = get_employee(employee_id)
        if not emp_result.get('success'):
            return jsonify({'status': 'error', 'message': 'Employee not found'}), 404
        
        employee_data = emp_result.get('data', {})
        email = employee_data.get('email')
        full_name = employee_data.get('full_name')
        role = employee_data.get('role')
        
        # Generate new temporary password
        new_password = generate_temp_password(12)
        
        # Update employee password
        result = change_employee_password(employee_id, new_password)
        if not result.get('success'):
            return jsonify({
                'status': 'error',
                'message': 'Failed to reset password'
            }), 500
        
        # Send welcome email with new credentials
        email_result = send_welcome_email(email, full_name, new_password, role)
        
        if email_result.get('success'):
            return jsonify({
                'status': 'success',
                'message': 'Welcome email resent with new temporary password'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Password reset but failed to send email'
            }), 500
            
    except Exception as e:
        logger.exception(f'Resend welcome email error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
