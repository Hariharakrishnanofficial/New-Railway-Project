"""
Employee Invitation Service

Handles employee invitation workflow:
1. Admin invites employee by email (with Role/Department/Designation)
2. Generate secure invitation token
3. Send invitation email with registration link
4. Track invitation status
5. On registration, create employee record (not user record)
"""

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from config import TABLES
from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from services.otp_service import send_otp_email, FROM_EMAIL, APP_NAME

logger = logging.getLogger(__name__)

# Configuration
INVITATION_EXPIRY_HOURS = int(os.getenv('INVITATION_EXPIRY_HOURS', '24'))  # 24 hours default


def generate_invitation_token() -> str:
    """Generate a secure invitation token (URL-safe)."""
    return secrets.token_urlsafe(32)  # 256 bits of entropy, URL-safe


def create_employee_invitation(
    admin_employee_id: str,  # ROWID of admin employee (not user!)
    employee_email: str,
    role: str = 'Employee',
    department: str = None,
    designation: str = None,
) -> Dict:
    """
    Create an employee invitation.
    
    Args:
        admin_employee_id: ROWID of the admin employee creating the invitation
        employee_email: Email address of the employee to invite
        role: Role to assign ('Admin' or 'Employee')
        department: Optional department for the new employee
        designation: Optional designation for the new employee
    
    Returns:
        Result dict with success status and data
    """
    try:
        # Normalize role
        normalized_role = 'Admin' if (role or '').strip().lower() == 'admin' else 'Employee'

        if normalized_role not in ('Admin', 'Employee'):
            return {
                'success': False,
                'error': 'Invalid role. Must be Admin or Employee'
            }
        
        # Check if employee already exists
        existing_employee = cloudscale_repo.get_employee_by_email(employee_email)
        if existing_employee:
            return {
                'success': False,
                'error': 'Employee with this email already exists'
            }
        
        # Also check Users table (can't have same email as passenger)
        existing_user = cloudscale_repo.get_user_by_email(employee_email)
        if existing_user:
            return {
                'success': False,
                'error': 'A user (passenger) with this email already exists'
            }
        
        # Check for existing unused invitation (optional - don't fail on this)
        try:
            # Use CriteriaBuilder for safe ZCQL query construction
            criteria = CriteriaBuilder() \
                .eq("Email", employee_email.lower().strip()) \
                .eq("Is_Used", "false") \
                .build()
            
            check_query = f"SELECT ROWID FROM {TABLES['employee_invitations']} WHERE {criteria}"
            logger.debug(f"Check query: {check_query}")
            
            existing_result = cloudscale_repo.execute_query(check_query)
            if existing_result.get('success') and existing_result.get('data', {}).get('data'):
                return {
                    'success': False,
                    'error': 'Active invitation already exists for this email'
                }
        except Exception as check_err:
            logger.warning(f"Could not check existing invitations (continuing): {check_err}")
        
        # Generate invitation token
        token = generate_invitation_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITATION_EXPIRY_HOURS)
        
        # Create invitation record with Role/Department/Designation
        # Note: Invited_By is a foreign key to Employees table (ROWID)
        invitation_data = {
            'Invitation_Token': token,
            'Email': employee_email.lower().strip(),
            'Role': normalized_role,
            'Department': department or '',
            'Designation': designation or '',
            'Invited_By': str(admin_employee_id),  # Foreign key as string
            'Invited_At': datetime.now(timezone.utc).isoformat(),
            'Expires_At': expires_at.isoformat(),
            'Is_Used': "false",  # Use string format for CloudScale boolean compatibility
        }
        
        logger.info(f"Creating invitation with data: {invitation_data}")
        
        result = cloudscale_repo.create_record(
            TABLES['employee_invitations'], 
            invitation_data
        )
        
        logger.info(f"Create invitation result: {result}")
        
        if not result.get('success'):
            logger.error(f"Failed to create invitation: {result.get('error')}")
            return {
                'success': False,
                'error': f"Failed to create invitation: {result.get('error', 'Unknown error')}"
            }
        
        invitation_id = result.get('data', {}).get('ROWID')
        
        # Send invitation email
        email_result = send_invitation_email(employee_email, token, role, department, designation)
        if not email_result.get('success'):
            logger.warning(f"Invitation created but email failed: {email_result.get('error')}")
            # Don't fail the whole operation - invitation exists
        
        logger.info(f"Employee invitation created: {employee_email} (role={normalized_role}) by admin employee {admin_employee_id}")
        
        return {
            'success': True,
            'data': {
                'invitation_id': invitation_id,
                'token': token,
                'email': employee_email,
                'role': normalized_role,
                'department': department,
                'designation': designation,
                'expires_at': expires_at.isoformat(),
                'registration_link': f"{get_base_url()}/app/index.html#/employee-register?invitation={token}"
            }
        }
        
    except Exception as e:
        logger.exception(f"Error creating employee invitation: {e}")
        return {
            'success': False,
            'error': 'Failed to create invitation'
        }


