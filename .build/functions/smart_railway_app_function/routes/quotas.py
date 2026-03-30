"""
Quotas Routes - Quota management.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo
from config import TABLES, QUOTA_TYPES
from core.security import require_admin

logger = logging.getLogger(__name__)
quotas_bp = Blueprint('quotas', __name__)


@quotas_bp.route('/quotas', methods=['GET'])
def get_all_quotas():
    """Get all quotas."""
    try:
        result = cloudscale_repo.get_all_records(TABLES['quotas'], limit=200)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200
        return jsonify({'status': 'error', 'message': 'Failed to fetch quotas'}), 500
    except Exception as e:
        logger.exception(f'Get quotas error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@quotas_bp.route('/quotas/types', methods=['GET'])
def get_quota_types():
    """Get all quota types."""
    return jsonify({'status': 'success', 'data': QUOTA_TYPES}), 200


@quotas_bp.route('/quotas/<quota_id>', methods=['GET'])
def get_quota(quota_id):
    """Get quota by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['quotas'], quota_id)
        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        return jsonify({'status': 'error', 'message': 'Quota not found'}), 404
    except Exception as e:
        logger.exception(f'Get quota error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@quotas_bp.route('/quotas', methods=['POST'])
@require_admin
def create_quota():
    """Create quota (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        quota_data = {
            'Train_ID': data.get('trainId') or data.get('Train_ID'),
            'Quota_Type': data.get('quotaType') or data.get('Quota_Type') or 'GN',
            'Travel_Class': data.get('travelClass') or data.get('Travel_Class') or 'SL',
            'Seats_Allocated': data.get('seatsAllocated') or data.get('Seats_Allocated') or 0,
        }
        result = cloudscale_repo.create_record(TABLES['quotas'], quota_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201
        return jsonify({'status': 'error', 'message': 'Failed to create quota'}), 500
    except Exception as e:
        logger.exception(f'Create quota error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@quotas_bp.route('/quotas/<quota_id>', methods=['PUT'])
@require_admin
def update_quota(quota_id):
    """Update quota (admin only)."""
    data = request.get_json(silent=True) or {}
    try:
        update_data = {}
        field_mapping = {
            'quotaType': 'Quota_Type',
            'travelClass': 'Travel_Class',
            'seatsAllocated': 'Seats_Allocated',
        }
        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['quotas'], quota_id, update_data)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Quota updated'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to update quota'}), 500
    except Exception as e:
        logger.exception(f'Update quota error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@quotas_bp.route('/quotas/<quota_id>', methods=['DELETE'])
@require_admin
def delete_quota(quota_id):
    """Delete quota (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['quotas'], quota_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Quota deleted'}), 200
        return jsonify({'status': 'error', 'message': 'Failed to delete quota'}), 500
    except Exception as e:
        logger.exception(f'Delete quota error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
