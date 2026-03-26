"""
Quotas module for Railway Ticketing System.
Provides CRUD operations for Quotas Zoho forms.
"""

from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from config import TABLES
from core.security import require_admin
from utils.log_helper import log_admin_action
import logging

quotas_bp = Blueprint('quotas', __name__, url_prefix='/api/quotas')
logger = logging.getLogger(__name__)

def _is_true(val):
    if val is None:             return False
    if isinstance(val, bool):   return val
    if isinstance(val, str):    return val.lower().strip() in ('true', '1', 'yes', 'checked')
    return bool(val)

@quotas_bp.route('', methods=['GET'])
def get_quotas():
    result = zoho.get_all_records(TABLES['quotas'])
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to fetch quotas')}), 500
    records = result.get('data', {}).get('data', [])
    return jsonify({'success': True, 'data': records})

@quotas_bp.route('/<id>', methods=['GET'])
def get_quota(id):
    result = zoho.get_record_by_id(TABLES['quotas'], id)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Quota not found')}), 404
    return jsonify({'success': True, 'data': result.get('data', {})})

@quotas_bp.route('', methods=['POST'])
@require_admin
def create_quota():
    data = request.json

    # Validate required fields for CloudScale schema
    required_fields = ['Train_ID', 'Class', 'Total_Seats']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({'success': False, 'error': f'Missing required fields: {", ".join(missing)}'}), 400

    # Build payload with CloudScale Quotas schema fields
    total_seats = int(data.get('Total_Seats'))
    payload = {k: v for k, v in {
        'Train_ID':         data.get('Train_ID'),
        'Class':            data.get('Class'),
        'Quota_Type':       data.get('Quota_Type'),
        'Quota_Code':       data.get('Quota_Code'),
        'Total_Seats':      total_seats,
        'Available_Seats':  int(data.get('Available_Seats', total_seats)),
        'Booking_Opens':    data.get('Booking_Opens'),  # Time string like "10:00"
        'Is_Active':        'true' if _is_true(data.get('Is_Active', True)) else 'false'
    }.items() if v is not None}

    result = zoho.create_record(TABLES['quotas'], payload)
    if result.get('success'):
        record_id = result.get('data', {}).get('ID')
        user_email = request.headers.get('X-User-Email', 'Unknown')
        log_admin_action(user_email, 'CREATE_QUOTA', {'record_id': record_id, 'details': payload})

    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to create quota')}), 400
    return jsonify({'success': True, 'data': result.get('data', {})}), 201

@quotas_bp.route('/<id>', methods=['PUT', 'PATCH'])
@require_admin
def update_quota(id):
    data = request.json

    # Build payload with CloudScale Quotas schema fields (all optional for update)
    payload = {}

    if 'Train_ID' in data:
        payload['Train_ID'] = data.get('Train_ID')
    if 'Class' in data:
        payload['Class'] = data.get('Class')
    if 'Quota_Type' in data:
        payload['Quota_Type'] = data.get('Quota_Type')
    if 'Quota_Code' in data:
        payload['Quota_Code'] = data.get('Quota_Code')
    if 'Total_Seats' in data:
        payload['Total_Seats'] = int(data.get('Total_Seats'))
    if 'Available_Seats' in data:
        payload['Available_Seats'] = int(data.get('Available_Seats'))
    if 'Booking_Opens' in data:
        payload['Booking_Opens'] = data.get('Booking_Opens')  # Time string like "10:00"
    if 'Is_Active' in data:
        payload['Is_Active'] = 'true' if _is_true(data.get('Is_Active')) else 'false'

    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}

    result = zoho.update_record(TABLES['quotas'], id, payload)
    if result.get('success'):
        user_email = request.headers.get('X-User-Email', 'Unknown')
        log_admin_action(user_email, 'UPDATE_QUOTA', {'record_id': id, 'updated_data': payload})

    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to update quota')}), 400
    return jsonify({'success': True, 'data': result.get('data', {})})

@quotas_bp.route('/<id>', methods=['DELETE'])
@require_admin
def delete_quota(id):
    user_email = request.headers.get('X-User-Email', 'Unknown')
    log_admin_action(user_email, 'DELETE_QUOTA', {'record_id': id})
    
    result = zoho.delete_record(TABLES['quotas'], id)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to delete quota')}), 400
    return jsonify({'success': True, 'message': 'Quota deleted'})
