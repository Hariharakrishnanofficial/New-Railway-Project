"""
Announcements routes — CRUD for system-wide and train/station-specific notices.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from config import TABLES
from core.security import require_admin
from core.security import get_current_user_id
from utils.date_helpers import to_zoho_date_only

logger = logging.getLogger(__name__)

trains_bp = Blueprint('trains', __name__)

def _is_true(val):
    if val is None:             return True
    if isinstance(val, bool):   return val
    if isinstance(val, str):    return val.lower().strip() in ('true', '1', 'yes', 'active')
    if isinstance(val, (int, float)): return val != 0
    return bool(val)

announcements_bp = Blueprint('announcements', __name__)


@announcements_bp.route('/api/announcements', methods=['GET'])
def get_announcements():
    """GET /api/announcements — all announcements (admin); optionally filter by active."""
    limit = request.args.get('limit', 100, type=int)

    result = zoho.get_all_records(TABLES['announcements'], criteria=None, limit=limit)
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)

    records = result.get('data', {}).get('data', []) or []
    return jsonify({'success': True, 'data': {'data': records, 'count': len(records)}, 'status_code': 200}), 200


@announcements_bp.route('/api/announcements/active', methods=['GET'])
def get_active_announcements():
    """GET /api/announcements/active — only currently active announcements for passengers."""
    result = zoho.get_all_records(TABLES['announcements'], criteria=None, limit=200)
    if not result.get('success'):
        return jsonify(result), result.get('status_code', 500)

    records = result.get('data', {}).get('data', []) or []
    today = datetime.now().strftime('%Y-%m-%d')

    active = []
    for a in records:
        # is_active = str(a.get('Is_Active', 'true')).lower()
        # if is_active == 'false':
        #     continue

        start_date = a.get('Start_Date', '')
        end_date = a.get('End_Date', '')

        # Parse dates for comparison
        def parse_date(d):
            if not d:
                return None
            try:
                return datetime.strptime(str(d).split(' ')[0], '%d-%b-%Y').strftime('%Y-%m-%d')
            except Exception:
                try:
                    return str(d)[:10]
                except Exception:
                    return None

        start_ymd = parse_date(start_date)
        end_ymd = parse_date(end_date)

        if start_ymd and start_ymd > today:
            continue
        if end_ymd and end_ymd < today:
            continue

        active.append(a)

    return jsonify({'success': True, 'data': {'data': active, 'count': len(active)}, 'status_code': 200}), 200


@announcements_bp.route('/api/announcements/<ann_id>', methods=['GET'])
def get_announcement(ann_id):
    result = zoho.get_record_by_id(TABLES['announcements'], ann_id)
    return jsonify(result), result.get('status_code', 200)


@announcements_bp.route('/api/announcements', methods=['POST'])
@require_admin
def create_announcement():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    title = (data.get('Title') or '').strip()
    message = (data.get('Message') or '').strip()

    if not title or not message:
        return jsonify({'success': False, 'error': 'Title and Message are required'}), 400

    payload = {
        'Title':           title,
        'Message':         message,
        'Priority':        data.get('Priority', 'Normal'),
        'Is_Active':       _is_true(data.get('Is_Active', True)),
    }

    # Add Train_ID if provided (single ID, not array)
    if data.get('Train_ID'):
        payload['Train_ID'] = data['Train_ID']
    # Add Station_ID if provided (single ID, not array)
    if data.get('Station_ID'):
        payload['Station_ID'] = data['Station_ID']
    if data.get('Start_Date'):
        payload['Start_Date'] = to_zoho_date_only(data['Start_Date'])
    if data.get('End_Date'):
        payload['End_Date'] = to_zoho_date_only(data['End_Date'])

    # Add Created_By from authenticated user
    user_id = get_current_user_id()
    if user_id:
        payload['Created_By'] = user_id

    result = zoho.create_record(TABLES['announcements'], payload)
    return jsonify(result), result.get('status_code', 200)


@announcements_bp.route('/api/announcements/<ann_id>', methods=['PUT'])
@require_admin
def update_announcement(ann_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    payload = {}
    for field in ['Title', 'Message', 'Priority', 'Is_Active', 'Train_ID', 'Station_ID']:
        if field in data:
            if field == 'Is_Active':
                payload[field] = _is_true(data[field])
            else:
                payload[field] = data[field]

    if 'Start_Date' in data:
        payload['Start_Date'] = to_zoho_date_only(data['Start_Date'])
    if 'End_Date' in data:
        payload['End_Date'] = to_zoho_date_only(data['End_Date'])

    result = zoho.update_record(TABLES['announcements'], ann_id, payload)
    return jsonify(result), result.get('status_code', 200)


@announcements_bp.route('/api/announcements/<ann_id>', methods=['DELETE'])
@require_admin
def delete_announcement(ann_id):
    result = zoho.delete_record(TABLES['announcements'], ann_id)
    return jsonify(result), result.get('status_code', 200)
