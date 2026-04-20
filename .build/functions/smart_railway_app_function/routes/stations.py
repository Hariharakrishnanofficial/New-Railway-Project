"""
Stations Routes - Station management CRUD operations.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.permission_validator import require_permission

logger = logging.getLogger(__name__)
stations_bp = Blueprint('stations', __name__)


@stations_bp.route('/stations', methods=['GET'])
@require_permission('stations', 'view')
def get_all_stations():
    """Get all stations."""
    try:
        stations = cloudscale_repo.get_all_stations_cached()
        return jsonify({'status': 'success', 'data': stations}), 200
    except Exception as e:
        logger.exception(f'Get stations error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@stations_bp.route('/stations/<station_id>', methods=['GET'])
@require_permission('stations', 'view')
def get_station(station_id):
    """Get station by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['stations'], station_id)
        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        return jsonify({'status': 'error', 'message': 'Station not found'}), 404
    except Exception as e:
        logger.exception(f'Get station error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@stations_bp.route('/stations', methods=['POST'])
@require_permission('stations', 'create')
def create_station():
    """Create a new station (admin only)."""
    data = request.get_json(silent=True) or {}

    station_code = (data.get('stationCode') or data.get('Station_Code') or '').strip().upper()
    station_name = (data.get('stationName') or data.get('Station_Name') or '').strip()

    if not station_code or not station_name:
        return jsonify({'status': 'error', 'message': 'Station code and name are required'}), 400

    try:
        station_data = {
            'Station_Code': station_code,
            'Station_Name': station_name,
            'City': data.get('city') or data.get('City') or '',
            'State': data.get('state') or data.get('State') or '',
            'Zone': data.get('zone') or data.get('Zone') or '',
            'Platform_Count': data.get('platformCount') or data.get('Platform_Count') or 1,
            'Is_Active': 'true',
        }

        result = cloudscale_repo.create_record(TABLES['stations'], station_data)

        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data')}), 201

        return jsonify({'status': 'error', 'message': 'Failed to create station'}), 500

    except Exception as e:
        logger.exception(f'Create station error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@stations_bp.route('/stations/<station_id>', methods=['PUT'])
@require_permission('stations', 'edit')
def update_station(station_id):
    """Update station (admin only)."""
    data = request.get_json(silent=True) or {}

    try:
        update_data = {}
        field_mapping = {
            'stationCode': 'Station_Code',
            'stationName': 'Station_Name',
            'city': 'City',
            'state': 'State',
            'zone': 'Zone',
            'platformCount': 'Platform_Count',
            'isActive': 'Is_Active',
        }

        for client_key, db_key in field_mapping.items():
            if client_key in data:
                update_data[db_key] = data[client_key]

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        result = cloudscale_repo.update_record(TABLES['stations'], station_id, update_data)

        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Station updated'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to update station'}), 500

    except Exception as e:
        logger.exception(f'Update station error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@stations_bp.route('/stations/<station_id>', methods=['DELETE'])
@require_permission('stations', 'delete')
def delete_station(station_id):
    """Delete station (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['stations'], station_id)

        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'Station deleted'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to delete station'}), 500

    except Exception as e:
        logger.exception(f'Delete station error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
