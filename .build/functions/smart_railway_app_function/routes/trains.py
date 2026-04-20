"""
Trains Routes - Train management CRUD operations.

Enhanced with:
  - Train search by route
  - Seat availability per train
"""

import logging
from flask import Blueprint, jsonify, request

from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import require_auth
from core.permission_validator import require_permission
from services.seat_service import seat_service
from utils.date_helpers import to_zoho_date_only

logger = logging.getLogger(__name__)
trains_bp = Blueprint('trains', __name__)


# ══════════════════════════════════════════════════════════════════════════════
#  TRAIN SEARCH
# ══════════════════════════════════════════════════════════════════════════════

@trains_bp.route('/trains/search', methods=['GET'])
def search_trains():
    """
    Search trains between stations on a specific date.
    
    Query params:
    - from: Source station code or ID
    - to: Destination station code or ID
    - date: Journey date (YYYY-MM-DD)
    - class: Travel class filter (optional)
    """
    try:
        from_station = request.args.get('from', '').strip()
        to_station = request.args.get('to', '').strip()
        journey_date = request.args.get('date', '').strip()
        travel_class = request.args.get('class', '').strip()
        
        if not from_station or not to_station:
            return jsonify({
                'status': 'error',
                'message': 'Source (from) and destination (to) stations required'
            }), 400
        
        # Search trains
        trains = cloudscale_repo.search_trains_by_route(
            from_station=from_station,
            to_station=to_station,
            journey_date=journey_date,
            travel_class=travel_class if travel_class else None,
            active_only=True
        )
        
        # Enrich with availability if date provided
        if journey_date and trains:
            date_zoho = to_zoho_date_only(journey_date) or journey_date
            
            for train in trains:
                train_id = train.get('ROWID')
                availability = cloudscale_repo.get_seat_availability_by_train(
                    train_id=train_id,
                    journey_date=date_zoho,
                    travel_class=travel_class if travel_class else None
                )
                train['availability'] = availability
        
        return jsonify({
            'status': 'success',
            'data': {
                'trains': trains,
                'count': len(trains),
                'query': {
                    'from': from_station,
                    'to': to_station,
                    'date': journey_date,
                    'class': travel_class
                }
            }
        }), 200
    
    except Exception as e:
        logger.exception(f'Search trains error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@trains_bp.route('/trains/<train_id>/availability', methods=['GET'])
def get_train_availability(train_id):
    """
    Get seat availability for a train on a specific date.
    
    Query params:
    - date: Journey date (required)
    - class: Travel class (optional, returns all if not specified)
    """
    try:
        journey_date = request.args.get('date', '').strip()
        travel_class = request.args.get('class', '').strip()
        
        if not journey_date:
            return jsonify({
                'status': 'error',
                'message': 'Journey date required'
            }), 400
        
        date_zoho = to_zoho_date_only(journey_date) or journey_date
        
        if travel_class:
            result = seat_service.check_availability(train_id, date_zoho, travel_class)
        else:
            result = seat_service.check_availability_bulk(train_id, date_zoho)
        
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result['data']}), 200
        
        return jsonify({
            'status': 'error',
            'message': result.get('error', 'Failed to check availability')
        }), 400
    
    except Exception as e:
        logger.exception(f'Get availability error: {e}')
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  TRAIN CRUD
# ══════════════════════════════════════════════════════════════════════════════

@trains_bp.route('/trains', methods=['GET'])
@require_permission('trains', 'view')
def get_all_trains():
    """Get all trains with optional filtering."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        active_only = request.args.get('active', 'false').lower() == 'true'  # Changed default to false
        source = request.args.get('source', '')
        destination = request.args.get('destination', '')

        cb = CriteriaBuilder()
        # Only filter by Is_Active if explicitly requested (to avoid column error)
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
@require_permission('trains', 'view')
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
@require_permission('trains', 'create')
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
@require_permission('trains', 'edit')
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
@require_permission('trains', 'delete')
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
