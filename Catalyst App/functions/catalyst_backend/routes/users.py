"""
Users routes — CRUD, user bookings, profile, account status management.
Updated: cache invalidation on write operations.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from services.zoho_service import zoho
from repositories.cloudscale_repository import zoho_repo, CriteriaBuilder
from config import TABLES
from core.security import require_admin, hash_password, get_current_user_id, get_current_user_role
from utils.log_helper import log_admin_action
import logging

logger   = logging.getLogger(__name__)
users_bp = Blueprint('users', __name__)


def _is_true(val):
    if isinstance(val, bool):  return val
    if isinstance(val, str):   return val.lower() in ('true', '1', 'yes', 'active')
    if isinstance(val, (int, float)): return val != 0
    return bool(val)


# ── CREATE ────────────────────────────────────────────────────────────────────
@users_bp.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    full_name = (data.get('Full_Name') or '').strip()
    email     = (data.get('Email') or '').strip()
    phone     = (data.get('Phone_Number') or '').strip()
    if not all([full_name, email, phone]):
        missing = [f for f, v in [('Full_Name', full_name), ('Email', email), ('Phone_Number', phone)] if not v]
        return jsonify({'success': False, 'error': f'Missing: {", ".join(missing)}'}), 400

    payload = {k: v for k, v in {
        'Full_Name':       full_name,
        'Email':           email,
        'Phone_Number':    phone,
        'Address':         data.get('Address', ''),
        'Address1':        data.get('Address1', ''),
        'Gender':          data.get('Gender', 'Male'),
        'Role':            data.get('Role', 'User'),
        'Date_of_Birth':   data.get('Date_of_Birth') or None,
        'ID_Proof_Type':   data.get('ID_Proof_Type') or None,
        'ID_Proof_Number': data.get('ID_Proof_Number') or None,
        'Account_Status':  data.get('Account_Status', 'Active'),
        'Aadhar_Verified': _is_true(data.get('Aadhar_Verified', False)),
        'Is_Aadhar_Verified': _is_true(data.get('Aadhar_Verified', False)),  # Sync both names
        'Registered_Date': datetime.now().strftime('%d-%b-%Y %H:%M:%S'),
        'Password':        hash_password(data['Password']) if data.get('Password') else None,
    }.items() if v is not None}

    result = zoho.create_record(TABLES['users'], payload)
    
    if result.get('success'):
        record_id = result.get('data', {}).get('ID')
        user_email = request.headers.get('X-User-Email', 'Unknown')
        # Don't log password
        logged_payload = {k: v for k, v in payload.items() if k != 'Password'}
        log_admin_action(user_email, 'CREATE_USER', {'record_id': record_id, 'details': logged_payload})

    return jsonify(result), result.get('status_code', 200)


# ── LIST ──────────────────────────────────────────────────────────────────────
@users_bp.route('/api/users', methods=['GET'])
@require_admin
def get_users():
    limit  = request.args.get('limit', 200, type=int)
    role   = request.args.get('role', '').strip()
    search = request.args.get('search', '').strip()

    cb = CriteriaBuilder()
    if role: cb.eq('Role', role)
    result = zoho.get_all_records(TABLES['users'], cb.build(), limit)

    if search and result.get('success'):
        records = result.get('data', {}).get('data', []) or []
        s = search.lower()
        filtered = [u for u in records
                    if s in (u.get('Full_Name') or '').lower()
                    or s in (u.get('Email') or '').lower()
                    or s in (u.get('Phone_Number') or '').lower()]
        result = {**result, 'data': {**result.get('data', {}), 'data': filtered}}

    return jsonify(result), result.get('status_code', 200)


# ── GET BY ID ─────────────────────────────────────────────────────────────────
@users_bp.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    # Get current user from JWT context (set by require_auth or legacy headers)
    from core.security import require_auth
    from flask import g
    
    # Manually check auth since we can't stack decorators easily
    from core.security import _extract_bearer, decode_token
    token = _extract_bearer(request)
    
    current_user_id = None
    current_role = None
    
    if token:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        current_user_id = payload.get('sub', '')
        current_role = payload.get('role', 'User')
    else:
        # Legacy header fallback
        current_user_id = request.headers.get('X-User-ID', '').strip()
        current_role = request.headers.get('X-User-Role', 'User').strip()
    
    # Check if user is admin or accessing their own profile
    if not current_user_id:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    from config import ADMIN_DOMAIN, ADMIN_EMAIL
    is_admin_email = (request.headers.get('X-User-Email', '').strip().lower() == ADMIN_EMAIL or 
                      request.headers.get('X-User-Email', '').strip().lower().endswith('@' + ADMIN_DOMAIN))
    is_admin = is_admin_email or current_role.lower() == 'admin'
    
    # Allow access if admin or accessing own profile
    if not (is_admin or str(current_user_id) == str(user_id)):
        return jsonify({'success': False, 'error': 'You can only access your own profile'}), 403
    
    result = zoho.get_record_by_id(TABLES['users'], user_id)
    return jsonify(result), result.get('status_code', 200)


# ── UPDATE ────────────────────────────────────────────────────────────────────
@users_bp.route('/api/users/<user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    payload = {k: v for k, v in {
        'Full_Name':       data.get('Full_Name'),
        'Email':           data.get('Email'),
        'Phone_Number':    data.get('Phone_Number'),
        'Address':         data.get('Address'),
        'Address1':        data.get('Address1'),
        'Gender':          data.get('Gender'),
        'Role':            data.get('Role'),
        'Date_of_Birth':   data.get('Date_of_Birth'),
        'ID_Proof_Type':   data.get('ID_Proof_Type'),
        'ID_Proof_Number': data.get('ID_Proof_Number'),
        'Account_Status':  data.get('Account_Status'),
        'Aadhar_Verified': _is_true(data.get('Aadhar_Verified')) if 'Aadhar_Verified' in data else None,
        'Is_Aadhar_Verified': _is_true(data.get('Aadhar_Verified')) if 'Aadhar_Verified' in data else None,
        'Password':        hash_password(data['Password']) if data.get('Password') else None,
    }.items() if v is not None}

    if not payload:
        return jsonify({'success': False, 'error': 'No valid fields to update'}), 400

    result = zoho.update_record(TABLES['users'], user_id, payload)

    if result.get('success'):
        zoho_repo.invalidate_user_cache(user_id)
        user_email = request.headers.get('X-User-Email', 'Unknown')
        logged_payload = {k: v for k, v in payload.items() if k != 'Password'}
        log_admin_action(user_email, 'UPDATE_USER', {'record_id': user_id, 'updated_data': logged_payload})

    return jsonify(result), result.get('status_code', 200)


@users_bp.route('/api/users/<user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    user_email = request.headers.get('X-User-Email', 'Unknown')
    log_admin_action(user_email, 'DELETE_USER', {'record_id': user_id})
    
    result = zoho.delete_record(TABLES['users'], user_id)
    if result.get('success'):
        zoho_repo.invalidate_user_cache(user_id)
    return jsonify(result), result.get('status_code', 200)


# ── USER BOOKINGS (optimized — criteria-based query) ─────────────────────────
@users_bp.route('/api/users/<user_id>/bookings', methods=['GET'])
def get_user_bookings(user_id):
    upcoming_only = request.args.get('upcoming', '').lower() == 'true'
    status_filter = request.args.get('status', '').strip()

    cb = CriteriaBuilder().id_eq('Users', user_id)
    if status_filter:
        cb.eq('Booking_Status', status_filter)
    criteria = cb.build()

    result = zoho.get_all_records(TABLES['bookings'], criteria=criteria, limit=200)
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)

    records = result.get('data', {}).get('data', []) or []

    if upcoming_only:
        today = datetime.now().strftime('%Y-%m-%d')
        def to_ymd(jd):
            if not jd: return ''
            try:
                if len(str(jd).split('-')[0]) == 4: return str(jd)[:10]
                return datetime.strptime(str(jd).split(' ')[0], '%d-%b-%Y').strftime('%Y-%m-%d')
            except Exception: return ''
        records = [b for b in records if to_ymd(b.get('Journey_Date', '')) >= today]

    return jsonify({'success': True, 'data': {'data': records, 'count': len(records)}}), 200


# ── PROFILE UPDATE (self-service) ─────────────────────────────────────────────
@users_bp.route('/api/users/<user_id>/profile', methods=['PUT'])
def update_profile(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    allowed = {'Full_Name', 'Phone_Number', 'Address', 'Date_of_Birth', 'ID_Proof_Type', 'ID_Proof_Number', 'Gender'}
    payload = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not payload:
        return jsonify({'success': False, 'error': 'No valid fields to update'}), 400

    result = zoho.update_record(TABLES['users'], user_id, payload)
    if result.get('success'):
        zoho_repo.invalidate_user_cache(user_id)
        return jsonify({'success': True, 'message': 'Profile updated'}), 200
    return jsonify(result), result.get('status_code', 500)


# ── ACCOUNT STATUS (admin) ────────────────────────────────────────────────────
@users_bp.route('/api/users/<user_id>/status', methods=['PUT'])
@require_admin
def update_account_status(user_id):
    data       = request.get_json() or {}
    new_status = data.get('Account_Status', '').strip()
    if new_status not in ('Active', 'Blocked', 'Suspended'):
        return jsonify({'success': False, 'error': 'Account_Status must be Active, Blocked, or Suspended'}), 400

    result = zoho.update_record(TABLES['users'], user_id, {'Account_Status': new_status})
    if result.get('success'):
        zoho_repo.invalidate_user_cache(user_id)
        return jsonify({'success': True, 'message': f'User account {new_status.lower()}'}), 200
    return jsonify(result), result.get('status_code', 500)


# ── TRAVEL HISTORY INSIGHTS ───────────────────────────────────────────────────
@users_bp.route('/api/users/<user_id>/insights', methods=['GET'])
def get_user_insights(user_id):
    """GET /api/users/{id}/insights — travel statistics for the passenger dashboard."""
    cb       = CriteriaBuilder().id_eq('Users', user_id).build()
    bookings = zoho_repo.get_records(TABLES['bookings'], criteria=cb, limit=100)

    total = len(bookings)
    confirmed  = sum(1 for b in bookings if (b.get('Booking_Status') or '').lower() == 'confirmed')
    cancelled  = sum(1 for b in bookings if (b.get('Booking_Status') or '').lower() == 'cancelled')
    total_spent = sum(float(b.get('Total_Fare') or 0) for b in bookings
                      if (b.get('Booking_Status') or '').lower() != 'cancelled')

    class_count = {}
    for b in bookings:
        cls = b.get('Class', 'Unknown')
        class_count[cls] = class_count.get(cls, 0) + 1

    preferred_class = max(class_count, key=class_count.get) if class_count else 'SL'

    return jsonify({'success': True, 'data': {
        'total_bookings':  total,
        'confirmed':       confirmed,
        'cancelled':       cancelled,
        'total_spent':     round(total_spent, 2),
        'preferred_class': preferred_class,
        'class_breakdown': class_count,
    }}), 200
