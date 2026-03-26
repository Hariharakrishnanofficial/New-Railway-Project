"""
Auth routes — register, login, JWT refresh, change-password, forgot/reset password.
Uses UserService + core.security JWT system.
"""

import os
import random
import logging
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

from services.user_service import user_service
from repositories.cloudscale_repository import cloudscale_repo
from core.security import decode_token, generate_access_token, rate_limit
from core.exceptions import RailwayException

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


# ── Register ─────────────────────────────────────────────────────────────────
@auth_bp.route('/api/auth/register', methods=['POST'])
@rate_limit(max_calls=10, window_seconds=3600)
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    try:
        result = user_service.register(data)
        return jsonify({'success': True, **result}), 201
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f'register error: {e}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/api/auth/login', methods=['POST'])
@rate_limit(max_calls=10, window_seconds=900)
def login():
    data = request.get_json(silent=True) or {}
    email    = (data.get('Email')    or '').strip()
    password = (data.get('Password') or '').strip()
    
    logger.debug(f"Login attempt — Email: '{email}', Pwd Len: {len(password)}")
    try:
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and Password are required'}), 400

        result = user_service.login(email, password)
        return jsonify({'success': True, **result}), 200
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f'login error: {e}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ── Refresh token ─────────────────────────────────────────────────────────────
@auth_bp.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    data          = request.get_json(silent=True) or {}
    refresh_token = data.get('refresh_token', '').strip()
    if not refresh_token:
        return jsonify({'success': False, 'error': 'refresh_token is required'}), 400

    payload = decode_token(refresh_token)
    if not payload or payload.get('type') != 'refresh':
        return jsonify({'success': False, 'error': 'Invalid or expired refresh token'}), 401

    # Fetch user to get current role
    user = cloudscale_repo.get_user_cached(payload.get('sub', ''))
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    from services.user_service import resolve_role
    role  = resolve_role(user)
    token = generate_access_token(payload['sub'], payload['email'], role)
    return jsonify({'success': True, 'access_token': token, 'token_type': 'Bearer', 'expires_in': 3600}), 200


# ── Logout (token revocation stub) ───────────────────────────────────────────
@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    # In a full impl, add jti to a Redis blacklist.
    # For now, client simply discards the token.
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


# ── Change password ───────────────────────────────────────────────────────────
@auth_bp.route('/api/auth/change-password', methods=['POST'])
def change_password():
    data = request.get_json(silent=True) or {}
    try:
        user_service.change_password(
            data.get('user_id', '').strip(),
            data.get('old_password', '').strip(),
            data.get('new_password', '').strip()
        )
        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f'change_password error: {e}')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ── Forgot password ───────────────────────────────────────────────────────────
@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
@rate_limit(max_calls=5, window_seconds=900)
def forgot_password():
    data  = request.get_json(silent=True) or {}
    email = (data.get('Email') or '').strip()
    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400

    from config import get_form_config
    forms = get_form_config()

    records = cloudscale_repo.get_records(forms['reports']['users'],
                                criteria=f'(Email == "{email}")', limit=1)
    if not records:
        return jsonify({'success': False, 'error': 'No account found with this email'}), 404

    otp        = str(random.randint(100000, 999999))
    expires_at = (datetime.now() + timedelta(minutes=15)).strftime('%d-%b-%Y %H:%M:%S')

    cloudscale_repo.create_record(forms['forms']['reset_tokens'], {
        'User_Email': email, 'OTP': otp,
        'Expires_At': expires_at, 'Is_Used': 'false',
    })
    return jsonify({'success': True,
                    'message': 'OTP generated. In production this is emailed.',
                    'otp': otp}), 200


# ── Reset password ────────────────────────────────────────────────────────────
@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data         = request.get_json(silent=True) or {}
    email        = (data.get('email') or data.get('Email') or '').strip()
    otp          = (data.get('otp') or '').strip()
    new_password = (data.get('new_password') or '').strip()

    if not all([email, otp, new_password]):
        return jsonify({'success': False, 'error': 'email, otp, and new_password are required'}), 400
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400

    from config import get_form_config
    from core.security import hash_password
    forms = get_form_config()

    tokens = cloudscale_repo.get_records(forms['reports']['reset_tokens'],
                               criteria=f'(User_Email == "{email}") && (OTP == "{otp}")', limit=5)
    valid = None
    for t in tokens:
        if str(t.get('Is_Used', 'false')).lower() == 'true':
            continue
        try:
            exp = datetime.strptime(t.get('Expires_At', ''), '%d-%b-%Y %H:%M:%S')
            if datetime.now() > exp:
                continue
        except Exception:
            continue
        valid = t
        break

    if not valid:
        return jsonify({'success': False, 'error': 'Invalid or expired OTP'}), 400

    users = cloudscale_repo.get_records(forms['reports']['users'],
                              criteria=f'(Email == "{email}")', limit=1)
    if not users:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    cloudscale_repo.update_record(forms['reports']['users'], users[0]['ID'],
                       {'Password': hash_password(new_password)})
    cloudscale_repo.update_record(forms['reports']['reset_tokens'], valid['ID'], {'Is_Used': 'true'})
    return jsonify({'success': True, 'message': 'Password reset successfully'}), 200


