"""
Admin Logs route — fetches and displays admin actions.
"""
from flask import Blueprint, jsonify, request
from services.zoho_service import zoho
from config import get_form_config
from core.security import require_admin

admin_logs_bp = Blueprint('admin_logs', __name__, url_prefix='/api/admin-logs')

@admin_logs_bp.route('', methods=['GET'])
@require_admin
def get_admin_logs():
    forms = get_form_config()
    limit = request.args.get('limit', 200, type=int)
    
    # Basic filtering
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    record_id = request.args.get('record_id')

    criteria_parts = []
    if user_id:
        criteria_parts.append(f'(User_ID == "{user_id}")')
    if action:
        criteria_parts.append(f'(Action == "{action}")')
    if record_id:
        criteria_parts.append(f'(Affected_Record_ID == "{record_id}")')
    
    criteria = ' && '.join(criteria_parts) if criteria_parts else None

    result = zoho.get_all_records(forms['reports']['admin_logs'], criteria=criteria, limit=limit, order_by='Timestamp', sort_order='desc')
    
    if not result.get('success'):
        return jsonify({'success': False, 'error': result.get('error', 'Failed to fetch admin logs')}), 500
    
    records = result.get('data', {}).get('data', [])
    return jsonify({'success': True, 'data': records})
