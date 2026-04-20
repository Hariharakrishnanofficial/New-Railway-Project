"""
Employee Service - Smart Railway Ticketing System

Handles employee (staff) operations:
- Employee CRUD operations
- Employee ID generation
- Permission management
- Employee authentication
- Employee profile management

Employees are separate from Users (passengers). Employees have:
- Employee_ID (e.g., EMP001, ADM001)
- Role (Admin/Employee)
- Department & Designation
- Permissions (JSON)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any

from config import TABLES
from repositories.cloudscale_repository import cloudscale_repo
from core.security import hash_password, verify_password

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  DEFAULT PERMISSIONS
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_ADMIN_PERMISSIONS = {
    "modules": {
        "dashboard": ["view"],
        "bookings": ["view", "create", "edit", "cancel", "refund"],
        "trains": ["view", "create", "edit", "delete"],
        "stations": ["view", "create", "edit", "delete"],
        "routes": ["view", "create", "edit", "delete"],
        "users": ["view", "create", "edit", "deactivate"],
        "employees": ["view", "create", "edit", "deactivate", "invite"],
        "reports": ["view", "export"],
        "announcements": ["view", "create", "edit", "delete"],
        "settings": ["view", "edit"],
        "audit_logs": ["view"],
    },
    "admin_access": True,
    "can_invite_employees": True,
}

DEFAULT_EMPLOYEE_PERMISSIONS = {
    "modules": {
        "dashboard": ["view"],
        "bookings": ["view", "create"],
        "trains": ["view"],
        "stations": ["view"],
        "routes": ["view"],
        "users": ["view"],
        "announcements": ["view"],
    },
    "admin_access": False,
    "can_invite_employees": False,
}


# ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE CRUD OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def _normalize_employee_role(role: str) -> str:
    role_value = (role or '').strip().lower()
    if role_value == 'admin' or role_value == 'administrator':
        return 'Admin'
    return 'Employee'


def _normalize_user_role(role: str) -> str:
    role_value = (role or '').strip().lower()
    if role_value == 'admin' or role_value == 'administrator':
        return 'ADMIN'
    if role_value == 'employee' or role_value == 'staff':
        return 'EMPLOYEE'
    return 'USER'

def create_employee(
    full_name: str,
    email: str,
    password: str,  # Plain text - will be hashed
    role: str,
    invited_by: str,  # Employee ROWID of inviting admin
    invitation_id: str = None,
    user_id: str = None,
    department: str = None,
    designation: str = None,
    phone_number: str = None,
    permissions: Dict = None,
) -> Dict[str, Any]:
    """
    Create a new employee record.
    
    Args:
        full_name: Employee's full name
        email: Unique email address
        password: Plain text password (will be hashed)
        role: 'Admin' or 'Employee'
        invited_by: ROWID of the employee who invited them
        invitation_id: Optional link to invitation record
        department: Optional department name
        designation: Optional job title
        phone_number: Optional contact number
        permissions: Optional custom permissions (uses defaults if not provided)
    
    Returns:
        Result dict with success status and employee data
    """
    try:
        email_lower = email.lower().strip()
        
        # Check if employee already exists
        existing = cloudscale_repo.get_employee_by_email(email_lower)
        if existing:
            return {
                'success': False,
                'error': 'Employee with this email already exists'
            }
        
        # Also check Users table - employees can't have same email as a passenger
        existing_user = cloudscale_repo.get_user_by_email(email_lower)
        if existing_user:
            return {
                'success': False,
                'error': 'A user (passenger) with this email already exists'
            }
        
        normalized_role = _normalize_employee_role(role)

        # Generate Employee ID
        employee_id = cloudscale_repo.get_next_employee_id(normalized_role)

        # Hash password (stored for compatibility; auth uses Users table)
        password_hash = hash_password(password)

        # Set default permissions based on role
        if permissions is None:
            permissions = DEFAULT_ADMIN_PERMISSIONS if normalized_role == 'Admin' else DEFAULT_EMPLOYEE_PERMISSIONS
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Build a schema-resilient payload (Employees schema has varied across deployments).
        base_data = {
            'Employee_ID': employee_id,
            'Full_Name': full_name.strip(),
            'Email': email_lower,
            'Password': password_hash,
            'Role': normalized_role,
            'Account_Status': 'Active',
            'Joined_At': now,
        }

        # Optional fields (add only if provided)
        if phone_number is not None:
            base_data['Phone_Number'] = phone_number
        if department is not None:
            base_data['Department'] = department
        if designation is not None:
            base_data['Designation'] = designation

        # Some schemas include these fields; include when available.
        try:
            base_data['Invited_By'] = int(invited_by)
        except Exception:
            pass
        if invitation_id:
            try:
                base_data['Invitation_Id'] = int(invitation_id)
            except Exception:
                pass

        # Prefer explicit active flag if the column exists.
        base_data['Is_Active'] = True

        # Optional audit timestamps (some schemas use Created_At/Updated_At, others rely on CREATEDTIME/MODIFIEDTIME).
        base_data['Created_At'] = now
        base_data['Updated_At'] = now

        if user_id:
            # Some deployments use User_ID; keep both attempts via fallback.
            try:
                base_data['User_ID'] = int(user_id)
            except Exception:
                pass

        def _try_create(payload: dict) -> dict:
            return cloudscale_repo.create_employee(payload)

        result = _try_create(dict(base_data))
        if not result.get('success'):
            # Fallback 1: drop schema-variant columns that often cause "Invalid column" errors
            slim = dict(base_data)
            for k in (
                'Created_At', 'Updated_At',
                'Invitation_Id', 'Invited_By', 'User_ID',
                'Is_Active', 'Joined_At',
                'Phone_Number', 'Department', 'Designation',
            ):
                slim.pop(k, None)
            result = _try_create(slim)

        if not result.get('success'):
            # Fallback 2: minimal required fields only
            minimal = {
                'Employee_ID': employee_id,
                'Full_Name': full_name.strip(),
                'Email': email_lower,
                'Password': password_hash,
                'Role': normalized_role,
                'Account_Status': 'Active',
            }
            result = _try_create(minimal)
        
        if not result.get('success'):
            logger.error(f"Failed to create employee: {result.get('error')}")
            return {
                'success': False,
                'error': 'Failed to create employee record'
            }
        
        employee_row_id = result.get('data', {}).get('ROWID')
        logger.info(f"Employee created: {employee_id} ({email_lower}), ROWID={employee_row_id}")
        
        return {
            'success': True,
            'data': {
                'row_id': employee_row_id,
                'employee_id': employee_id,
                'email': email_lower,
                'full_name': full_name.strip(),
                'role': normalized_role,
                'department': department,
                'designation': designation,
            }
        }
        
    except Exception as e:
        logger.exception(f"Error creating employee: {e}")
        return {
            'success': False,
            'error': 'Failed to create employee'
        }


def get_employee(employee_row_id: str) -> Dict[str, Any]:
    """
    Get employee by ROWID.
    
    Returns:
        Result dict with employee data (excluding password)
    """
    try:
        employee = cloudscale_repo.get_employee_cached(employee_row_id)
        if not employee:
            return {
                'success': False,
                'error': 'Employee not found'
            }

        # Role-only RBAC: permissions are derived from role constants (not per-employee DB fields).
        normalized_role = _normalize_employee_role(employee.get('Role', 'Employee'))
        permissions = DEFAULT_ADMIN_PERMISSIONS if normalized_role == 'Admin' else DEFAULT_EMPLOYEE_PERMISSIONS
        
        return {
            'success': True,
            'data': {
                'row_id': employee.get('ROWID'),
                'employee_id': employee.get('Employee_ID'),
                'full_name': employee.get('Full_Name'),
                'email': employee.get('Email'),
                'phone_number': employee.get('Phone_Number'),
                'role': employee.get('Role'),
                'department': employee.get('Department'),
                'designation': employee.get('Designation'),
                'permissions': permissions,
                'account_status': employee.get('Account_Status'),
                'last_login': employee.get('Last_Login'),
                'joined_at': employee.get('Joined_At'),
                'created_at': employee.get('Created_At'),
            }
        }
        
    except Exception as e:
        logger.exception(f"Error getting employee: {e}")
        return {
            'success': False,
            'error': 'Failed to get employee'
        }


def update_employee(
    employee_row_id: str,
    full_name: str = None,
    phone_number: str = None,
    department: str = None,
    designation: str = None,
    permissions: Dict = None,
    account_status: str = None,
) -> Dict[str, Any]:
    """
    Update employee details.
    
    Note: Email, Role, and Employee_ID cannot be changed.
    """
    try:
        # Verify employee exists
        employee = cloudscale_repo.get_employee_by_id(employee_row_id)
        if not employee:
            return {
                'success': False,
                'error': 'Employee not found'
            }
        
        update_data = {}
        
        if full_name is not None:
            update_data['Full_Name'] = full_name.strip()
        if phone_number is not None:
            update_data['Phone_Number'] = phone_number
        if department is not None:
            update_data['Department'] = department
        if designation is not None:
            update_data['Designation'] = designation
        # Permissions handling - skip until Permissions column exists
        # if permissions is not None:
        #     update_data['Permissions'] = json.dumps(permissions)
        if account_status is not None:
            if account_status not in ('Active', 'Inactive', 'Suspended'):
                return {
                    'success': False,
                    'error': 'Invalid account status. Must be Active, Inactive, or Suspended'
                }
            update_data['Account_Status'] = account_status
        
        result = cloudscale_repo.update_employee(employee_row_id, update_data)
        
        if not result.get('success'):
            return {
                'success': False,
                'error': 'Failed to update employee'
            }
        
        logger.info(f"Employee updated: ROWID={employee_row_id}")
        return {
            'success': True,
            'message': 'Employee updated successfully'
        }
        
    except Exception as e:
        logger.exception(f"Error updating employee: {e}")
        return {
            'success': False,
            'error': 'Failed to update employee'
        }


def change_employee_password(employee_row_id: str, new_password: str) -> Dict[str, Any]:
    """Change employee password."""
    try:
        # Hash new password (shared with Users)
        password_hash = hash_password(new_password)

        employee = cloudscale_repo.get_employee_by_id(employee_row_id)
        if not employee:
            return {
                'success': False,
                'error': 'Employee not found'
            }

        user = cloudscale_repo.get_user_by_email(employee.get('Email', ''))
        
        update_data = {
            'Password': password_hash,
        }

        result = cloudscale_repo.update_employee(employee_row_id, update_data)
        if not result.get('success'):
            # Fallback: some schemas disallow updating unknown fields; keep minimal.
            result = cloudscale_repo.update_employee(employee_row_id, {'Password': password_hash})
        
        if not result.get('success'):
            return {
                'success': False,
                'error': 'Failed to update password'
            }

        if user:
            # Users table uses Catalyst auto MODIFIEDTIME; don't write Modified_Time (schema variant).
            cloudscale_repo.update_record(TABLES['users'], str(user.get('ROWID')), {
                'Password': password_hash,
            })
        
        logger.info(f"Password changed for employee ROWID={employee_row_id}")
        return {
            'success': True,
            'message': 'Password changed successfully'
        }
        
    except Exception as e:
        logger.exception(f"Error changing employee password: {e}")
        return {
            'success': False,
            'error': 'Failed to change password'
        }


def deactivate_employee(employee_row_id: str, reason: str = None) -> Dict[str, Any]:
    """Deactivate an employee account."""
    return update_employee(employee_row_id, account_status='Inactive')


def delete_employee(employee_row_id: str) -> Dict[str, Any]:
    """
    Delete an employee record.
    
    Args:
        employee_row_id: Employee ROWID to delete
    
    Returns:
        Result dict with success status
    """
    try:
        # Verify employee exists
        employee = cloudscale_repo.get_employee_by_id(employee_row_id)
        if not employee:
            return {
                'success': False,
                'error': 'Employee not found'
            }
        
        result = cloudscale_repo.delete_employee(employee_row_id)
        
        if not result.get('success'):
            return {
                'success': False,
                'error': 'Failed to delete employee'
            }
        
        logger.info(f"Employee deleted: ROWID={employee_row_id}")
        return {
            'success': True,
            'message': 'Employee deleted successfully'
        }
        
    except Exception as e:
        logger.exception(f"Error deleting employee: {e}")
        return {
            'success': False,
            'error': 'Failed to delete employee'
        }


def list_all_employees() -> Dict[str, Any]:
    """
    List all employees without filters.
    
    Returns:
        Result dict with employees list
    """
    try:
        employees = cloudscale_repo.get_all_employees()
        
        # Format employees for response (exclude password)
        formatted = []
        for emp in employees:
            normalized_role = _normalize_employee_role(emp.get('Role', 'Employee'))
            permissions = DEFAULT_ADMIN_PERMISSIONS if normalized_role == 'Admin' else DEFAULT_EMPLOYEE_PERMISSIONS
            
            formatted.append({
                'row_id': emp.get('ROWID'),
                'employee_id': emp.get('Employee_ID'),
                'full_name': emp.get('Full_Name'),
                'email': emp.get('Email'),
                'phone_number': emp.get('Phone_Number'),
                'role': emp.get('Role'),
                'department': emp.get('Department'),
                'designation': emp.get('Designation'),
                'permissions': permissions,
                'account_status': emp.get('Account_Status'),
                'last_login': emp.get('Last_Login'),
                'joined_at': emp.get('Joined_At'),
                'created_at': emp.get('Created_At'),
            })
        
        return {
            'success': True,
            'data': formatted
        }
        
    except Exception as e:
        logger.exception(f"Error listing all employees: {e}")
        return {
            'success': False,
            'error': 'Failed to list employees'
        }


def get_employees_by_role(role: str) -> Dict[str, Any]:
    """
    Get employees filtered by role.
    
    Args:
        role: 'Admin' or 'Employee'
    
    Returns:
        Result dict with employees list
    """
    try:
        if role not in ('Admin', 'Employee'):
            return {
                'success': False,
                'error': 'Invalid role. Must be Admin or Employee'
            }
        
        employees = cloudscale_repo.get_all_employees(role=role)
        
        # Format employees for response (exclude password)
        formatted = []
        for emp in employees:
            normalized_role = _normalize_employee_role(emp.get('Role', 'Employee'))
            permissions = DEFAULT_ADMIN_PERMISSIONS if normalized_role == 'Admin' else DEFAULT_EMPLOYEE_PERMISSIONS
            
            formatted.append({
                'row_id': emp.get('ROWID'),
                'employee_id': emp.get('Employee_ID'),
                'full_name': emp.get('Full_Name'),
                'email': emp.get('Email'),
                'phone_number': emp.get('Phone_Number'),
                'role': emp.get('Role'),
                'department': emp.get('Department'),
                'designation': emp.get('Designation'),
                'permissions': permissions,
                'account_status': emp.get('Account_Status'),
                'last_login': emp.get('Last_Login'),
                'joined_at': emp.get('Joined_At'),
                'created_at': emp.get('Created_At'),
            })
        
        return {
            'success': True,
            'data': formatted
        }
        
    except Exception as e:
        logger.exception(f"Error listing employees by role: {e}")
        return {
            'success': False,
            'error': 'Failed to list employees'
        }


def list_employees(
    role: str = None,
    department: str = None,
    status: str = 'Active',
    limit: int = 100
) -> Dict[str, Any]:
    """
    List employees with optional filters.
    
    Args:
        role: Filter by role ('Admin' or 'Employee')
        department: Filter by department
        status: Filter by account status (default: 'Active')
        limit: Maximum records to return
    
    Returns:
        Result dict with employees list
    """
    try:
        employees = cloudscale_repo.get_all_employees(
            role=role,
            department=department,
            status=status,
            limit=limit
        )
        
        # Format employees for response (exclude password)
        formatted = []
        for emp in employees:
            normalized_role = _normalize_employee_role(emp.get('Role', 'Employee'))
            permissions = DEFAULT_ADMIN_PERMISSIONS if normalized_role == 'Admin' else DEFAULT_EMPLOYEE_PERMISSIONS
            
            formatted.append({
                'row_id': emp.get('ROWID'),
                'employee_id': emp.get('Employee_ID'),
                'full_name': emp.get('Full_Name'),
                'email': emp.get('Email'),
                'phone_number': emp.get('Phone_Number'),
                'role': emp.get('Role'),
                'department': emp.get('Department'),
                'designation': emp.get('Designation'),
                'permissions': permissions,
                'account_status': emp.get('Account_Status'),
                'last_login': emp.get('Last_Login'),
                'joined_at': emp.get('Joined_At'),
            })
        
        return {
            'success': True,
            'data': {
                'employees': formatted,
                'total': len(formatted)
            }
        }
        
    except Exception as e:
        logger.exception(f"Error listing employees: {e}")
        return {
            'success': False,
            'error': 'Failed to list employees'
        }


# ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

def authenticate_employee(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticate employee by email and password using only the Employees table.
    """
    try:
        email_lower = email.lower().strip()
        logger.info(f"[AUTH] Authenticating employee: {email_lower}")

        # Step 1: Look directly into the Employees table
        employee = cloudscale_repo.get_employee_by_email(email_lower)
        
        logger.info(f"[AUTH] Employee lookup result: {employee is not None}")
        if employee:
            logger.info(f"[AUTH] Found employee: {employee.get('Email')}, has_password: {bool(employee.get('Password'))}")
        
        if not employee:
            logger.warning(f"[AUTH] Employee not found for email: {email_lower}")
            return {
                'success': False,
                'error_code': 'EMPLOYEE_NOT_FOUND',
                'error': 'No employee account found with this email address. Please contact your administrator.'
            }

        # Step 2: Check account status
        emp_status = employee.get('Account_Status', 'Active')
        logger.info(f"[AUTH] Account status: {emp_status}")
        if emp_status != 'Active':
            return {
                'success': False,
                'error_code': 'EMPLOYEE_ACCOUNT_INACTIVE',
                'error': f"Employee account is {emp_status}"
            }

        # Step 3: Verify password against Employees table
        stored_hash = employee.get('Password', '')
        logger.info(f"[AUTH] Password verification - hash_len: {len(stored_hash) if stored_hash else 0}")
        if not verify_password(password, stored_hash):
            logger.warning(f"[AUTH] Password verification failed for {email_lower}")
            return {
                'success': False,
                'error_code': 'INVALID_PASSWORD',
                'error': 'Invalid email or password'
            }

        # Step 4: Role-only permissions (do not depend on Employees schema)
        normalized_role = _normalize_employee_role(employee.get('Role', 'Employee'))
        permissions = DEFAULT_ADMIN_PERMISSIONS if normalized_role == 'Admin' else DEFAULT_EMPLOYEE_PERMISSIONS

        logger.info(f"Employee authenticated: {employee.get('Employee_ID')} ({email_lower})")
        
        return {
            'success': True,
            'data': {
                'row_id': employee.get('ROWID'),
                'employee_id': employee.get('Employee_ID'),
                'full_name': employee.get('Full_Name'),
                'email': employee.get('Email'),
                'role': _normalize_user_role(normalized_role),
                'department': employee.get('Department'),
                'designation': employee.get('Designation'),
                'permissions': permissions,
                'type': 'employee',
            }
        }
        
    except Exception as e:
        logger.exception(f"Error authenticating employee: {e}")
        return {
            'success': False,
            'error_code': 'AUTH_FAILED',
            'error': 'Authentication failed'
        }


