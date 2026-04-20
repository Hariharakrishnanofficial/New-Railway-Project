"""
Admin Logs Routes - Audit log management.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.permission_validator import require_permission
from core.session_middleware import get_current_user_email

logger = logging.getLogger(__name__)
admin_logs_bp = Blueprint('admin_logs', __name__)


@admin_logs_bp.route('/admin/logs', methods=['GET'])
@require_permission('audit_logs', 'view')
def get_all_logs():
    """Get all admin logs (admin only)."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        action_type = request.args.get('actionType')
        user_email = request.args.get('userEmail')

        cb = CriteriaBuilder()
        if action_type:
            cb.eq('Action_Type', action_type)
        if user_email:
            cb.eq('User_Email', user_email)

        criteria = cb.build()

        result = cloudscale_repo.get_all_records(
            TABLES['admin_logs'],
            criteria=criteria,
            limit=limit,
            offset=offset,
            order_by='ROWID DESC'
        )

        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch logs'}), 500
    except Exception as e:
        logger.exception(f'Get logs error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_logs_bp.route('/admin/logs', methods=['POST'])
@require_permission('audit_logs', 'view')
def create_log():
    """Create admin log entry (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        log_data = {
            'User_Email': get_current_user_email() or data.get('userEmail') or '',
            'Action_Type': data.get('actionType') or data.get('Action_Type') or '',
            'Action_Details': data.get('actionDetails') or data.get('Action_Details') or '',
            'Entity_Type': data.get('entityType') or data.get('Entity_Type') or '',
            'Entity_ID': data.get('entityId') or data.get('Entity_ID') or '',
            'IP_Address': request.remote_addr or '',
            'Timestamp': datetime.utcnow().isoformat(),
        }
        result = cloudscale_repo.create_record(TABLES['admin_logs'], log_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create log'}), 500
    except Exception as e:
        logger.exception(f'Create log error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


def log_admin_action(action_type: str, action_details: str, entity_type: str = '', entity_id: str = ''):
    """Helper function to log admin actions."""
    try:
        log_data = {
            'User_Email': get_current_user_email() or 'system',
            'Action_Type': action_type,
            'Action_Details': action_details,
            'Entity_Type': entity_type,
            'Entity_ID': entity_id,
            'IP_Address': request.remote_addr if request else '',
            'Timestamp': datetime.utcnow().isoformat(),
        }
        cloudscale_repo.create_record(TABLES['admin_logs'], log_data)
    except Exception as e:
        logger.error(f'Failed to log admin action: {e}')
