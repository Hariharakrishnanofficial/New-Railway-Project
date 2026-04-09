"""
Announcements Routes - System announcements.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_admin

logger = logging.getLogger(__name__)
announcements_bp = Blueprint('announcements', __name__)


@announcements_bp.route('/announcements', methods=['GET'])
def get_all_announcements():
    """Get all announcements."""
    try:
        result = cloudscale_repo.get_all_records(TABLES['announcements'], limit=100, order_by='ROWID DESC')
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch announcements'}), 500
    except Exception as e:
        logger.exception(f'Get announcements error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements/active', methods=['GET'])
def get_active_announcements():
    """Get active announcements."""
    try:
        criteria = CriteriaBuilder().eq('Is_Active', 'true').build()
        result = cloudscale_repo.get_all_records(TABLES['announcements'], criteria=criteria, limit=50)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch announcements'}), 500
    except Exception as e:
        logger.exception(f'Get active announcements error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements/<announcement_id>', methods=['GET'])
def get_announcement(announcement_id):
    """Get announcement by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['announcements'], announcement_id)
        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        return jsonify({'status': 'error', 'message': 'Announcement not found'}), 404
    except Exception as e:
        logger.exception(f'Get announcement error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements', methods=['POST'])
@require_admin
def create_announcement():
    """Create announcement (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        announcement_data = {
            'Title': data.get('title') or data.get('Title') or '',
            'Message': data.get('message') or data.get('Message') or '',
            'Type': data.get('type') or data.get('Type') or 'info',
            'Priority': data.get('priority') or data.get('Priority') or 'normal',
            'Is_Active': 'true',
            'Created_At': datetime.utcnow().isoformat(),
        }
        result = cloudscale_repo.create_record(TABLES['announcements'], announcement_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create announcement'}), 500
    except Exception as e:
        logger.exception(f'Create announcement error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements/<announcement_id>', methods=['PUT'])
@require_admin
def update_announcement(announcement_id):
    """Update announcement (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        field_mapping = {
            'title': 'Title',
            'message': 'Message',
            'type': 'Type',
            'priority': 'Priority',
            'isActive': 'Is_Active',
        }
        for client_key, db_key in field_mapping.items():
            if client_key in data:
                value = data[client_key]
                if client_key == 'isActive':
                    value = 'true' if value else 'false'
                update_data[db_key] = value

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['announcements'], announcement_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Announcement updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update announcement'}), 500
    except Exception as e:
        logger.exception(f'Update announcement error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@announcements_bp.route('/announcements/<announcement_id>', methods=['DELETE'])
@require_admin
def delete_announcement(announcement_id):
    """Delete announcement (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['announcements'], announcement_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Announcement deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete announcement'}), 500
    except Exception as e:
        logger.exception(f'Delete announcement error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