def verify_invitation_token(token: str) -> Tuple[bool, Optional[Dict]]:
    """
    Verify an invitation token and return invitation details.
    
    Args:
        token: Invitation token to verify
    
    Returns:
        Tuple of (is_valid, invitation_data)
    """
    try:
        # Use CriteriaBuilder for safe ZCQL query construction
        criteria = CriteriaBuilder() \
            .eq("Invitation_Token", token) \
            .eq("Is_Used", "false") \
            .build()
        
        query = f"""
            SELECT ROWID, Invitation_Token, Email, Role, Department, Designation,
                   Invited_By, Invited_At, Expires_At, Is_Used, Used_At
            FROM {TABLES['employee_invitations']}
            WHERE {criteria}
            LIMIT 1
        """
        
        result = cloudscale_repo.execute_query(query)

        if not result.get('success'):
            logger.warning(f"Failed to verify invitation token: {result.get('error')}")
            return False, None
        
        rows = result.get('data', {}).get('data', [])
        if not rows:
            return False, None
        
        invitation = rows[0]
        
        # Check expiry in Python
        expires_at_str = invitation.get('Expires_At')
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if expires_at < datetime.now(timezone.utc):
                    logger.info(f"Invitation token expired: {token[:10]}...")
                    return False, None
            except:
                pass
        return True, invitation
        
    except Exception as e:
        logger.exception(f"Error verifying invitation token: {e}")
        return False, None


def mark_invitation_used(token: str, registered_employee_id: str) -> bool:
    """
    Mark an invitation as used after successful employee registration.
    
    Args:
        token: Invitation token
        registered_employee_id: ROWID of the newly registered employee
    
    Returns:
        True if successfully marked as used
    """
    try:
        # Update data with string format for boolean
        update_data = {
            'Is_Used': "true",  # Use string format for CloudScale boolean compatibility
            'Used_At': datetime.now(timezone.utc).isoformat()
        }
        
        # Find invitation by token using CriteriaBuilder
        criteria = CriteriaBuilder().eq("Invitation_Token", token).build()
        query = f"""
            SELECT ROWID FROM {TABLES['employee_invitations']}
            WHERE {criteria}
            LIMIT 1
        """
        
        result = cloudscale_repo.execute_query(query)
        if not result.get('success') or not result.get('data', {}).get('data'):
            return False
        
        invitation_id = result['data']['data'][0]['ROWID']
        
        # Update invitation
        update_result = cloudscale_repo.update_record(
            TABLES['employee_invitations'],
            str(invitation_id),
            update_data
        )
        
        return update_result.get('success', False)
        
    except Exception as e:
        logger.exception(f"Error marking invitation as used: {e}")
        return False


def send_invitation_email(
    email: str, 
    token: str, 
    role: str = 'Employee',
    department: str = None,
    designation: str = None
) -> Dict:
    """
    Send invitation email to employee.
    
    Args:
        email: Employee email address
        token: Invitation token
        role: Role being assigned
        department: Department name (optional)
        designation: Designation/title (optional)
    
    Returns:
        Result dict with success status
    """
    try:
        registration_link = f"{get_base_url()}/app/index.html#/employee-register?invitation={token}"
        
        subject = f'{APP_NAME} - Employee Invitation'
        content = build_invitation_email(token, registration_link, role, department, designation)
        
        # Use the existing OTP email infrastructure
        mail_obj = {
            'from_email': FROM_EMAIL,
            'to_email': [email],
            'subject': subject,
            'content': content,
            'html_mode': True,
        }
        
        # Initialize Catalyst SDK and send
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        mail_service = app.email()
        
        logger.info(f"Sending employee invitation to {email} (role={role})")
        response = mail_service.send_mail(mail_obj)
        logger.info(f"Invitation email sent to {email}, response: {response}")
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Failed to send invitation email: {str(e)}")
        return {'success': False, 'error': str(e)}


