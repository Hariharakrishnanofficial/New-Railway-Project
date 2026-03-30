"""
Trains Routes - Train management CRUD operations.
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_auth, require_admin

logger = logging.getLogger(__name__)
trains_bp = Blueprint('trains', __name__)


@trains_bp.route('/trains', methods=['GET'])
def get_all_trains():
    """Get all trains with optional filtering."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        active_only = request.args.get('active', 'true').lower() == 'true'
        source = request.args.get('source', '')
        destination = request.args.get('destination', '')

        cb = CriteriaBuilder()
        if active_only:
            cb.eq('Is_Active', 'true')
        if source:
            cb.contains('From_Station', source.upper())
        if destination:
            cb.contains('To_Station', destination.upper())

        criteria = cb.build()

        result = cloudscale_repo.get_all_records(
            TABLES['trains'],
            criteria=criteria,
            limit=limit,
            offset=offset
        )

        if result.get('success'):
            return jsonify({'status': 'success', 'data': result.get('data', {}).get('data', [])}), 200

        return jsonify({'status': 'error', 'message': 'Failed to fetch trains'}), 500

    except Exception as e:
        logger.exception(f'Get trains error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trains_bp.route('/trains/<train_id>', methods=['GET'])
def get_train(train_id):
    """Get train by ID."""
    try:
        result = cloudscale_repo.get_record_by_id(TABLES['trains'], train_id)

        if result.get('success') and result.get('data'):
            return jsonify({'status': 'success', 'data': result['data']}), 200

        return jsonify({'status': 'error', 'message': 'Train not found'}), 404

    except Exception as e:
        logger.exception(f'Get train error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trains_bp.route('/trains', methods=['POST'])
@require_admin
def create_train():
    """Create a new train (admin only)."""
    data = request.get_json(silent=True) or {}

    train_number = (data.get('trainNumber') or data.get('Train_Number') or '').strip()
    train_name = (data.get('trainName') or data.get('Train_Name') or '').strip()

    if not train_number or not train_name:
        return jsonify({'status': 'error', 'message': 'Train number and name are required'}), 400

    try:
        train_data = {
            'Train_Number': train_number,
            'Train_Name': train_name,
            'Train_Type': data.get('trainType') or data.get('Train_Type') or 'Mail/Express',
            'From_Station': data.get('fromStation') or data.get('From_Station') or '',
            'To_Station': data.get('toStation') or data.get('To_Station') or '',
            'Departure_Time': data.get('departureTime') or data.get('Departure_Time') or '',
            'Arrival_Time': data.get('arrivalTime') or data.get('Arrival_Time') or '',
            'Duration': data.get('duration') or data.get('Duration') or '',
            'Days_Of_Operation': data.get('daysOfOperation') or data.get('Days_Of_Operation') or 'All Days',
            'Is_Active': 'true',
            'Total_Seats_SL': data.get('totalSeatsSL') or 0,
            'Total_Seats_3A': data.get('totalSeats3A') or 0,
            'Total_Seats_2A': data.get('totalSeats2A') or 0,
            'Total_Seats_1A': data.get('totalSeats1A') or 0,
            'Total_Seats_CC': data.get('totalSeatsCC') or 0,
        }

        result = cloudscale_repo.create_record(TABLES['trains'], train_data)

        if result.get('success'):
            cloudscale_repo.invalidate_train_cache()
            return jsonify({'status': 'success', 'data': result.get('data')}), 201

        return jsonify({'status': 'error', 'message': 'Failed to create train'}), 500

    except Exception as e:
        logger.exception(f'Create train error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trains_bp.route('/trains/<train_id>', methods=['PUT'])
@require_admin
def update_train(train_id):
    """Update train (admin only)."""
    data = request.get_json(silent=True) or {}

    try:
        update_data = {}
        field_mapping = {
            'trainNumber': 'Train_Number',
            'trainName': 'Train_Name',
            'trainType': 'Train_Type',
            'fromStation': 'From_Station',
            'toStation': 'To_Station',
            'departureTime': 'Departure_Time',
            'arrivalTime': 'Arrival_Time',
            'duration': 'Duration',
            'daysOfOperation': 'Days_Of_Operation',
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

        result = cloudscale_repo.update_record(TABLES['trains'], train_id, update_data)

        if result.get('success'):
            cloudscale_repo.invalidate_train_cache(train_id)
            return jsonify({'status': 'success', 'message': 'Train updated'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to update train'}), 500

    except Exception as e:
        logger.exception(f'Update train error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trains_bp.route('/trains/<train_id>', methods=['DELETE'])
@require_admin
def delete_train(train_id):
    """Delete train (admin only)."""
    try:
        result = cloudscale_repo.delete_record(TABLES['trains'], train_id)

        if result.get('success'):
            cloudscale_repo.invalidate_train_cache(train_id)
            return jsonify({'status': 'success', 'message': 'Train deleted'}), 200

        return jsonify({'status': 'error', 'message': 'Failed to delete train'}), 500

    except Exception as e:
        logger.exception(f'Delete train error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
