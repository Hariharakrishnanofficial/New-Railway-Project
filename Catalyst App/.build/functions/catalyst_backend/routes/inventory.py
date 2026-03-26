"""
Train Inventory module for Railway Ticketing System.
Provides CRUD operations for Train_Inventory Zoho forms.
Includes summary and chart preparation endpoints.
"""

from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from config import get_form_config
from core.security import require_admin
from utils.date_helpers import to_zoho_date_only
from utils.log_helper import log_admin_action
import json
import logging

inventory_bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')
logger = logging.getLogger(__name__)


def _is_true(val):
    if val is None:             return False
    if isinstance(val, bool):   return val
    if isinstance(val, str):    return val.lower().strip() in ('true', '1', 'yes', 'checked')
    return bool(val)


@inventory_bp.route('', methods=['GET'])
@require_admin
def get_inventory():
    forms = get_form_config()
    train_id = request.args.get('train_id', '').strip()
    journey_date = request.args.get('date', '').strip()
    cls = request.args.get('class', '').strip()

    criteria_parts = []
    if train_id:
        criteria_parts.append(f'(Train == "{train_id}")')
    if journey_date:
        zoho_date = to_zoho_date_only(journey_date)
        criteria_parts.append(f'(Journey_Date == "{zoho_date}")')
    if cls:
        criteria_parts.append(f'(Class == "{cls}")')

    criteria = ' && '.join(criteria_parts) if criteria_parts else None

    result = zoho.get_all_records(forms['reports']['train_inventory'], criteria=criteria)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to fetch inventory')}), 500
    records = result.get('data', {}).get('data', [])
    return jsonify({'success': True, 'data': records})


@inventory_bp.route('/<id>', methods=['GET'])
@require_admin
def get_inventory_by_id(id):
    forms = get_form_config()
    result = zoho.get_record_by_id(forms['reports']['train_inventory'], id)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Inventory record not found')}), 404
    return jsonify({'success': True, 'data': result.get('data', {})})


@inventory_bp.route('', methods=['POST'])
@require_admin
def create_inventory():
    forms = get_form_config()
    data = request.json
    payload = {k: v for k, v in {
        'Train':               data.get('Train'),
        'Journey_Date':        data.get('Journey_Date'),
        'Class':               data.get('Class'),
        'Total_Capacity':      int(data.get('Total_Capacity') or 0),
        'Confirmed_Seats_JSON': data.get('Confirmed_Seats_JSON', '[]'),
        'RAC_Count':           int(data.get('RAC_Count') or 0),
        'Waitlist_Count':      int(data.get('Waitlist_Count') or 0),
        'Chart_Prepared':      _is_true(data.get('Chart_Prepared', False)),
        'Last_Updated':        data.get('Last_Updated')
    }.items() if v is not None}

    result = zoho.create_record(forms['forms']['train_inventory'], payload)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to create inventory')}), 400
    
    record_id = result.get('data', {}).get('ID')
    log_admin_action('create_inventory', record_id=record_id, details=payload)
    return jsonify({'success': True, 'data': result.get('data', {})}), 201


@inventory_bp.route('/<id>', methods=['PUT', 'PATCH'])
@require_admin
def update_inventory(id):
    forms = get_form_config()
    data = request.json
    payload = {k: v for k, v in {
        'Train':               data.get('Train'),
        'Journey_Date':        data.get('Journey_Date'),
        'Class':               data.get('Class'),
        'Total_Capacity':      int(data.get('Total_Capacity') or 0) if 'Total_Capacity' in data else None,
        'Confirmed_Seats_JSON': data.get('Confirmed_Seats_JSON'),
        'RAC_Count':           int(data.get('RAC_Count') or 0) if 'RAC_Count' in data else None,
        'Waitlist_Count':      int(data.get('Waitlist_Count') or 0) if 'Waitlist_Count' in data else None,
        'Chart_Prepared':      _is_true(data.get('Chart_Prepared')) if 'Chart_Prepared' in data else None,
        'Last_Updated':        data.get('Last_Updated')
    }.items() if v is not None}

    result = zoho.update_record(forms['reports']['train_inventory'], id, payload)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to update inventory')}), 400
    log_admin_action('update_inventory', record_id=id, details=payload)
    return jsonify({'success': True, 'data': result.get('data', {})})