# ── Admin setup ───────────────────────────────────────────────────────────────
@auth_bp.route('/api/auth/setup-admin', methods=['POST'])
def setup_admin():
    from core.security import is_admin_email
    from config import get_form_config, ADMIN_EMAIL, ADMIN_DOMAIN
    from core.security import hash_password

    setup_key = os.getenv('ADMIN_SETUP_KEY', '').strip()
    if not setup_key:
        return jsonify({'success': False, 'error': 'Admin setup not enabled on this server'}), 503

    data         = request.get_json() or {}
    provided_key = (data.get('setup_key') or '').strip()
    if provided_key != setup_key:
        return jsonify({'success': False, 'error': 'Invalid setup key'}), 403

    password     = (data.get('Password') or '').strip()
    if not password:
        return jsonify({'success': False, 'error': 'Password is required'}), 400

    forms        = get_form_config()
    target_email = (data.get('Email') or ADMIN_EMAIL).strip().lower()
    full_name    = (data.get('Full_Name') or 'Admin').strip()

    if not is_admin_email(target_email):
        return jsonify({'success': False, 'error': f'Only @{ADMIN_DOMAIN} emails allowed'}), 400

    existing = cloudscale_repo.get_records(forms['reports']['users'],
                                 criteria=f'(Email == "{target_email}")', limit=1)
    hashed   = hash_password(password)

    if existing:
        cloudscale_repo.update_record(forms['reports']['users'], existing[0]['ID'],
                           {'Password': hashed, 'Role': 'Admin', 'Full_Name': full_name})
        return jsonify({'success': True, 'message': f'Admin updated: {target_email}', 'action': 'updated'}), 200

    cloudscale_repo.create_record(forms['forms']['users'], {
        'Full_Name': full_name, 'Email': target_email,
        'Password': hashed, 'Role': 'Admin',
        'Phone_Number': data.get('Phone_Number', ''),
        'Account_Status': 'Active',
    })
    return jsonify({'success': True, 'message': f'Admin created: {target_email}', 'action': 'created'}), 201


# ── Test Token (verify auth status) ──────────────────────────────────────────
@auth_bp.route('/api/test/token', methods=['GET', 'OPTIONS'])
def test_token():
    """Test endpoint to verify authentication status and token validity."""
    from core.security import _extract_bearer, decode_token
    from config import ADMIN_DOMAIN, ADMIN_EMAIL

    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        return '', 200

    token = _extract_bearer(request)
    email = request.headers.get('X-User-Email', '').strip().lower()
    role = request.headers.get('X-User-Role', '').strip()
    user_id = request.headers.get('X-User-ID', '').strip()

    result = {
        'success': True,
        'auth_method': None,
        'jwt_valid': False,
        'jwt_payload': None,
        'legacy_headers': {
            'email': email or None,
            'role': role or None,
            'user_id': user_id or None,
        },
        'is_admin': False,
    }

    if token:
        payload = decode_token(token)
        if payload and payload.get('type') == 'access':
            result['auth_method'] = 'jwt'
            result['jwt_valid'] = True
            result['jwt_payload'] = {
                'sub': payload.get('sub'),
                'email': payload.get('email'),
                'role': payload.get('role'),
                'exp': payload.get('exp'),
            }
            email = payload.get('email', '').lower()
            role = payload.get('role', '')
        else:
            result['auth_method'] = 'jwt_invalid'
            result['jwt_valid'] = False
    elif email:
        result['auth_method'] = 'legacy_headers'
    else:
        result['auth_method'] = 'none'

    # Check admin status
    if email:
        is_admin_email = (email == ADMIN_EMAIL or email.endswith('@' + ADMIN_DOMAIN))
        result['is_admin'] = is_admin_email or role.lower() == 'admin'

    return jsonify(result), 200