def build_invitation_email(
    token: str, 
    registration_link: str,
    role: str = 'Employee',
    department: str = None,
    designation: str = None
) -> str:
    """Build HTML email for employee invitation."""
    # Build role details section
    role_details = f"<li><strong>Role:</strong> {role}</li>"
    if department:
        role_details += f"\n                    <li><strong>Department:</strong> {department}</li>"
    if designation:
        role_details += f"\n                    <li><strong>Designation:</strong> {designation}</li>"
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background: #f5f7fa;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">
                {APP_NAME}
            </h1>
            <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0; font-size: 16px;">
                Employee Invitation
            </p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 30px;">
            <h2 style="color: #333; margin: 0 0 20px; font-size: 24px;">
                You've been invited to join our team! 🎉
            </h2>
            
            <p style="color: #555; font-size: 16px; margin: 0 0 20px;">
                You have been invited to create an employee account for <strong>{APP_NAME}</strong>. 
                Click the button below to complete your registration.
            </p>
            
            <!-- Role Details -->
            <div style="background: #e8f4f8; padding: 15px 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                <h4 style="color: #333; margin: 0 0 10px; font-size: 16px;">Your Position Details</h4>
                <ul style="color: #555; margin: 0; padding-left: 20px; list-style: none;">
                    {role_details}
                </ul>
            </div>
            
            <!-- CTA Button -->
            <div style="text-align: center; margin: 30px 0;">
                <a href="{registration_link}" 
                   style="display: inline-block; background: #667eea; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Create Employee Account
                </a>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0;">
                <h3 style="color: #333; margin: 0 0 10px; font-size: 18px;">What's next?</h3>
                <ul style="color: #666; margin: 0; padding-left: 20px;">
                    <li>Click the registration button above</li>
                    <li>Fill out your employee details</li>
                    <li>Verify your email with the OTP code</li>
                    <li>Start using {APP_NAME} with employee privileges</li>
                </ul>
            </div>
            
            <p style="color: #666; font-size: 14px; margin: 20px 0 0;">
                This invitation will expire in <strong>{INVITATION_EXPIRY_HOURS} hours</strong>. 
                If you have any questions, please contact your administrator.
            </p>
            
            <p style="color: #999; font-size: 12px; margin: 25px 0 0; padding-top: 20px; border-top: 1px solid #eee;">
                If the button doesn't work, copy and paste this link:<br>
                <a href="{registration_link}" style="color: #667eea; word-break: break-all;">{registration_link}</a>
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px; margin: 0;">
                © 2026 {APP_NAME}. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>"""


def get_base_url() -> str:
    """Get the base URL for the application."""
    # In production, this should be the actual domain
    return os.getenv('BASE_URL', 'https://smart-railway-app-60066581545.development.catalystserverless.in')


def list_employee_invitations(admin_employee_id: str = None, limit: int = 50) -> Dict:
    """
    List employee invitations.
    
    Args:
        admin_employee_id: If provided, filter by inviting admin (Employee ROWID)
        limit: Maximum number of invitations to return
    
    Returns:
        Result dict with invitations list
    """
    try:
        # ZCQL doesn't support table aliases or JOINs well - use simple query
        if admin_employee_id:
            # Use CriteriaBuilder for safe query construction
            criteria = CriteriaBuilder().eq("Invited_By", admin_employee_id).build()
            query = f"""
                SELECT ROWID, Email, Role, Department, Designation, Invited_By,
                       Invited_At, Expires_At, Is_Used, Used_At
                FROM {TABLES['employee_invitations']}
                WHERE {criteria}
                ORDER BY Invited_At DESC
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT ROWID, Email, Role, Department, Designation, Invited_By,
                       Invited_At, Expires_At, Is_Used, Used_At
                FROM {TABLES['employee_invitations']}
                ORDER BY Invited_At DESC
                LIMIT {limit}
            """

        result = cloudscale_repo.execute_query(query)
        if not result.get('success'):
            logger.warning(f"Failed to fetch invitations: {result.get('error')}")
            return {'success': False, 'error': 'Failed to fetch invitations'}

        invitations = result.get('data', {}).get('data', [])
        
        # Format invitations for response
        formatted_invitations = []
        for inv in invitations:
            formatted_invitations.append({
                'id': inv.get('ROWID'),
                'email': inv.get('Email'),
                'role': inv.get('Role'),
                'department': inv.get('Department'),
                'designation': inv.get('Designation'),
                'invited_at': inv.get('Invited_At'),
                'expires_at': inv.get('Expires_At'),
                'is_used': inv.get('Is_Used'),
                'used_at': inv.get('Used_At'),
                'invited_by': inv.get('Invited_By')
            })
        
        return {
            'success': True,
            'data': {
                'invitations': formatted_invitations,
                'total': len(formatted_invitations)
            }
        }
        
    except Exception as e:
        logger.exception(f"Error listing employee invitations: {e}")
        return {'success': False, 'error': 'Failed to list invitations'}


def _get_invitation_by_id(invitation_id: str, admin_employee_id: str = None) -> Optional[Dict]:
    try:
        if admin_employee_id:
            # Use CriteriaBuilder for safe query construction
            criteria = CriteriaBuilder() \
                .id_eq("ROWID", invitation_id) \
                .id_eq("Invited_By", admin_employee_id) \
                .build()
            
            query = f"""
                  SELECT ROWID, Invitation_Token, Email, Role, Department, Designation,
                      Invited_By, Invited_At, Expires_At, Is_Used, Used_At, Registered_Employee_Id
                FROM {TABLES['employee_invitations']}
                WHERE {criteria}
                LIMIT 1
            """
        else:
            # Use CriteriaBuilder for safe query construction
            criteria = CriteriaBuilder().id_eq("ROWID", invitation_id).build()
            
            query = f"""
                  SELECT ROWID, Invitation_Token, Email, Role, Department, Designation,
                      Invited_By, Invited_At, Expires_At, Is_Used, Used_At, Registered_Employee_Id
                FROM {TABLES['employee_invitations']}
                WHERE {criteria}
                LIMIT 1
            """
        result = cloudscale_repo.execute_query(query)
        if not result.get('success'):
            # Fallback query without Registered_Employee_Id column (for schema compatibility)
            criteria_fallback = CriteriaBuilder().id_eq("ROWID", invitation_id).build()
            fallback = f"""
                SELECT ROWID, Invitation_Token, Email, Role, Department, Designation,
                       Invited_By, Invited_At, Expires_At, Is_Used, Used_At
                FROM {TABLES['employee_invitations']}
                WHERE {criteria_fallback}
                LIMIT 1
            """
            result = cloudscale_repo.execute_query(fallback)
            if not result.get('success'):
                return None
        rows = result.get('data', {}).get('data', [])
        return rows[0] if rows else None
    except Exception:
        return None


def refresh_invitation(invitation_id: str, admin_employee_id: str) -> Dict:
    """
    Refresh an invitation expiry and resend the same token.
    """
    invitation = _get_invitation_by_id(invitation_id, admin_employee_id)
    if not invitation:
        return {'success': False, 'error': 'Invitation not found'}

    if invitation.get('Is_Used'):
        return {'success': False, 'error': 'Invitation already used'}

    expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITATION_EXPIRY_HOURS)
    update_data = {
        'Expires_At': expires_at.isoformat(),
        'Invited_At': datetime.now(timezone.utc).isoformat(),
    }

    update_result = cloudscale_repo.update_record(
        TABLES['employee_invitations'],
        str(invitation_id),
        update_data
    )

    if not update_result.get('success'):
        return {'success': False, 'error': 'Failed to refresh invitation'}

    email_result = send_invitation_email(
        invitation.get('Email'),
        invitation.get('Invitation_Token'),
        invitation.get('Role') or 'Employee',
        invitation.get('Department') or None,
        invitation.get('Designation') or None,
    )

    if not email_result.get('success'):
        logger.warning(f"Invitation refreshed but email failed: {email_result.get('error')}")

    return {
        'success': True,
        'data': {
            'invitation_id': invitation_id,
            'email': invitation.get('Email'),
            'role': invitation.get('Role'),
            'department': invitation.get('Department'),
            'designation': invitation.get('Designation'),
            'expires_at': expires_at.isoformat()
        }
    }


def reinvite_employee(invitation_id: str, admin_employee_id: str) -> Dict:
    """
    Reinvite by generating a new token and resetting expiry.
    """
    invitation = _get_invitation_by_id(invitation_id, admin_employee_id)
    if not invitation:
        return {'success': False, 'error': 'Invitation not found'}

    if invitation.get('Is_Used'):
        return {'success': False, 'error': 'Invitation already used'}

    token = generate_invitation_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITATION_EXPIRY_HOURS)
    update_data = {
        'Invitation_Token': token,
        'Expires_At': expires_at.isoformat(),
        'Invited_At': datetime.now(timezone.utc).isoformat(),
        'Is_Used': False,
    }

    update_result = cloudscale_repo.update_record(
        TABLES['employee_invitations'],
        str(invitation_id),
        update_data
    )

    if not update_result.get('success'):
        return {'success': False, 'error': 'Failed to reinvite employee'}

    email_result = send_invitation_email(
        invitation.get('Email'),
        token,
        invitation.get('Role') or 'Employee',
        invitation.get('Department') or None,
        invitation.get('Designation') or None,
    )

    if not email_result.get('success'):
        logger.warning(f"Reinvite updated but email failed: {email_result.get('error')}")

    return {
        'success': True,
        'data': {
            'invitation_id': invitation_id,
            'email': invitation.get('Email'),
            'role': invitation.get('Role'),
            'department': invitation.get('Department'),
            'designation': invitation.get('Designation'),
            'expires_at': expires_at.isoformat()
        }
    }