@inventory_bp.route('/<id>', methods=['DELETE'])
@require_admin
def delete_inventory(id):
    forms = get_form_config()
    result = zoho.delete_record(forms['reports']['train_inventory'], id)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to delete inventory')}), 400
    log_admin_action('delete_inventory', record_id=id)
    return jsonify({'success': True, 'message': 'Inventory record deleted'})


@inventory_bp.route('/summary', methods=['GET'])
@require_admin
def inventory_summary():
    """
    GET /api/inventory/summary?train_id=X&date=YYYY-MM-DD
    Returns a summary of seat availability across all classes for a train+date.
    """
    forms = get_form_config()
    train_id = request.args.get('train_id', '').strip()
    journey_date = request.args.get('date', '').strip()

    if not train_id or not journey_date:
        return jsonify({'success': False, 'error': 'train_id and date are required'}), 400

    zoho_date = to_zoho_date_only(journey_date)
    criteria = f'(Train == "{train_id}" && Journey_Date == "{zoho_date}")'

    result = zoho.get_all_records(forms['reports']['train_inventory'], criteria=criteria)
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to fetch inventory for summary')}), 500

    records = result.get('data', {}).get('data', [])
    if not records:
        return jsonify({'success': True, 'data': {
            'train_id': train_id, 'journey_date': journey_date, 'total_capacity': 0,
            'total_confirmed': 0, 'total_rac': 0, 'total_wl': 0, 'total_available': 0,
            'by_class': {}
        }})

    summary = {
        'total_capacity': 0, 'total_confirmed': 0, 'total_rac': 0, 'total_wl': 0, 'by_class': {}
    }

    for record in records:
        cls = record.get('Class', 'Unknown')
        capacity = int(record.get('Total_Capacity', 0))
        rac_count = int(record.get('RAC_Count', 0))
        wl_count = int(record.get('Waitlist_Count', 0))
        
        try:
            confirmed_seats = json.loads(record.get('Confirmed_Seats_JSON', '[]'))
            confirmed_count = len(confirmed_seats)
        except (json.JSONDecodeError, TypeError):
            confirmed_count = 0

        available = max(0, capacity - confirmed_count)

        summary['total_capacity'] += capacity
        summary['total_confirmed'] += confirmed_count
        summary['total_rac'] += rac_count
        summary['total_wl'] += wl_count
        
        summary['by_class'][cls] = {
            'capacity': capacity,
            'confirmed': confirmed_count,
            'rac': rac_count,
            'wl': wl_count,
            'available': available
        }

    summary['total_available'] = max(0, summary['total_capacity'] - summary['total_confirmed'])
    summary['train_id'] = train_id
    summary['journey_date'] = journey_date

    return jsonify({'success': True, 'data': summary})


@inventory_bp.route('/prepare-chart', methods=['POST'])
@require_admin
def prepare_chart():
    """
    POST /api/inventory/prepare-chart
    Body: { "train_id": "...", "date": "YYYY-MM-DD", "class": "SL" (optional) }
    Marks Chart_Prepared = true for the inventory record(s).
    """
    forms = get_form_config()
    data = request.get_json() or {}
    train_id = data.get('train_id', '').strip()
    journey_date = data.get('date', '').strip()
    cls = data.get('class', '').strip()

    if not train_id or not journey_date:
        return jsonify({'success': False, 'error': 'train_id and date are required'}), 400

    zoho_date = to_zoho_date_only(journey_date)
    criteria_parts = [f'(Train == "{train_id}")', f'(Journey_Date == "{zoho_date}")']
    if cls:
        criteria_parts.append(f'(Class == "{cls}")')

    criteria = ' && '.join(criteria_parts)
    result = zoho.get_all_records(forms['reports']['train_inventory'], criteria=criteria, limit=20)

    if not result.get('success'):
        return jsonify({'success': False, 'error': 'Failed to fetch inventory records'}), 500

    records = result.get('data', {}).get('data', [])
    updated = 0
    for r in records:
        upd = zoho.update_record(forms['reports']['train_inventory'], r['ID'], {'Chart_Prepared': True})
        if upd.get('success'):
            updated += 1

    return jsonify({'success': True, 'message': f'Chart prepared for {updated} inventory record(s)', 'updated_count': updated})