# ══════════════════════════════════════════════════════════════════════════════
#  PERMISSION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def has_permission(employee_row_id: str, module: str, action: str) -> bool:
    """
    Check if employee has a specific permission.
    
    Args:
        employee_row_id: Employee ROWID
        module: Module name (e.g., 'bookings', 'trains')
        action: Action name (e.g., 'view', 'create', 'edit')
    
    Returns:
        True if employee has the permission
    """
    try:
        employee = cloudscale_repo.get_employee_cached(employee_row_id)
        if not employee:
            return False

        normalized_role = _normalize_employee_role(employee.get('Role', 'Employee'))
        if normalized_role == 'Admin':
            return True

        module_perms = (DEFAULT_EMPLOYEE_PERMISSIONS.get('modules') or {}).get(module, [])
        return action in module_perms
        
    except Exception:
        return False


def can_invite_employees(employee_row_id: str) -> bool:
    """Check if employee can invite other employees."""
    try:
        employee = cloudscale_repo.get_employee_cached(employee_row_id)
        if not employee:
            return False

        normalized_role = _normalize_employee_role(employee.get('Role', 'Employee'))
        if normalized_role == 'Admin':
            return True
        return bool(DEFAULT_EMPLOYEE_PERMISSIONS.get('can_invite_employees', False))
        
    except Exception:
        return False


def get_employee_permissions(employee_row_id: str) -> Dict:
    """Get employee permissions as dict."""
    try:
        employee = cloudscale_repo.get_employee_cached(employee_row_id)
        if not employee:
            return {}

        normalized_role = _normalize_employee_role(employee.get('Role', 'Employee'))
        return DEFAULT_ADMIN_PERMISSIONS if normalized_role == 'Admin' else DEFAULT_EMPLOYEE_PERMISSIONS
        
    except Exception:
        return {}


def update_employee_permissions(employee_row_id: str, permissions: Dict) -> Dict[str, Any]:
    """Update employee permissions."""
    return update_employee(employee_row_id, permissions=permissions)
