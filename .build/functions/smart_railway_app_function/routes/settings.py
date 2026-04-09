"""
Settings Routes - System settings management.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_admin

logger = logging.getLogger(__name__)
settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings', methods=['GET'])
def get_all_settings():
    """Get all settings."""
    try:
        result = cloudscale_repo.get_all_records(TABLES['settings'], limit=100)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch settings'}), 500
    except Exception as e:
        logger.exception(f'Get settings error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@settings_bp.route('/settings/key/<key>', methods=['GET'])
def get_setting_by_key(key):
    """Get setting by key."""
    try:
        criteria = CriteriaBuilder().eq('Setting_Key', key).build()
        records = cloudscale_repo.get_records(TABLES['settings'], criteria=criteria, limit=1)
        if records:
            return jsonify({'status': 'success', 'data': records[0]}), 200
        return jsonify({'status': 'error', 'message': 'Setting not found'}), 404
    except Exception as e:
        logger.exception(f'Get setting by key error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@settings_bp.route('/settings/<setting_id>', methods=['GET'])
def get_setting(setting_id):
    """Get setting by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['settings'], setting_id)
        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        return jsonify({'status': 'error', 'message': 'Setting not found'}), 404
    except Exception as e:
        logger.exception(f'Get setting error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@settings_bp.route('/settings', methods=['POST'])
@require_admin
def create_setting():
    """Create setting (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        setting_data = {
            'Setting_Key': data.get('key') or data.get('Setting_Key') or '',
            'Setting_Value': data.get('value') or data.get('Setting_Value') or '',
            'Description': data.get('description') or data.get('Description') or '',
            'Category': data.get('category') or data.get('Category') or 'general',
        }
        result = cloudscale_repo.create_record(TABLES['settings'], setting_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create setting'}), 500
    except Exception as e:
        logger.exception(f'Create setting error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@settings_bp.route('/settings/<setting_id>', methods=['PUT'])
@require_admin
def update_setting(setting_id):
    """Update setting (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        field_mapping = {
            'key': 'Setting_Key',
            'value': 'Setting_Value',
            'description': 'Description',
            'category': 'Category',
        }
        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['settings'], setting_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Setting updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update setting'}), 500
    except Exception as e:
        logger.exception(f'Update setting error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@settings_bp.route('/settings/<setting_id>', methods=['DELETE'])
@require_admin
def delete_setting(setting_id):
    """Delete setting (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['settings'], setting_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Setting deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete setting'}), 500
    except Exception as e:
        logger.exception(f'Delete setting error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
