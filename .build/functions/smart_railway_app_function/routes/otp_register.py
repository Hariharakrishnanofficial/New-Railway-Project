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
    
    Request:
        POST /session/register/initiate
        {
            "fullName": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "phoneNumber": "+1234567890"  // optional
        }
    
    Response:
        {
            "status": "success",
            "message": "Verification code sent to your email",
            "data": {
                "email": "john@example.com",
                "expiresInMinutes": 15
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
        
        # Store registration data temporarily
        _store_pending_registration(email, {
            'fullName': full_name,
            'email': email,
            'password': password,  # Will be hashed when verified
            'phoneNumber': phone_number,
        })
        
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
                'expiresInMinutes': otp_result.get('expiresInMinutes', 15)
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
    
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    email = (data.get('email') or data.get('Email') or '').strip().lower()
    otp = (data.get('otp') or data.get('OTP') or '').strip()
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    if not otp:
        return jsonify({'status': 'error', 'message': 'Verification code is required'}), 400
    if len(otp) != 6 or not otp.isdigit():
        return jsonify({'status': 'error', 'message': 'Invalid verification code format'}), 400
    
    try:
        # Verify OTP
        otp_valid, otp_message = verify_otp(email, otp, 'registration')
        
        if not otp_valid:
            return jsonify({'status': 'error', 'message': otp_message}), 400
        
        # Get pending registration data
        pending_data = _get_pending_registration(email)
        
        if not pending_data:
            return jsonify({
                'status': 'error',
                'message': 'Registration session expired. Please start again.'
            }), 400
        
        # Check again if email exists (race condition protection)
        existing = cloudscale_repo.get_user_by_email(email)
        if existing:
            _clear_pending_registration(email)
            return jsonify({'status': 'error', 'message': 'Email already registered'}), 409
        
        # Create user with hashed password
        hashed_password = hash_password(pending_data['password'])
        
        # Only use fields that exist in Users table schema
        user_data = {
            'Full_Name': pending_data['fullName'],
            'Email': email,
            'Password': hashed_password,
            'Role': 'User',
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
        
        # Create session
        try:
            session_id, csrf_token = create_session(
                user_id=user_id,
                user_email=email,
                user_role='User',
                ip_address=_get_client_ip(),
                user_agent=_get_user_agent(),
                device_fingerprint=None
            )
        except Exception as sess_err:
            logger.error(f"Session creation failed for {email}: {sess_err}")
            # User was created but session failed - still return success
            # User can login to get a session
            return jsonify({
                'status': 'success',
                'message': 'Registration successful! Please login.',
                'data': {
                    'user': {
                        'id': user_id,
                        'fullName': pending_data['fullName'],
                        'email': email,
                        'role': 'User',
                    },
                    'csrfToken': None,
                }
            }), 201
        
        user_response = {
            'id': user_id,
            'fullName': pending_data['fullName'],
            'email': email,
            'phoneNumber': pending_data.get('phoneNumber', ''),
            'role': 'User',
            'accountStatus': 'Active',
            'emailVerified': True,
        }
        
        # Build response with session cookie
        response = make_response(jsonify({
            'status': 'success',
            'message': 'Registration successful! Welcome aboard.',
            'data': {
                'user': user_response,
                'csrfToken': csrf_token,
            }
        }), 201)
        
        _set_session_cookie(response, session_id)
        
        logger.info(f"User registered successfully: {email}")
        return response
        
    except Exception as e:
        logger.exception(f"Registration verification error: {e}")
        return jsonify({'status': 'error', 'message': f'Registration failed: {str(e)}'}), 500


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
    
    # Check if there's a pending registration
    pending = _get_pending_registration(email)
    if not pending:
        return jsonify({
            'status': 'error',
            'message': 'No pending registration found. Please start registration again.'
        }), 400
    
    # Check cooldown
    can_send, remaining = can_resend_otp(email, 'registration')
    if not can_send:
        return jsonify({
            'status': 'error',
            'message': f'Please wait {remaining} seconds before requesting another code',
            'cooldown': remaining
        }), 429
    
    # Send new OTP
    otp_result = send_registration_otp(email)
    
    if not otp_result.get('success'):
        return jsonify({
            'status': 'error',
            'message': otp_result.get('error', 'Failed to send verification code')
        }), 500
    
    return jsonify({
        'status': 'success',
        'message': 'New verification code sent to your email',
        'data': {
            'expiresInMinutes': otp_result.get('expiresInMinutes', 15)
        }
    }), 200
