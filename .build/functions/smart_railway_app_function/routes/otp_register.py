"""
OTP Registration Routes - Smart Railway Ticketing System

Two-step registration with email OTP verification:
  1. POST /session/register/initiate - Submit form, sends OTP email
  2. POST /session/register/verify   - Submit OTP, creates account + session

Flow:
  User fills form → Backend validates → Sends OTP → User enters OTP → Account created
"""

import logging
import json
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, make_response

from repositories.cloudscale_repository import cloudscale_repo
from config import TABLES
from core.security import hash_password, rate_limit
from core.session_middleware import require_session
from services.otp_service import (
    generate_otp,
    create_otp_record,
    verify_otp,
    send_otp_email,
    send_registration_otp,
    can_resend_otp,
)
from services.session_service import create_session

logger = logging.getLogger(__name__)
otp_register_bp = Blueprint('otp_register', __name__)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _extract_payload() -> dict:
    """Extract request payload from JSON/form/query."""
    data = request.get_json(silent=True)
    if isinstance(data, dict) and data:
        return data
    
    raw = request.get_data(as_text=True) or ''
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    
    return request.form.to_dict() or request.values.to_dict() or {}


def _get_client_ip() -> str:
    """Get client IP address."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or ''


def _get_user_agent() -> str:
    """Get User-Agent header."""
    return request.headers.get('User-Agent', '')[:500]


def _set_session_cookie(response, session_id: str) -> None:
    """Set HttpOnly session cookie."""
    from config import (
        SESSION_COOKIE_NAME,
        SESSION_COOKIE_SECURE,
        SESSION_COOKIE_SAMESITE,
        SESSION_COOKIE_HTTPONLY,
        SESSION_TIMEOUT_HOURS,
    )
    from datetime import timedelta
    
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_TIMEOUT_HOURS)
    
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        expires=expires,
        httponly=SESSION_COOKIE_HTTPONLY,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path='/'
    )


# In-memory store for pending registrations (for simplicity)
# In production, store in database or Redis
_pending_registrations = {}


def _store_pending_registration(email: str, data: dict) -> None:
    """Store registration data temporarily until OTP is verified."""
    _pending_registrations[email.lower()] = {
        'data': data,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def _get_pending_registration(email: str) -> dict:
    """Retrieve pending registration data."""
    return _pending_registrations.get(email.lower(), {}).get('data')


def _clear_pending_registration(email: str) -> None:
    """Clear pending registration after successful verification."""
    _pending_registrations.pop(email.lower(), None)


# ══════════════════════════════════════════════════════════════════════════════
#  DEBUG: Test OTP system
# ══════════════════════════════════════════════════════════════════════════════

@otp_register_bp.route('/session/register/debug', methods=['GET'])
def debug_registration():
    """Debug endpoint to check registration state."""
    email = request.args.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email parameter required'}), 400
    
    try:
        debug_info = {
            'email_config': {
                'from_email': FROM_EMAIL,
                'app_name': APP_NAME,
                'catalyst_available': CATALYST_AVAILABLE
            },
            'otp_settings': {
                'expiry_minutes': OTP_EXPIRY_MINUTES,
                'max_attempts': OTP_MAX_ATTEMPTS,
                'resend_cooldown': OTP_RESEND_COOLDOWN_SECONDS
            },
            'pending_registration': _get_pending_registration(email) is not None,
            'user_exists': cloudscale_repo.get_user_by_email(email) is not None
        }
        
        # Check recent OTP
        from config import TABLES
        query = f"""
            SELECT Created_At, Attempts, Expires_At
            FROM {TABLES.get('otp_tokens', 'OTP_Tokens')}
            WHERE User_Email = '{email.replace("'", "''")}'
            AND Purpose = 'registration'
            ORDER BY Created_At DESC
            LIMIT 1
        """
        
        result = cloudscale_repo.execute_query(query)
        if result.get('success') and result.get('data', {}).get('data'):
            otp_record = result['data']['data'][0]
            debug_info['latest_otp'] = {
                'created_at': otp_record.get('Created_At'),
                'attempts': otp_record.get('Attempts'),
                'expires_at': otp_record.get('Expires_At')
            }
        else:
            debug_info['latest_otp'] = None
        
        return jsonify({
            'status': 'success',
            'debug_info': debug_info
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Debug failed: {str(e)}'
        }), 500


@otp_register_bp.route('/session/register/test', methods=['GET'])
def test_otp_system():
    """Debug endpoint to test OTP system components."""
    results = {
        'database_connection': False,
        'otp_table_access': False,
        'email_service': False,
        'errors': []
    }
    
    try:
        # Test 1: Database connection via Users table
        test_user = cloudscale_repo.get_user_by_email('test@nonexistent.com')
        results['database_connection'] = True
        results['user_check'] = 'passed (no exception)'
    except Exception as e:
        results['errors'].append(f'Database connection: {str(e)}')
    
    try:
        # Test 2: OTP table access
        from config import TABLES
        query = f"SELECT ROWID FROM {TABLES.get('otp_tokens', 'OTP_Tokens')} LIMIT 1"
        result = cloudscale_repo.execute_query(query)
        results['otp_table_access'] = result.get('success', False)
        if not result.get('success'):
            results['errors'].append(f"OTP table query failed: {result.get('error')}")
    except Exception as e:
        results['errors'].append(f'OTP table access: {str(e)}')
    
    try:
        # Test 3: Check Catalyst SDK
        import zcatalyst_sdk
        results['catalyst_sdk'] = 'available'
    except ImportError:
        results['catalyst_sdk'] = 'not available (dev mode)'
    
    return jsonify({
        'status': 'success' if not results['errors'] else 'partial',
        'results': results
    }), 200


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1: INITIATE REGISTRATION (Send OTP)
# ══════════════════════════════════════════════════════════════════════════════

@otp_register_bp.route('/session/register/initiate', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=30, window_seconds=3600)  # Increased from 5 to 30 per hour
def initiate_registration():
    """
    Step 1: Validate registration data and send OTP email.
    
    Supports both regular registration and employee invitation registration.
    
    Request:
        POST /session/register/initiate
        {
            "fullName": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "phoneNumber": "+1234567890",  // optional
            "invitationToken": "abc123..."  // optional - for employee registration
        }
    
    Response:
        {
            "status": "success",
            "message": "Verification code sent to your email",
            "data": {
                "email": "john@example.com",
                "expiresInMinutes": 15,
                "isEmployee": true  // if invitation token used
            }
        }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = _extract_payload()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    # Extract and validate fields
    full_name = (data.get('fullName') or data.get('Full_Name') or '').strip()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    password = data.get('password') or data.get('Password') or ''
    phone_number = (data.get('phoneNumber') or data.get('Phone_Number') or '').strip()
    invitation_token = (data.get('invitationToken') or '').strip()
    
    # Check if this is an employee invitation registration
    is_employee_registration = False
    invitation_data = None
    
    if invitation_token:
        from services.employee_invitation_service import verify_invitation_token
        is_valid, invitation_data = verify_invitation_token(invitation_token)
        
        if not is_valid:
            return jsonify({
                'status': 'error', 
                'message': 'Invalid or expired invitation link'
            }), 400
        
        # Verify email matches invitation
        if invitation_data['Email'] != email:
            return jsonify({
                'status': 'error',
                'message': 'Email must match the invitation'
            }), 400
        
        is_employee_registration = True
    
    # Validation
    if not full_name:
        return jsonify({'status': 'error', 'message': 'Full name is required'}), 400
    if len(full_name) < 2:
        return jsonify({'status': 'error', 'message': 'Full name must be at least 2 characters'}), 400
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address'}), 400
    
    if not password:
        return jsonify({'status': 'error', 'message': 'Password is required'}), 400
    if len(password) < 8:
        return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400
    
    try:
        # Check if email already exists
        existing = cloudscale_repo.get_user_by_email(email)
        if existing:
            return jsonify({'status': 'error', 'message': 'Email already registered'}), 409
        
        # NOTE: Do NOT store pending registration data in-memory.
        # Catalyst functions can run on multiple instances / cold starts, so
        # in-memory state is not reliable. The client must send the registration
        # details again during OTP verification.
        #
        # (We still validate upfront and send the OTP here.)
        
        # Send OTP
        otp_result = send_registration_otp(email)
        
        if not otp_result.get('success'):
            error = otp_result.get('error', 'Failed to send verification code')
            cooldown = otp_result.get('cooldown')
            logger.error(f"OTP send failed for {email}: {error}")
            
            if cooldown:
                return jsonify({
                    'status': 'error',
                    'message': error,
                    'cooldown': cooldown
                }), 429
            
            return jsonify({'status': 'error', 'message': error}), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Verification code sent to your email',
            'data': {
                'email': email,
                'expiresInMinutes': otp_result.get('expiresInMinutes', 15),
                'isEmployee': is_employee_registration
            }
        }), 200
        
    except Exception as e:
        logger.exception(f"Registration initiation error for {email if 'email' in dir() else 'unknown'}: {e}")
        return jsonify({'status': 'error', 'message': f'Registration failed: {str(e)}'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2: VERIFY OTP AND CREATE ACCOUNT
# ══════════════════════════════════════════════════════════════════════════════

@otp_register_bp.route('/session/register/verify', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=30, window_seconds=3600)  # Increased from 10 to 30 per hour
def verify_registration():
    """
    Step 2: Verify OTP and create user account with session.
    
    Request:
        POST /session/register/verify
        {
            "email": "john@example.com",
            "otp": "123456"
        }
    
    Response:
        Set-Cookie: railway_sid=<session_id>; HttpOnly; Secure
        {
            "status": "success",
            "message": "Registration successful",
            "data": {
                "user": { ... },
                "csrfToken": "..."
            }
        }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = _extract_payload()
    logger.info(f"OTP verification request for email: {data.get('email', 'NOT_PROVIDED')}")
    logger.debug(f"Request data keys: {list(data.keys()) if data else 'NO_DATA'}")
    
    if not data:
        logger.warning("OTP verification failed: No data provided")
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    otp = (data.get('otp') or data.get('OTP') or '').strip()
    logger.debug(f"Extracted email: '{email}', OTP length: {len(otp) if otp else 0}")
    
    if not email:
        logger.warning("OTP verification failed: Email is required")
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    if not otp:
        logger.warning(f"OTP verification failed for {email}: Verification code is required")
        return jsonify({'status': 'error', 'message': 'Verification code is required'}), 400
    if len(otp) != 6 or not otp.isdigit():
        logger.warning(f"OTP verification failed for {email}: Invalid format - length={len(otp)}, isdigit={otp.isdigit()}")
        return jsonify({'status': 'error', 'message': 'Invalid verification code format'}), 400
    
    try:
        # Verify OTP
        logger.info(f"Verifying OTP for {email}")
        otp_valid, otp_message = verify_otp(email, otp, 'registration')
        
        if not otp_valid:
            logger.warning(f"OTP verification failed for {email}: {otp_message}")
            # Check if it's an expiry message
            if "expired" in otp_message.lower():
                return jsonify({
                    'status': 'error',
                    'error_code': 'OTP_EXPIRED',
                    'message': otp_message,
                    'action_required': 'request_new_otp'
                }), 400
            elif "no valid otp" in otp_message.lower():
                return jsonify({
                    'status': 'error', 
                    'error_code': 'NO_OTP_FOUND',
                    'message': otp_message,
                    'action_required': 'restart_registration'
                }), 400
            else:
                return jsonify({
                    'status': 'error',
                    'error_code': 'INVALID_OTP',
                    'message': otp_message
                }), 400
        
        # Get registration details.
        # Prefer request payload (stateless), fallback to in-memory pending data for
        # backwards compatibility in single-instance local dev.
        logger.debug(f"OTP verified, resolving registration payload for {email}")

        pending_data = {
            'fullName': (data.get('fullName') or data.get('Full_Name') or data.get('full_name') or '').strip(),
            'password': data.get('password') or data.get('Password') or '',
            'phoneNumber': (data.get('phoneNumber') or data.get('Phone_Number') or data.get('phone_number') or '').strip(),
            'invitationToken': (data.get('invitationToken') or data.get('invitation_token') or '').strip() or None,
        }

        if not pending_data.get('fullName') or not pending_data.get('password'):
            fallback = _get_pending_registration(email)
            if isinstance(fallback, dict):
                pending_data = {**fallback, **{k: v for k, v in pending_data.items() if v}}

        if not pending_data.get('fullName') or not pending_data.get('password'):
            logger.warning(f"Registration payload missing for {email}")
            return jsonify({
                'status': 'error',
                'error_code': 'SESSION_EXPIRED',
                'message': 'Missing registration details for verification. Please restart registration and try again.',
                'action_required': 'restart_registration'
            }), 400

        # Defensive validation (client should already validate, but don't trust it).
        if len(pending_data.get('fullName', '')) < 2:
            return jsonify({'status': 'error', 'message': 'Full name must be at least 2 characters'}), 400
        if len(pending_data.get('password', '')) < 8:
            return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400

        # Determine whether this is an employee registration.
        is_employee = bool(pending_data.get('invitationToken'))
        pending_data['isEmployee'] = is_employee
        
        # Check again if email exists (race condition protection)
        existing = cloudscale_repo.get_user_by_email(email)
        if existing:
            _clear_pending_registration(email)
            return jsonify({'status': 'error', 'message': 'Email already registered'}), 409
        
        # Determine role and type based on registration
        is_employee = pending_data.get('isEmployee', False)
        invitation_token = pending_data.get('invitationToken')
        invitation_data = None
        
        # Re-verify invitation if this is employee registration
        if is_employee and invitation_token:
            from services.employee_invitation_service import verify_invitation_token
            is_valid, invitation_data = verify_invitation_token(invitation_token)
            
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': 'Invitation link has expired or is invalid'
                }), 400

            # Verify email matches invitation
            if str(invitation_data.get('Email', '')).strip().lower() != email:
                return jsonify({
                    'status': 'error',
                    'message': 'Email must match the invitation'
                }), 400
        
        # Hash password
        hashed_password = hash_password(pending_data['password'])
        
        if is_employee:
            # Create user + employee profile
            from services.employee_service import create_employee
            
            role = invitation_data.get('Role', 'Employee') if invitation_data else 'Employee'
            department = invitation_data.get('Department') if invitation_data else None
            designation = invitation_data.get('Designation') if invitation_data else None
            invited_by = invitation_data.get('Invited_By') if invitation_data else None
            invitation_id = invitation_data.get('ROWID') if invitation_data else None

            user_role = 'ADMIN' if str(role).lower() == 'admin' else 'EMPLOYEE'
            user_type = 'employee'

            user_data = {
                'Full_Name': pending_data['fullName'],
                'Email': email,
                'Password': hashed_password,
                'Role': user_role,
                'Account_Status': 'Active',
            }

            if pending_data.get('phoneNumber'):
                user_data['Phone_Number'] = pending_data['phoneNumber']

            user_result = cloudscale_repo.create_record(TABLES['users'], user_data)
            if not user_result.get('success'):
                logger.error(f"User creation failed: {user_result.get('error')}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to create user account'
                }), 500

            user_id = user_result.get('data', {}).get('ROWID')

            employee_result = create_employee(
                full_name=pending_data['fullName'],
                email=email,
                password=pending_data['password'],
                role=role,
                invited_by=str(invited_by) if invited_by else '1',
                invitation_id=str(invitation_id) if invitation_id else None,
                user_id=str(user_id),
                department=department,
                designation=designation,
                phone_number=pending_data.get('phoneNumber'),
            )
            
            if not employee_result.get('success'):
                logger.error(f"Employee creation failed: {employee_result.get('error')}")
                if user_id:
                    cloudscale_repo.delete_record(TABLES['users'], str(user_id))
                return jsonify({
                    'status': 'error',
                    'message': employee_result.get('error', 'Failed to create employee account')
                }), 500

            employee_row_id = employee_result.get('data', {}).get('row_id')

            # Mark invitation as used
            if invitation_token and employee_row_id:
                from services.employee_invitation_service import mark_invitation_used
                mark_invitation_used(invitation_token, employee_row_id)

            # Use employee ROWID for employee sessions
            user_id = employee_row_id
        else:
            # Create passenger (user) record
            user_role = 'USER'
            user_type = 'user'
            
            user_data = {
                'Full_Name': pending_data['fullName'],
                'Email': email,
                'Password': hashed_password,
                'Role': user_role,
                'Account_Status': 'Active',
            }
            
            if pending_data.get('phoneNumber'):
                user_data['Phone_Number'] = pending_data['phoneNumber']
            
            result = cloudscale_repo.create_record(TABLES['users'], user_data)
            
            if not result.get('success'):
                logger.error(f"User creation failed: {result.get('error')}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to create account'
                }), 500
            
            user_id = result.get('data', {}).get('ROWID')
        
        # Clear pending registration
        _clear_pending_registration(email)
        
        # Create session with appropriate user_type
        try:
            session_id, csrf_token = create_session(
                user_id=user_id,
                user_email=email,
                user_role=user_role,  # 'User', 'Employee', or 'Admin'
                ip_address=_get_client_ip(),
                user_agent=_get_user_agent(),
                device_fingerprint=None,
                user_type=user_type  # 'user' for passengers, 'employee' for staff
            )
        except Exception as sess_err:
            logger.error(f"Session creation failed for {email}: {sess_err}")
            # User/Employee was created but session failed - still return success
            # Can login to get a session
            return jsonify({
                'status': 'success',
                'message': 'Registration successful! Please login.',
                'data': {
                    'user': {
                        'id': user_id,
                        'fullName': pending_data['fullName'],
                        'email': email,
                        'role': user_role,
                        'type': user_type,
                    },
                    'csrfToken': None,
                }
            }), 201
        
        user_response = {
            'id': user_id,
            'fullName': pending_data['fullName'],
            'email': email,
            'phoneNumber': pending_data.get('phoneNumber', ''),
            'role': user_role,  # User, Employee, or Admin
            'type': user_type,  # 'user' or 'employee'
            'accountStatus': 'Active',
            'emailVerified': True,
        }
        
        # Build response with session cookie
        welcome_message = (
            'Employee registration successful! Welcome to the team.' if is_employee 
            else 'Registration successful! Welcome aboard.'
        )
        
        response = make_response(jsonify({
            'status': 'success',
            'message': welcome_message,
            'data': {
                'user': user_response,
                'csrfToken': csrf_token,
            }
        }), 201)
        
        _set_session_cookie(response, session_id)
        
        logger.info(f"{'Employee' if is_employee else 'User'} registered successfully: {email}")
        return response
        
    except Exception as e:
        logger.exception(f"Registration verification error: {e}")
        return jsonify({'status': 'error', 'message': 'Registration failed due to a server error. Please try again.'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  RESEND OTP
# ══════════════════════════════════════════════════════════════════════════════

@otp_register_bp.route('/session/register/resend-otp', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=10, window_seconds=3600)  # Increased from 3 to 10 per hour
def resend_registration_otp():
    """
    Resend OTP for pending registration.
    
    Request:
        POST /session/register/resend-otp
        { "email": "john@example.com" }
    
    Response:
        { "status": "success", "message": "Verification code sent" }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    data = _extract_payload()
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    
    # In serverless deployments we don't rely on in-memory pending state.
    # Allow resend as long as the email is not already registered.
    existing = cloudscale_repo.get_user_by_email(email)
    if existing:
        return jsonify({'status': 'error', 'message': 'Email already registered'}), 409

    # Check cooldown
    can_send, remaining = can_resend_otp(email, 'registration')
    if not can_send:
        return jsonify({
            'status': 'error',
            'message': f'Please wait {remaining} seconds before requesting another code',
            'cooldown': remaining
        }), 429
    
    # Send new OTP (mark as resend)
    otp_result = send_registration_otp(email, is_resend=True)
    
    if not otp_result.get('success'):
        # Check if limit exceeded
        if otp_result.get('limit_exceeded'):
            return jsonify({
                'status': 'error',
                'message': otp_result.get('error'),
                'limit_exceeded': True
            }), 429
        
        return jsonify({
            'status': 'error',
            'message': otp_result.get('error', 'Failed to send verification code')
        }), 500
    
    return jsonify({
        'status': 'success',
        'message': 'New verification code sent to your email',
        'data': {
            'expiresInMinutes': otp_result.get('expiresInMinutes', 15),
            'remaining_resend_attempts': otp_result.get('remaining_resend_attempts', 2)
        }
    }), 200
