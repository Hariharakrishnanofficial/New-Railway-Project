"""
Coach Layouts module for Railway Ticketing System.
Provides CRUD operations for Coach_Layouts Zoho forms.
"""

from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from config import get_form_config
from core.security import require_admin
import logging

coaches_bp = Blueprint('coaches', __name__, url_prefix='/api/coaches')
logger = logging.getLogger(__name__)

def _is_true(val):
    if val is None:             return True
    if isinstance(val, bool):   return val
    if isinstance(val, str):    return val.lower().strip() in ('true', '1', 'yes', 'active')
    if isinstance(val, (int, float)): return val != 0
    return bool(val)

@coaches_bp.route('', methods=['GET'])
def get_coaches():
    result = zoho.get_all_records(_get_reports()['coach_layouts'])
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to fetch coach layouts')}), 500
    records = result.get('data', {}).get('data', [])
    return jsonify({'success': True, 'data': records})

@coaches_bp.route('/<id>', methods=['GET'])
def get_coach(id):
    result = zoho.get_record_by_id(_get_reports()['coach_layouts'], id)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Coach layout not found')}), 404
    return jsonify({'success': True, 'data': result.get('data', {})})

@coaches_bp.route('', methods=['POST'])
@require_admin
def create_coach():
    data = request.json
    payload = {k: v for k, v in {
        'Coach_Number':      data.get('Coach_Number'),
        'Coach_Type':        data.get('Coach_Type'),
        'Train':             data.get('Train'),
        'Total_Seats':       int(data.get('Total_Seats') or 0) if 'Total_Seats' in data else None,
        'Seat_Layout':       data.get('Seat_Layout'),
        'Berths_Per_Bay':    int(data.get('Berths_Per_Bay') or 0) if 'Berths_Per_Bay' in data else None,
        'Side_Berths':       int(data.get('Side_Berths') or 0) if 'Side_Berths' in data else None,
        'RAC_Capacity':      int(data.get('RAC_Capacity') or 0) if 'RAC_Capacity' in data else None,
        'WL_Capacity':       int(data.get('WL_Capacity') or 0) if 'WL_Capacity' in data else None,
        'Position_In_Train': int(data.get('Position_In_Train') or 0) if 'Position_In_Train' in data else None,
        'Has_Pantry':        _is_true(data.get('Has_Pantry', False)) if 'Has_Pantry' in data else False,
        'Is_AC':             _is_true(data.get('Is_AC', False)) if 'Is_AC' in data else False,
        'Is_Active':         _is_true(data.get('Is_Active', True)),
        'Seat_Details':      data.get('Seat_Details')
    }.items() if v is not None}

    result = zoho.create_record(_get_forms()['coach_layouts'], payload)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to create coach layout')}), 400
    return jsonify({'success': True, 'data': result.get('data', {})}), 201

@coaches_bp.route('/<id>', methods=['PUT', 'PATCH'])
@require_admin
def update_coach(id):
    data = request.json
    payload = {k: v for k, v in {
        'Coach_Number':      data.get('Coach_Number'),
        'Coach_Type':        data.get('Coach_Type'),
        'Train':             data.get('Train'),
        'Total_Seats':       int(data.get('Total_Seats') or 0) if 'Total_Seats' in data else None,
        'Seat_Layout':       data.get('Seat_Layout'),
        'Berths_Per_Bay':    int(data.get('Berths_Per_Bay') or 0) if 'Berths_Per_Bay' in data else None,
        'Side_Berths':       int(data.get('Side_Berths') or 0) if 'Side_Berths' in data else None,
        'RAC_Capacity':      int(data.get('RAC_Capacity') or 0) if 'RAC_Capacity' in data else None,
        'WL_Capacity':       int(data.get('WL_Capacity') or 0) if 'WL_Capacity' in data else None,
        'Position_In_Train': int(data.get('Position_In_Train') or 0) if 'Position_In_Train' in data else None,
        'Has_Pantry':        _is_true(data.get('Has_Pantry')) if 'Has_Pantry' in data else None,
        'Is_AC':             _is_true(data.get('Is_AC')) if 'Is_AC' in data else None,
        'Is_Active':         _is_true(data.get('Is_Active')) if 'Is_Active' in data else None,
        'Seat_Details':      data.get('Seat_Details')
    }.items() if v is not None}

    result = zoho.update_record(_get_reports()['coach_layouts'], id, payload)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to update coach layout')}), 400
    return jsonify({'success': True, 'data': result.get('data', {})})

@coaches_bp.route('/<id>', methods=['DELETE'])
@require_admin
def delete_coach(id):
    result = zoho.delete_record(_get_reports()['coach_layouts'], id)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to delete coach layout')}), 400
    return jsonify({'success': True, 'message': 'Coach layout deleted'})
